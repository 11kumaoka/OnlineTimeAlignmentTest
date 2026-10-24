"""Selected native in-plane rotation closure gates, not a general alignment framework."""
import json
import re
import copy
import xml.etree.ElementTree as ET
import math
import numpy as np
from geometry.transforms import rotation_exp,rotation_log,multiply,transpose
from geometry.placements import xml_number
from research_common import stage,execute,digest,require,done,write_json

INJECTED_RX_RAD=.0018


def labels(mode):
    return [700104] if mode=='l1_rx' else [700102,700104,700202]


def config_name(mode):
    return 'l1_global_rx' if mode=='l1_rx' else 'l1_y_rx_l2_y'


def rotate_component(component,increment):
    """Left-Global Exp(dx) about this sensor center, serialized in the proven Rx chart.

    The actual DD4hep constructor maps decreasing component XML y to increasing
    physical Global X. The restriction to this one-axis subgroup is intentional;
    this is not additive Euler correction for arbitrary coupled rotations.
    """
    if not math.isfinite(increment) or abs(increment)>.01:raise ValueError('Only bounded L1 Global Rx enabled')
    r=component.find('rotation')
    x,y,z=[xml_number(r.get(a,'0'),{'pi':math.pi}) for a in 'xyz']
    if abs(x+math.pi/2)>1e-12 or abs(z)>1e-12:raise ValueError('Selected Rx serialization requires the proven component chart')
    current=rotation_exp((-(y+math.pi/2),0.,0.))
    target=multiply(rotation_exp((increment,0.,0.)),current)
    vector=rotation_log(target)
    if abs(vector[1])+abs(vector[2])>1e-12:raise ValueError('Outside selected one-axis subgroup')
    r.set('y',f'{-math.pi/2-vector[0]:.17g}')


def pose_checks(before,after,shifts,rx):
    """Actual DD4hep and ACTS poses, not XML attribute assumptions."""
    for a,b in zip(before,after):
        layer=a['layer'];q=np.array(rotation_exp((rx.get(layer,0.),0.,0.)))
        assert a['volume_id']==b['volume_id'] and a['geometry_id']==b['geometry_id']
        assert np.allclose(b['center_mm'],np.array(a['center_mm'])+[0,shifts.get(layer,0.),0],atol=1e-9,rtol=0)
        assert np.allclose(b['acts_rotation'],q@a['acts_rotation'],atol=2e-12,rtol=0)
        assert np.allclose(b['dd4hep_rotation'],q@a['dd4hep_rotation'],atol=2e-12,rtol=0)
        # Every 100 mm square sensitive corner stays inside the existing module
        # projection (100.5 mm) and layer z envelope (102 mm), including shifts.
        if layer in (1,2):
            from validation.telescope_closure.closure import MODULE_TO_GLOBAL
            total=np.array(b['acts_rotation'])@np.array(MODULE_TO_GLOBAL).T
            half=50*(abs(total[1,1])+abs(total[1,2]))
            assert half+abs(b['center_mm'][1])<50.25
            assert 50*(abs(total[2,1])+abs(total[2,2]))<51.


def physical_derivatives(args,reconstruction="nominal"):
    """Frozen native reference against fresh real DD4hep/ACTS surface perturbations."""
    from validation.telescope_closure.closure import displaced_xml,environment
    p=stage(args.result,'physical_derivatives' if reconstruction=='nominal' else 'corrected_physical_derivatives')
    native=json.loads((args.result/reconstruction/'mille.json').read_text())
    geometry=args.result/('geometry/fixtures/nominal.xml' if reconstruction=='nominal' else 'correction/corrected.xml')
    base_path=args.result/('data/control/channels_truth.json' if reconstruction=='nominal' else 'correction/geometry_audit/geometry.json')
    base=json.loads(base_path.read_text())['sensors']
    maximum=0.;checks=0;errors={}
    for step in (1e-4,1e-5,1e-6):
        poses=[]
        for sign in (1,-1):
            q=stage(p,f'step_{step:g}_{sign:+d}')
            displaced_xml(geometry,q/'geometry.xml',{},rotations={1:sign*step})
            execute([args.build/'TelescopeChannels',q/'geometry.xml',0,q/'geometry.json'],q,env=environment(args.build))
            sensors=json.loads((q/'geometry.json').read_text())['sensors']
            pose_checks(base,sensors,{}, {1:sign*step})
            poses.append(sensors[1])
        error=0.
        for event in native['events']:
            point=np.array(event['reference_position_mm']);direction=np.array(event['reference_direction'])
            predictions=[]
            for sensor in poses:
                r=np.array(sensor['acts_rotation']);center=np.array(sensor['center_mm']);normal=r[:,2]
                intersection=point+direction*(normal@(center-point))/(normal@direction)
                predictions.append((r.T@(intersection-center))[:2])
            finite=(predictions[0]-predictions[1])/(2*step)
            equation=next(e for e in event['equations'] if e['layer']==1)
            error=max(error,float(np.max(np.abs(finite-np.array(equation['global'])[:,3]))));checks+=1
        assert error<2e-5,(step,error)
        errors[str(step)]=error;maximum=max(maximum,error)
    write_json(p/'report.json',{'passed':True,'checks':checks,'errors_mm_per_rad':errors,
      'maximum_error_mm_per_rad':maximum,'method':'frozen actual native reference, independently perturbed real DD4hep surfaces',
      'model_sha256':native['model_sha256'],'residual_convention':'measured-predicted = A*localDelta + G*physicalDelta'})
    done(p,passed=True)


def correct(args):
    from validation.telescope_closure.closure import displaced_xml,environment
    from alignment.pede import read_pede
    require(args.result,'solve');p=stage(args.result,'correction')
    values=read_pede(args.result/'solve/millepede.res')
    shifts={l:values[k] for l,k in [(1,700102),(2,700202)] if k in values}
    rotations={1:values[700104]}
    nominal=args.result/'geometry/fixtures/nominal.xml'
    displaced_xml(nominal,p/'corrected.xml',shifts,rotations=rotations)
    write_json(p/'provenance.json',{'parent_sha256':digest(nominal),'pede_sha256':digest(args.result/'solve/millepede.res'),
       'physical_global_y_mm':shifts,'physical_global_rx_rad':rotations,'pivot':'current sensitive center',
       'composition':'Rnew=Exp([dx,0,0]) Rcurrent','truth_used':False,'activated':False})
    q=stage(p,'geometry_audit');execute([args.build/'TelescopeChannels',p/'corrected.xml',0,q/'geometry.json'],q,env=environment(args.build))
    base=json.loads((args.result/'data/control/channels_truth.json').read_text())['sensors']
    pose_checks(base,json.loads((q/'geometry.json').read_text())['sensors'],shifts,rotations)
    done(p,physical_global_y_mm=shifts,physical_global_rx_rad=rotations)


def check(args):
    import ROOT
    from podio import reading
    from validation.telescope_closure.closure import channel_values,channel_digest
    from validation.telescope_alignment.check import records,profile
    from alignment.pede import read_pede
    for name in ('geometry','data','nominal','physical_derivatives','corrected_physical_derivatives','solve','correction','corrected','postsolve','control','controlsolve'):require(args.result,name)
    p=stage(args.result,args.validation_name)
    selected=labels(args.mode);combined=args.mode!='l1_rx'
    injected={700104:INJECTED_RX_RAD}
    if combined:injected.update({700102:.150,700202:.200})
    truth=json.loads((args.result/'data/shifted/channels_truth.json').read_text())
    base=json.loads((args.result/'data/control/channels_truth.json').read_text())
    pose_checks(base['sensors'],truth['sensors'],{1:.150,2:.200} if combined else {},{1:INJECTED_RX_RAD})
    # Independent XML whitelist: only selected module references, component X
    # translation and the selected L1 component Y rotation serialization may vary.
    def structure(n):return n.tag,dict(n.attrib),(n.text or '').strip(),tuple(structure(c) for c in n)
    nominal_xml=ET.parse(args.result/'geometry/fixtures/nominal.xml').getroot()
    for xml in (args.result/'geometry/truth.xml',args.result/'correction/corrected.xml'):
        candidate=ET.parse(xml).getroot();detector=candidate.find("./detectors/detector[@name='SiMAPS']")
        original=nominal_xml.find("./detectors/detector[@name='SiMAPS']")
        for layer in ([1,2] if combined else [1]):
            a=original.find(f"./layer[@id='{layer}']");b=detector.find(f"./layer[@id='{layer}']")
            module=detector.find(f"./module[@name='{b.get('module')}']")
            reference=original.find(f"./module[@name='{a.get('module')}']")
            normalized=copy.deepcopy(module);normalized.set('name',reference.get('name'))
            normalized.find('./module_component/position').set('x',reference.find('./module_component/position').get('x'))
            if layer==1:normalized.find('./module_component/rotation').set('y',reference.find('./module_component/rotation').get('y'))
            assert structure(normalized)==structure(reference)
            detector.remove(module);b.set('module',a.get('module'))
        assert structure(candidate)==structure(nominal_xml)
    solution=json.loads((args.result/'solve/independent.json').read_text())
    control_solution=json.loads((args.result/'controlsolve/independent.json').read_text())
    values=read_pede(args.result/'solve/millepede.res');post=read_pede(args.result/'postsolve/millepede.res')
    actual=json.loads((args.result/'correction/geometry_audit/geometry.json').read_text())['sensors']
    # Geometry tolerance is predeclared as five original-covariance nominal errors,
    # separately from the much tighter actual pose serialization consistency gate.
    tolerances={k:5*solution['nominal_sigma'][i] for i,k in enumerate(selected)}
    for i,k in enumerate(selected):
        assert abs(values[k]-injected[k])<tolerances[k]
        assert abs(control_solution['parameters'][str(k)])<5*control_solution['nominal_sigma'][i]
        assert abs(post[k])<2e-5,(k,post[k])
    from geometry.transforms import orientation_distance
    angle_error=orientation_distance(truth['sensors'][1]['acts_rotation'],actual[1]['acts_rotation'])
    assert angle_error<tolerances[700104]
    input_path=args.result/'data/shifted.root';payload=channel_values(input_path)
    assert digest(input_path)==json.loads((args.result/'data/shifted_input.json').read_text())['file_sha256']
    assert channel_values(args.result/'nominal/reco.root')==channel_values(args.result/'corrected/reco.root')==payload
    changed=sum(a[1][1][0]!=b[1][1][0] for a,b in zip(payload,channel_values(args.result/'data/control.root')))
    assert changed>=args.events//4,'Rotation/translation fixture must have nontrivial quantized channel changes'
    nominal_audit=json.loads((args.result/'nominal/audit.json').read_text())
    corrected_audit=json.loads((args.result/'corrected/audit.json').read_text())
    for a,b in zip(nominal_audit['events'],corrected_audit['events']):
        for ha,hb in zip(a['measurement_details'],b['measurement_details']):
            assert all(ha[k]==hb[k] for k in ('cell_id','volume_id','geometry_id'))
            assert np.allclose(ha['loc_mm'],hb['loc_mm'],atol=2e-6,rtol=0)
            assert np.allclose(ha['covariance_mm2'],hb['covariance_mm2'],atol=1e-12,rtol=0)
    input_frame=next(iter(reading.get_reader(str(input_path)).get('events')))
    assert set(input_frame.getAvailableCollections())=={'EventHeader','TelescopeChannels'}
    summaries={};distributions={}
    for name in ('nominal','corrected','control'):
        audit=json.loads((args.result/name/'audit.json').read_text());mille=json.loads((args.result/name/'mille.json').read_text())
        assert audit['processed']==audit['accepted']==args.events and audit['rejected']==0
        blocks=list(records(args.result/name/'mille.dat'));assert len(blocks)==mille['records']==args.events
        local_residuals=[];by_layer={l:[] for l in range(5)}
        gid_to_layer={d['geometry_id']:l for l,d in enumerate(audit['events'][0]['measurement_details'])}
        for event,rows in zip(mille['events'],blocks):
            assert len(rows)==10 and {k for row in rows for k in row[3]}==set(selected)
            for equation in event['equations']:
                w=np.array(equation['whitening']);cov=np.array(equation['covariance'])
                assert np.allclose(w@cov@w.T,np.eye(2),atol=1e-10)
                # Audit every selected official Mille coefficient against the
                # unchanged ACTS columns and calibrated covariance whitening.
                g=w@np.array(equation['global']);l=equation['layer']
                for j in (0,1):
                    coefficients=rows[2*l+j][3]
                    expected={k:g[j,3 if k==700104 else 1] for k in selected if (1 if k==700104 else (k-700002)//100)==l and g[j,3 if k==700104 else 1]!=0}
                    assert coefficients.keys()==expected.keys()
                    assert all(abs(coefficients[k]-expected[k])<1e-10 for k in expected)
        for event in audit['events']:
            assert event['measurements']==5 and event['outliers']==0 and event['holes']==2
            local_residuals.extend(s['residual_mm'] for s in event['smoothed_states'])
            for state in event['smoothed_states']:by_layer[gid_to_layer[state['geometry_id']]].append(state['residual_mm'])
        # EDM read-back and reconstructed-position/local-coordinate consistency.
        frames=list(reading.get_reader(str(args.result/name/'reco.root')).get('events'));assert len(frames)==args.events
        geometry=actual if name=='corrected' else base['sensors']
        rec_truth=[]
        for i,frame in enumerate(frames):
            hits=frame.get('TelescopeHits');tracks=frame.get('TelescopeTracks');assert len(hits)==5 and len(tracks)==1
            assert len(frame.get('TelescopeHitAssociations'))==0 and tracks[0].getPdg()==11
            assert frame.get('EventHeader')[0].getEventNumber()==i
            seeds=frame.get('TelescopeSeeds');assert len(seeds)==1 and len(tracks[0].getMeasurements())==5
            assert tracks[0].getTrajectory().getSeed()==seeds[0]
            points=np.array([[h.getPosition().x,h.getPosition().y,h.getPosition().z] for h in hits])
            direction=points[-1]-points[0];direction/=np.linalg.norm(direction)
            expected=points[0]+(249.-points[0,0])/direction[0]*direction
            center=seeds[0].getPerigee();params=seeds[0].getParams()
            assert np.allclose([center.x,center.y,center.z],expected,atol=2e-6,rtol=0)
            assert abs(params.getPhi()-math.atan2(direction[1],direction[0]))<1e-6
            assert abs(params.getTheta()-math.acos(direction[2]))<1e-6
            for hit,measurement in zip(hits,frame.get('TelescopeMeasurements')):
                layer=(hit.getCellID()>>11)&63;sensor=geometry[layer]
                point=np.array([hit.getPosition().x,hit.getPosition().y,hit.getPosition().z])
                local=np.array(sensor['acts_rotation']).T@(point-sensor['center_mm'])
                assert np.allclose(local[:2],[measurement.getLoc().a,measurement.getLoc().b],atol=3e-6,rtol=0)
                assert hit.getRawHit().isAvailable() and measurement.getSurface()==sensor['geometry_id']
                if name!='control':rec_truth.append((point-np.array(truth['events'][i]['channels'][layer]['physical_intersection_mm'])).tolist())
        chi2=np.array([e['chi2'] for e in audit['events']]);ndf=sum(e['stored_ndf'] for e in audit['events']);assert ndf==10*args.events
        residual=np.array(local_residuals)
        summaries[name]={'accepted':audit['accepted'],'records':len(blocks),'chi2_sum':float(chi2.sum()),'stored_ndf_sum':ndf,
          'chi2_per_stored_ndf':float(chi2.sum()/ndf),'residual_mean_uv_mm':residual.mean(axis=0).tolist(),
          'residual_rms_uv_mm':np.sqrt(np.mean(residual**2,axis=0)).tolist(),'maximum_abs_residual_mm':float(np.max(np.abs(residual))),
          'layer_residual_mean_uv_mm':{l:np.mean(v,axis=0).tolist() for l,v in by_layer.items()},
          'layer_residual_rms_uv_mm':{l:np.sqrt(np.mean(np.array(v)**2,axis=0)).tolist() for l,v in by_layer.items()},
          'rec_minus_truth_global_rms_mm':np.sqrt(np.mean(np.array(rec_truth)**2,axis=0)).tolist() if rec_truth else None}
        distributions[name]={'chi2':chi2.tolist(),'residual':residual.tolist()}
    assert summaries['corrected']['chi2_sum']<summaries['nominal']['chi2_sum']
    assert np.linalg.norm(summaries['corrected']['residual_rms_uv_mm'])<np.linalg.norm(summaries['nominal']['residual_rms_uv_mm'])
    diagnostics={}
    for name in ('solve','postsolve','controlsolve'):
        log=(args.result/name/'stdout.log').read_text();rejects=[]
        for line in log.splitlines():
            parts=line.split()
            if len(parts)>=7 and parts[0].isdigit() and parts[1].isdigit() and parts[-1] in ('FMS','FM','F','MS') and parts[-2].isdigit():rejects.append(int(parts[-3]))
        assert rejects and max(rejects)==0
        match=re.search(r'Sum\(Chi\^2\)/Sum\(Ndf\)\s*=\s*([0-9.Ee+\-]+)\s*/\s*\(\s*(\d+)\s*-\s*(\d+)\s*\)',log)
        assert match and int(match[2])==6*args.events and int(match[3])==len(selected)
        reconstruction={'solve':'nominal','postsolve':'corrected','controlsolve':'control'}[name]
        pieces=[profile(block,selected) for block in records(args.result/reconstruction/'mille.dat')]
        normal=sum((v[0] for v in pieces),np.zeros((len(selected),len(selected))))
        rhs=sum((v[1] for v in pieces),np.zeros(len(selected)))
        chi2=sum(v[2] for v in pieces)-rhs@np.linalg.solve(normal,rhs)
        assert abs(chi2-float(match[1]))<1e-5
        ndf=int(match[2])-int(match[3])
        diagnostics[name]={'end_status':(args.result/name/'millepede.end').read_text().strip(),'rejected_local_fits':rejects,
          'chi2':float(match[1]),'ndf':ndf,'chi2_per_ndf':float(match[1])/ndf,'independent_profiled_chi2':float(chi2),
          'error_rescaling_recommended':'multiply all input standard deviations' in log,'error_rescaling_applied':False}
    ROOT.gROOT.SetBatch(True);f=ROOT.TFile.Open(str(p/'rotation.root'),'NEW');assert f and not f.IsZombie()
    for name,data in distributions.items():
        h=ROOT.TH1D(name+'_chi2',name+';ACTS chi2/stored-NDF;Tracks',100,0,max(2,max(data['chi2'])/10*1.05))
        for x in data['chi2']:h.Fill(x/10)
        h.Write()
        for j,axis in enumerate(('u','v')):
            h=ROOT.TH1D(name+'_'+axis,name+';Local residual [mm];Measurements',160,-.3,.3)
            for r in data['residual']:h.Fill(r[j])
            h.Write()
    f.Close();f=ROOT.TFile.Open(str(p/'rotation.root'));assert f.GetListOfKeys().GetEntries()==9;f.Close()
    result={'passed':True,'mode':args.mode,'events':args.events,'injected':injected,'parameters':values,'parameter_units':solution['parameter_units'],
      'errors':{k:values[k]-injected[k] for k in selected},'geometric_tolerance':tolerances,'orientation_error_rad':angle_error,
      'center_bias_mm':{l:(np.array(actual[l]['center_mm'])-truth['sensors'][l]['center_mm']).tolist() for l in (1,2)},
      'actual_l1_geometry_id':actual[1]['geometry_id'],'actual_l1_volume_id':actual[1]['volume_id'],
      'rank':solution['rank'],'condition_raw_mixed_units':solution['condition'],'condition_diagonal_scaled':solution['condition_diagonal_scaled'],
      'correlation':solution['correlation'],'nominal_sigma':solution['nominal_sigma'],'pede_reported_sigma':solution['pede_reported_sigma'],'post_correction':post,
      'summaries':summaries,'pede_diagnostics':diagnostics,'changed_l1_channel_events':changed,
      'input_channel_sha256':channel_digest(payload),'immutable_input_file_sha256':digest(input_path),
      'truth_used_for_inference':False,'geometry_activated':False,'scope':'quantized synthetic channels, zero field, no assigned ACTS material; not statistical coverage'}
    write_json(p/'report.json',result);done(p,passed=True)

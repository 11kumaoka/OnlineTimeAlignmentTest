"""Selected native rotation closure gates, not a general alignment framework."""
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
INJECTED_RY_RAD=.005
INJECTED_RZ_RAD=.005


def is_three(mode):
    return mode in ('l1_rx_ry_rz','l1_rx_ry_rz_negative')


def is_coupled(mode):
    return mode in ('l1_ry_rz','l1_ry_rz_negative') or is_three(mode)


def injected_vector(mode):
    return injected_rotation(mode) if is_three(mode) else [0.,*injected_rotation(mode)]


def axis(mode):
    if is_three(mode):return 'xyz'
    if is_coupled(mode):return 'yz'
    return 'y' if mode in ('l1_ry','l1_ry_negative') else ('z' if mode in ('l1_rz','l1_rz_negative') else 'x')


def rotation_label(mode):
    return {'x':700104,'y':700105,'z':700106}[axis(mode)]


def injected_rx(mode):
    return -INJECTED_RX_RAD if mode=='l1_rx_negative' else INJECTED_RX_RAD


def injected_rotation(mode):
    if is_three(mode):return [-.0018,-.0025,.0025] if mode.endswith('_negative') else [.0018,.0025,-.0025]
    if is_coupled(mode):return [-.0025,.0025] if mode.endswith('_negative') else [.0025,-.0025]
    if axis(mode)=='x':return injected_rx(mode)
    magnitude=INJECTED_RY_RAD if axis(mode)=='y' else INJECTED_RZ_RAD
    return -magnitude if mode.endswith('_negative') else magnitude


def labels(mode):
    if is_three(mode):return [700104,700105,700106]
    if is_coupled(mode):return [700105,700106]
    return [rotation_label(mode)] if mode!='l1_y_rx_l2_y' else [700102,700104,700202]


def config_name(mode):
    if is_three(mode):return 'l1_global_rx_ry_rz'
    if is_coupled(mode):return 'l1_global_ry_rz'
    return 'l1_y_rx_l2_y' if mode=='l1_y_rx_l2_y' else 'l1_global_r'+axis(mode)


def rotate_component(component,increment,axis='x'):
    """Restricted left-Global Exp(dw), current sensitive-center pivot.

    Actual DD4hep probes establish Rx = -(XML y + pi/2) and
    Ry = -(XML x + pi/2) on their separate one-axis charts. Compositions
    outside each subgroup are rejected. Rz uses the independently verified
    alternate chart x=0, y=-pi/2-Rz, z=pi/2; this is not a general serializer.
    """
    if axis in ('yz','xyz'):return rotate_coupled_component(component,increment,full=axis=='xyz')
    if axis not in ('x','y','z') or not math.isfinite(increment) or abs(increment)>.01:
        raise ValueError('Only bounded separate L1 Global Rx, Ry or Rz enabled')
    r=component.find('rotation')
    x,y,z=[xml_number(r.get(a,'0'),{'pi':math.pi}) for a in 'xyz']
    if axis=='z':
        # The alternate zero chart is physically identical to the nominal chart.
        # Only the pure-Rz subgroup is admitted; never decompose a general pose.
        nominal=abs(x+math.pi/2)<1e-12 and abs(y+math.pi/2)<1e-12 and abs(z)<1e-12
        selected=abs(x)<1e-12 and abs(z-math.pi/2)<1e-12
        if not (nominal or selected):raise ValueError('Unsupported composition outside the selected Rz chart')
        current=0. if nominal else -(y+math.pi/2)
        vector=rotation_log(multiply(rotation_exp((0.,0.,increment)),rotation_exp((0.,0.,current))))
        if abs(vector[0])+abs(vector[1])>1e-12:raise ValueError('Outside pure-Rz subgroup')
        r.set('x','0');r.set('y',f'{-math.pi/2-vector[2]:.17g}');r.set('z',f'{math.pi/2:.17g}')
        return
    if abs(z)>1e-12 or abs((x if axis=='x' else y)+math.pi/2)>1e-12:
        raise ValueError('Unsupported composition outside the selected one-axis chart')
    index=0 if axis=='x' else 1
    current=[0.,0.,0.];current[index]=-((y if axis=='x' else x)+math.pi/2)
    delta=[0.,0.,0.];delta[index]=increment
    vector=rotation_log(multiply(rotation_exp(delta),rotation_exp(current)))
    if sum(abs(v) for i,v in enumerate(vector) if i!=index)>1e-12:
        raise ValueError('Outside selected one-axis subgroup')
    r.set('y' if axis=='x' else 'x',f'{-math.pi/2-vector[index]:.17g}')


def pose_checks(before,after,shifts,rx,axis='x'):
    """Actual DD4hep and ACTS poses, not XML attribute assumptions."""
    for a,b in zip(before,after):
        layer=a['layer'];vector=[0.,0.,0.]
        if axis=='xyz':vector=rx.get(layer,[0.,0.,0.])
        elif axis=='yz':vector[1:]=rx.get(layer,[0.,0.])
        else:vector['xyz'.index(axis)]=rx.get(layer,0.)
        q=np.array(rotation_exp(vector))
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
            if axis in ('y','z','yz','xyz'):
                # Native component half lengths: X=50, Y=.025, Z=50 mm.
                # Parent module world half lengths: X=.325, Y/Z=50.25 mm.
                extent=np.abs(np.array(b['dd4hep_rotation']))@np.array([50.,.025,50.])
                offset=np.array(b['center_mm'])-np.array([250.+50*layer,0.,0.])
                assert np.all(np.abs(offset)+extent < [.325,50.25,50.25])
                for signs in __import__('itertools').product((-1,1),repeat=3):
                    corner=np.array(b['center_mm'])+np.array(b['dd4hep_rotation'])@(np.array(signs)*[50.,.025,50.])
                    radius=np.linalg.norm(corner[:2]);nominal=250.+50*layer
                    assert nominal-.025-1 < radius < math.hypot(nominal+.025+.4,50.3)+1
                    assert abs(corner[2])<51.


def physical_derivatives(args,reconstruction="nominal"):
    """Frozen native reference against fresh real DD4hep/ACTS surface perturbations."""
    if is_coupled(args.mode):return coupled_physical_derivatives(args,reconstruction)
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
            displaced_xml(geometry,q/'geometry.xml',{},rotations={1:sign*step},rotation_axis=axis(args.mode))
            execute([args.build/'TelescopeChannels',q/'geometry.xml',0,q/'geometry.json'],q,env=environment(args.build))
            sensors=json.loads((q/'geometry.json').read_text())['sensors']
            pose_checks(base,sensors,{}, {1:sign*step},axis=axis(args.mode))
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
            error=max(error,float(np.max(np.abs(finite-np.array(equation['global'])[:,3+'xyz'.index(axis(args.mode))]))));checks+=1
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
    rotations={1:[values[k] for k in labels(args.mode)] if is_coupled(args.mode) else values[rotation_label(args.mode)]}
    nominal=args.result/'geometry/fixtures/nominal.xml'
    displaced_xml(nominal,p/'corrected.xml',shifts,rotations=rotations,rotation_axis=axis(args.mode))
    write_json(p/'provenance.json',{'parent_sha256':digest(nominal),'pede_sha256':digest(args.result/'solve/millepede.res'),
       'physical_global_y_mm':shifts,'physical_global_r'+axis(args.mode)+'_rad':rotations,'pivot':'current sensitive center',
       'composition':(('Rnew=Exp([dRx,dRy,dRz]) Rcurrent; bounded L1 full rotation-vector update' if is_three(args.mode) else 'Rnew=Exp([0,dRy,dRz]) Rcurrent; current full pose, not a closed two-axis subgroup') if is_coupled(args.mode) else 'Rnew=Exp(dw_global) Rcurrent; selected '+axis(args.mode)+' subgroup'),'truth_used':False,'activated':False})
    q=stage(p,'geometry_audit');execute([args.build/'TelescopeChannels',p/'corrected.xml',0,q/'geometry.json'],q,env=environment(args.build))
    base=json.loads((args.result/'data/control/channels_truth.json').read_text())['sensors']
    pose_checks(base,json.loads((q/'geometry.json').read_text())['sensors'],shifts,rotations,axis=axis(args.mode))
    done(p,physical_global_y_mm=shifts,physical_rotation_rad=rotations,rotation_axis=axis(args.mode))


def check(args):
    import ROOT
    from podio import reading
    from validation.telescope_closure.closure import channel_values,channel_digest
    from validation.telescope_alignment.check import records,profile
    from alignment.pede import read_pede
    for name in ('geometry','data','nominal','physical_derivatives','corrected_physical_derivatives','solve','correction','corrected','postsolve','control','controlsolve'):require(args.result,name)
    p=stage(args.result,args.validation_name)
    selected=labels(args.mode);combined=args.mode=='l1_y_rx_l2_y'
    injected=dict(zip(labels(args.mode),injected_rotation(args.mode))) if is_coupled(args.mode) else {rotation_label(args.mode):injected_rotation(args.mode)}
    if combined:injected.update({700102:.150,700202:.200})
    truth=json.loads((args.result/'data/shifted/channels_truth.json').read_text())
    base=json.loads((args.result/'data/control/channels_truth.json').read_text())
    pose_checks(base['sensors'],truth['sensors'],{1:.150,2:.200} if combined else {},{1:injected_rotation(args.mode)},axis=axis(args.mode))
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
            if layer==1:
                attributes='xyz' if axis(args.mode) in ('z','yz','xyz') else ('x' if axis(args.mode)=='y' else 'y')
                for attribute in attributes:
                    normalized.find('./module_component/rotation').set(attribute,reference.find('./module_component/rotation').get(attribute))
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
        assert abs(post[k])<(solution['nominal_sigma'][i]/4 if axis(args.mode) in ('y','z','yz','xyz') else 2e-5),(k,post[k])
    from geometry.transforms import orientation_distance
    angle_error=orientation_distance(truth['sensors'][1]['acts_rotation'],actual[1]['acts_rotation'])
    if is_coupled(args.mode):
        covariance=np.linalg.inv(np.array(solution['normal']))
        error=np.array([values[k]-injected[k] for k in selected])
        assert error@np.linalg.solve(covariance,error)<25
        assert angle_error<5*np.sqrt(np.linalg.eigvalsh(covariance).max())
        assert angle_error<np.linalg.norm(injected_rotation(args.mode))
        require(args.result,'coupled_pose')
    else:assert angle_error<tolerances[rotation_label(args.mode)]
    input_path=args.result/'data/shifted.root';payload=channel_values(input_path)
    assert digest(input_path)==json.loads((args.result/'data/shifted_input.json').read_text())['file_sha256']
    assert channel_values(args.result/'nominal/reco.root')==channel_values(args.result/'corrected/reco.root')==payload
    changed=sum(a[1][1][0]!=b[1][1][0] for a,b in zip(payload,channel_values(args.result/'data/control.root')))
    assert changed>=args.events//(32 if axis(args.mode) in ('y','z','yz','xyz') else 4),'Rotation/translation fixture must have nontrivial quantized channel changes'
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
                    expected={k:g[j,k-700101 if k in (700104,700105,700106) else 1] for k in selected if (1 if k in (700104,700105,700106) else (k-700002)//100)==l and g[j,k-700101 if k in (700104,700105,700106) else 1]!=0}
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
        pieces=[profile(block,selected,require_global_rank=not is_coupled(args.mode)) for block in records(args.result/reconstruction/'mille.dat')]
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
        for j,coordinate in enumerate(('u','v')):
            h=ROOT.TH1D(name+'_'+coordinate,name+';Local residual [mm];Measurements',160,-.3,.3)
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
    if is_coupled(args.mode):
        result.update(injected_rotation_vector_rad=injected_vector(args.mode),
            injected_matrix=rotation_exp(injected_vector(args.mode)),
            recovered_rotation_vector_rad=([values[k] for k in selected] if is_three(args.mode) else [0.,values[700105],values[700106]]),
            nominal_covariance_rad2=covariance.tolist(),
            initial_error_mahalanobis_squared=float(error@np.linalg.solve(covariance,error)),
            truth_definition='single rotation vector, not an ordered Euler product')
    write_json(p/'report.json',result);done(p,passed=True)


def component_matrix(component):
    """Effective sensitive-to-module basis, checked against actual pinned DD4hep.

    This telescope parent/module frame is fixed by its existing geometry fixture.
    It is not a replacement geometry provider or a generic detector adapter.
    """
    r=component.find('rotation')
    x,y,z=[xml_number(r.get(a,'0'),{'pi':math.pi}) for a in 'xyz']
    return np.array(multiply(rotation_exp((x,0,0)),multiply(rotation_exp((0,y,0)),rotation_exp((0,0,z)))))


def rotate_coupled_component(component,increment,full=False):
    """Serialize a bounded physical left-Global rotation-vector update.

    The two-axis scope retains known commutator Rx but never fits Rx. The explicit
    full scope permits all three bounded L1 components. General singular Euler
    extraction is refused; exact one-axis targets use validated restricted charts.
    """
    from validation.telescope_closure.closure import MODULE_TO_GLOBAL
    parent=np.array(MODULE_TO_GLOBAL)
    delta=np.array(increment,dtype=float)
    if delta.shape!=((3,) if full else (2,)) or not np.isfinite(delta).all() or np.linalg.norm(delta)>.01:
        raise ValueError('Only bounded selected L1 Global rotation-vector increments supported')
    nominal=np.array(multiply(rotation_exp((-math.pi/2,0,0)),rotation_exp((0,-math.pi/2,0))))
    current=component_matrix(component)
    pose=parent@current@nominal.T@parent.T
    w=np.array(rotation_log(pose.tolist()))
    if np.linalg.norm(w)>.01 or (not full and abs(w[0])>1e-4):
        raise ValueError('Current pose outside bounded coupled-tilt scope')
    target=np.array(rotation_exp(delta if full else [0.,*delta]))@parent@current
    local=parent.T@target
    cy=math.hypot(local[0,0],local[0,1])
    if cy<1e-6:
        physical=np.array(rotation_log((target@nominal.T@parent.T).tolist()))
        if full and abs(physical[1])+abs(physical[2])<1e-12:
            angles=(-math.pi/2,-math.pi/2-physical[0],0.)
        elif abs(physical[0])+abs(physical[2])<1e-12:
            angles=(-math.pi/2-physical[1],-math.pi/2,0.)
        elif abs(physical[0])+abs(physical[1])<1e-12:
            angles=(0.,-math.pi/2-physical[2],math.pi/2)
        else:raise ValueError('Ambiguous near-singular coupled serialization chart')
    else:
        angles=(math.atan2(-local[1,2],local[2,2]),
                math.atan2(local[0,2],cy),math.atan2(-local[0,1],local[0,0]))
    candidate=copy.deepcopy(component)
    for name,value in zip('xyz',angles):candidate.find('rotation').set(name,f'{value:.17g}')
    if not np.allclose(parent@component_matrix(candidate),target,atol=5e-13,rtol=0):
        raise ValueError('Coupled target matrix cannot be serialized safely')
    # Mutation follows successful target-matrix and chart validation.
    for name in 'xyz':component.find('rotation').set(name,candidate.find('rotation').get(name))


def coupled_pose_gate(args):
    """Independent real-constructor composition/inverse checks before inference."""
    from validation.telescope_closure.closure import displaced_xml,environment
    from geometry.transforms import orientation_distance
    p=stage(args.result,'coupled_pose')
    base=json.loads((args.result/'data/control/channels_truth.json').read_text())['sensors']
    if is_three(args.mode):
        truth=json.loads((args.result/'data/shifted/channels_truth.json').read_text())['sensors']
        pose_checks(base,truth,{}, {1:injected_rotation(args.mode)},axis=axis(args.mode))
    original=args.result/'geometry/fixtures/nominal.xml'
    previous=base;geometry=original;chain=[]
    deltas=[('forward',[.0025,-.0025]),('cross',[-.001,.0015]),('inverse_cross',[.001,-.0015]),('inverse_forward',[-.0025,.0025])]
    if is_three(args.mode):deltas=[('forward',[.0018,.0025,-.0025]),('cross',[-.0007,-.001,.0015]),('inverse_cross',[.0007,.001,-.0015]),('inverse_forward',[-.0018,-.0025,.0025])]
    for name,delta in deltas:
        q=stage(p,name)
        displaced_xml(geometry,q/'geometry.xml',{},rotations={1:delta},rotation_axis=axis(args.mode))
        execute([args.build/'TelescopeChannels',q/'geometry.xml',0,q/'geometry.json'],q,env=environment(args.build))
        actual=json.loads((q/'geometry.json').read_text())['sensors']
        pose_checks(previous,actual,{}, {1:delta},axis=axis(args.mode))
        chain.append(actual);previous=actual;geometry=q/'geometry.xml'
    assert np.allclose(chain[2][1]['acts_rotation'],chain[0][1]['acts_rotation'],atol=2e-12,rtol=0)
    assert np.allclose(chain[3][1]['acts_rotation'],base[1]['acts_rotation'],atol=2e-12,rtol=0)
    joint=rotation_exp([0,.0025,-.0025])
    ordered=multiply(rotation_exp([0,.0025,0]),rotation_exp([0,0,-.0025]))
    if is_three(args.mode):
        joint=rotation_exp(injected_vector(args.mode))
        ordered=multiply(rotation_exp([.0018,0,0]),multiply(rotation_exp([0,.0025,0]),rotation_exp([0,0,-.0025])))
    difference=orientation_distance(joint,ordered)
    assert difference>1e-7,'Finite rotation vector and ordered product must remain distinct'
    write_json(p/'report.json',{'passed':True,'ordered_vs_joint_distance_rad':difference,
        'inverse_chain_max_matrix_error':float(np.max(np.abs(np.array(chain[3][1]['acts_rotation'])-base[1]['acts_rotation']))),
        'current_pose_retains_noncommutative_cross_axis_terms':True,'geometry_activated':False})
    done(p,passed=True)


def coupled_physical_derivatives(args,reconstruction):
    """Selected rotation columns against independent actual DD4hep poses."""
    from validation.telescope_closure.closure import displaced_xml,environment
    if reconstruction=='nominal':
        if (args.result/'coupled_pose').exists():require(args.result,'coupled_pose')
        else:coupled_pose_gate(args)
    p=stage(args.result,'physical_derivatives' if reconstruction=='nominal' else 'corrected_physical_derivatives')
    native=json.loads((args.result/reconstruction/'mille.json').read_text())
    geometry=args.result/('geometry/fixtures/nominal.xml' if reconstruction=='nominal' else 'correction/corrected.xml')
    base_path=args.result/('data/control/channels_truth.json' if reconstruction=='nominal' else 'correction/geometry_audit/geometry.json')
    base=json.loads(base_path.read_text())['sensors'];errors={};checks=0
    columns=(3,4,5) if is_three(args.mode) else (4,5)
    for column in columns:
        for step in (1e-4,1e-5,1e-6):
            poses=[]
            for sign in (1,-1):
                delta=[0.]*len(columns);delta[column-columns[0]]=sign*step
                q=stage(p,f'column_{column}_step_{step:g}_{sign:+d}')
                displaced_xml(geometry,q/'geometry.xml',{},rotations={1:delta},rotation_axis=axis(args.mode))
                execute([args.build/'TelescopeChannels',q/'geometry.xml',0,q/'geometry.json'],q,env=environment(args.build))
                sensors=json.loads((q/'geometry.json').read_text())['sensors']
                pose_checks(base,sensors,{}, {1:delta},axis=axis(args.mode));poses.append(sensors[1])
            error=0.
            for event in native['events']:
                point=np.array(event['reference_position_mm']);direction=np.array(event['reference_direction']);predictions=[]
                for sensor in poses:
                    r=np.array(sensor['acts_rotation']);center=np.array(sensor['center_mm']);normal=r[:,2]
                    intersection=point+direction*(normal@(center-point))/(normal@direction)
                    predictions.append((r.T@(intersection-center))[:2])
                finite=(predictions[0]-predictions[1])/(2*step)
                equation=next(e for e in event['equations'] if e['layer']==1)
                error=max(error,float(np.max(np.abs(finite-np.array(equation['global'])[:,column]))));checks+=1
            assert error<2e-5,(column,step,error)
            errors[f'{column}_{step}']=error
    write_json(p/'report.json',{'passed':True,'checks':checks,'errors_mm_per_rad':errors,
        'maximum_error_mm_per_rad':max(errors.values()),'model_sha256':native['model_sha256'],
        'method':'independent actual DD4hep/ACTS perturbations; selected left-Global columns, original native reference'})
    done(p,passed=True)

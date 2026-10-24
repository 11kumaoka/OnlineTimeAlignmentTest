#!/usr/bin/env python3
"""Focused readout-level reconstruction closure; run independent steps in the fixed container."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO))
from research_common import execute,stage,done,require,write_json,digest
from geometry.transforms import matvec,transpose
from validation.telescope_geometry.prepare import prepare
from alignment.align import read_pede
from validation.telescope_alignment.check import records,profile

LABELS=[700102,700202]
MODULE_TO_GLOBAL=((0.,0.,1.),(-1.,0.,0.),(0.,-1.,0.))


def displaced_xml(nominal,output,shifts):
    """Apply only physical Global Y translations via the validated barrel module frame."""
    if output.exists():raise ValueError('Geometry output must be new')
    root=ET.parse(nominal).getroot()
    detector=root.find("./detectors/detector[@name='SiMAPS']")
    for layer,delta in shifts.items():
        if int(layer) not in (1,2) or not math.isfinite(delta):raise ValueError('Only finite L1/L2 Global Y supported')
        placement=detector.find(f"./layer[@id='{int(layer)}']")
        original=detector.find(f"./module[@name='{placement.get('module')}']")
        module=copy.deepcopy(original);module.set('name',original.get('name')+f'_L{layer}')
        component=module.find('./module_component')
        position=component.find('position')
        offset=matvec(transpose(MODULE_TO_GLOBAL),(0.,delta,0.))
        for axis,value in zip('xyz',offset):
            current=float(position.get(axis,'0').replace('*mm',''))
            position.set(axis,f'{current+value:.17g}*mm')
        # Reject changes to sensor shape, material, rotation, or segmentation.
        original_component=copy.deepcopy(original.find('./module_component'))
        comparison=copy.deepcopy(component)
        comparison.remove(comparison.find('position'));original_component.remove(original_component.find('position'))
        assert ET.tostring(comparison)==ET.tostring(original_component)
        detector.append(module);placement.set('module',module.get('name'))
    ET.indent(root);ET.ElementTree(root).write(output,encoding='unicode')


def environment(build):
    env=os.environ.copy()
    env['LD_LIBRARY_PATH']=f'{build}:{REPO}/external/install/lib:'+env.get('LD_LIBRARY_PATH','')
    env['JANA_PLUGIN_PATH']=str(build)+':'+env.get('JANA_PLUGIN_PATH','')
    env['PYTHONDONTWRITEBYTECODE']='1'
    return env


def channel_values(path):
    import ROOT
    from podio import reading
    reader=reading.get_reader(str(path));values=[]
    for frame in reader.get('events'):
        header=frame.get('EventHeader')[0]
        channels=frame.get('TelescopeChannels')
        values.append((int(header.getEventNumber()),[(int(h.getCellID()),int(h.getCharge()),int(h.getTimeStamp())) for h in channels]))
    return values


def channel_digest(values):
    data=b''
    for event,hits in values:
        data+=struct.pack('<qI',event,len(hits))
        for cell,charge,time in hits:data+=struct.pack('<Qiq',cell,charge,time)
    return hashlib.sha256(data).hexdigest()


def pack(source,output):
    import ROOT
    from podio.frame import Frame
    from podio import root_io
    if output.exists():raise ValueError('Channel ROOT output must be new')
    data=json.loads(source.read_text());writer=root_io.Writer(str(output))
    for event in data['events']:
        headers=ROOT.edm4hep.EventHeaderCollection();header=headers.create()
        header.setRunNumber(1);header.setEventNumber(event['event'])
        hits=ROOT.edm4eic.RawTrackerHitCollection()
        for channel in event['channels']:
            hit=hits.create();hit.setCellID(channel['cell_id']);hit.setCharge(channel['charge']);hit.setTimeStamp(channel['timestamp'])
        frame=Frame();frame.put(headers,'EventHeader');frame.put(hits,'TelescopeChannels')
        writer.write_frame(frame,'events')
    # Pinned podio 1.7 exposes finalization only on the underlying C++ ROOTWriter.
    writer._writer.finish()
    values=channel_values(output)
    assert len(values)==len(data['events']) and all(len(hits)==5 for _,hits in values)
    return {'file_sha256':digest(output),'channel_payload_sha256':channel_digest(values),'events':len(values),
            'collections':['EventHeader','TelescopeChannels'],'truth_in_input':False}


def geometry_step(args):
    p=stage(args.result,'geometry')
    prepare(p/'fixtures',initialize_metadata=True)
    nominal=p/'fixtures/nominal.xml'
    displaced_xml(nominal,p/'truth.xml',{1:.150,2:.200})
    done(p,nominal_sha256=digest(nominal),truth_sha256=digest(p/'truth.xml'),injected_global_y_mm={'1':.150,'2':.200})


def data_step(args):
    require(args.result,'geometry');p=stage(args.result,'data')
    for name,xml in [('shifted',args.result/'geometry/truth.xml'),('control',args.result/'geometry/fixtures/nominal.xml')]:
        q=stage(p,name)
        execute([args.build/'TelescopeChannels',xml,args.events,q/'channels_truth.json'],q,env=environment(args.build))
        info=pack(q/'channels_truth.json',p/(name+'.root'))
        write_json(p/(name+'_input.json'),info)
    done(p,events=args.events)


def reconstruct(args,name,geometry,input_name,limit=None,cut=None):
    require(args.result,'data')
    if json.loads((args.result/'data/complete.json').read_text())['events']!=args.events:
        raise ValueError('Event count must match immutable input metadata')
    if name in ('corrected','control') and (args.result/'nominal/complete.json').exists():
        initial=json.loads((args.result/'nominal/complete.json').read_text())['measurement_selector_chi2_cut']
        if (cut or 15.)!=initial:raise ValueError('Closure passes must use the same measurement-selection cut')
    p=stage(args.result,name);env=environment(args.build)
    gate=stage(p,'gate')
    execute([args.build/'TelescopeMilleDerivatives',geometry,'geometry-center',gate/'derivatives.json'],gate,env=env)
    source=args.result/'data'/f'{input_name}.root';before=digest(source)
    # This invocation has no Truth trajectories, placements or MC collections.
    command=['eicrecon','-Pplugins_to_ignore=default',
      '-Pplugins=log,dd4hep,evaluator,acts,algorithms_init,beam,podio,TelescopeTracking,TelescopeMille',
      '-Pnthreads=1',f'-Pjana:nevents={limit or args.events}',f'-Pdd4hep:xml_files={geometry}',
      '-Pacts:MaterialMap=','-PTelescopeTracking:channelInput=true','-PTelescopeAudit:multipleEvents=true',
      '-PTelescopeMille:multipleEvents=true',f'-PTelescopeAudit:output={p}/audit.json',
      f'-PTelescopeMille:output={p}/mille.dat',f'-PTelescopeMille:report={p}/mille.json',
      f'-PTelescopeMille:config={REPO}/validation/telescope_alignment/l1_l2_global_y.json',
      f'-PTelescopeMille:derivativeGate={gate}/derivatives.json',f'-Ppodio:output_file={p}/reco.root',
      '-Ppodio:output_collections=EventHeader,TelescopeChannels,TelescopeHits,TelescopeHitAssociations,TelescopeMeasurements,TelescopeSeeds,TelescopeSeedParameters,TelescopeTrajectories,TelescopeTrackParameters,TelescopeTracks,TelescopeTrackLinks,TelescopeTrackAssociations']
    if cut is not None:command.append(f'-PTelescopeTracking:TelescopeCKF:Chi2CutOff={cut}')
    command.append(source)
    execute(command,p,env=env)
    assert digest(source)==before
    audit=json.loads((p/'audit.json').read_text())
    payload=channel_values(p/'reco.root');original=channel_values(source)[:limit or args.events]
    assert payload==original
    done(p,input_sha256=before,channel_payload_sha256=channel_digest(payload),processed=audit['processed'],
         accepted=audit['accepted'],rejected=audit['rejected'],measurement_selector_chi2_cut=cut or 15.)


def solve(args,reconstruction,name):
    require(args.result,reconstruction);p=stage(args.result,name)
    binary=args.result/reconstruction/'mille.dat'
    blocks=list(records(binary));assert len(blocks)==args.events and all(len(b)==10 for b in blocks)
    import numpy as np
    normal=np.zeros((2,2));rhs=np.zeros(2)
    for block in blocks:
        a,b,_=profile(block,LABELS);normal+=a;rhs+=b
    assert np.linalg.matrix_rank(normal)==2
    text=f'Cfiles\n{binary}\n\nentries 5\nmethod inversion 3 0.001\n\nParameter\n700102 0.0 1.0\n700202 0.0 1.0\n\nprintcounts\nend\n'
    (p/'pede.txt').write_text(text)
    execute([REPO/'external/install/bin/pede','pede.txt'],p,env=environment(args.build))
    status=(p/'millepede.end').read_text().strip()
    if status.split()[0] not in ('0','1'):raise ValueError('Pede failed: '+status)
    parameters=read_pede(p/'millepede.res')
    expected=np.linalg.solve(normal,rhs)
    assert np.allclose([parameters[k] for k in LABELS],expected,atol=6e-6)
    log=(p/'millepede.log').read_text();assert 'No rank defect of the symmetric matrix' in log
    covariance=np.linalg.inv(normal)
    write_json(p/'independent.json',{'parameters_mm':parameters,'schur_solution_mm':expected.tolist(),
      'nominal_sigma_mm':np.sqrt(np.diag(covariance)).tolist(),'rank':2,'condition':float(np.linalg.cond(normal)),
      'normal':normal.tolist(),'status':status,'records':len(blocks)})
    done(p,records=len(blocks),pede_status=status)


def correct(args):
    require(args.result,'solve');p=stage(args.result,'correction')
    parameters=read_pede(args.result/'solve/millepede.res')
    shifts={1:parameters[700102],2:parameters[700202]}
    # Correction reads nominal Geometry and solver output only, never Truth.
    nominal=args.result/'geometry/fixtures/nominal.xml'
    displaced_xml(nominal,p/'corrected.xml',shifts)
    write_json(p/'provenance.json',{'parent_sha256':digest(nominal),'pede_sha256':digest(args.result/'solve/millepede.res'),
      'physical_global_y_mm':shifts,'truth_used':False,'activated':False})
    q=stage(p,'geometry_audit')
    execute([args.build/'TelescopeChannels',p/'corrected.xml','0',q/'geometry.json'],q,env=environment(args.build))
    nominal_audit=json.loads((args.result/'data/control/channels_truth.json').read_text())['sensors']
    corrected=json.loads((q/'geometry.json').read_text())['sensors']
    for before,after in zip(nominal_audit,corrected):
        assert before['volume_id']==after['volume_id'] and before['geometry_id']==after['geometry_id']
        assert before['acts_rotation']==after['acts_rotation']
        delta=shifts.get(before['layer'],0.)
        assert max(abs(after['center_mm'][i]-before['center_mm'][i]-(delta if i==1 else 0.)) for i in range(3))<1e-9
    done(p,physical_global_y_mm=shifts)



def check(args):
    import numpy as np
    import ROOT
    from podio import reading
    for name in ('geometry','data','nominal','solve','correction','corrected','postsolve','control','controlsolve'):
        require(args.result,name)
    p=stage(args.result,args.validation_name)
    truth=json.loads((args.result/'data/shifted/channels_truth.json').read_text())
    nominal_geometry=json.loads((args.result/'data/control/channels_truth.json').read_text())
    for before,actual in zip(nominal_geometry['sensors'],truth['sensors']):
        assert before['volume_id']==actual['volume_id'] and before['geometry_id']==actual['geometry_id']
        expected=.150 if before['layer']==1 else (.200 if before['layer']==2 else 0.)
        assert abs(actual['center_mm'][1]-before['center_mm'][1]-expected)<1e-9
        assert before['acts_rotation']==actual['acts_rotation']
    solution=json.loads((args.result/'solve/independent.json').read_text())
    post=json.loads((args.result/'postsolve/independent.json').read_text())
    control_solution=json.loads((args.result/'controlsolve/independent.json').read_text())
    before=json.loads((args.result/'nominal/audit.json').read_text())
    after=json.loads((args.result/'corrected/audit.json').read_text())
    control=json.loads((args.result/'control/audit.json').read_text())
    input_values=channel_values(args.result/'data/shifted.root')
    assert digest(args.result/'data/shifted.root')==json.loads((args.result/'data/shifted_input.json').read_text())['file_sha256']
    assert channel_values(args.result/'nominal/reco.root')==channel_values(args.result/'corrected/reco.root')==input_values
    summaries={};residuals={}
    for name,audit in [('nominal',before),('corrected',after),('control',control)]:
        assert audit['processed']==audit['accepted']==args.events and audit['rejected']==0
        assert len({e['event_number'] for e in audit['events']})==args.events
        mille=json.loads((args.result/name/'mille.json').read_text())
        blocks=list(records(args.result/name/'mille.dat'))
        assert mille['records']==args.events and len(blocks)==args.events
        for event,rows in zip(mille['events'],blocks):
            assert event['accepted'] and event['records']==1 and event['scalar_measurements']==len(rows)==10
            assert {k for row in rows for k in row[3]}==set(LABELS)
            for e in event['equations']:
                assert e['cell_id']==audit['events'][event['event_number']]['measurement_details'][e['layer']]['cell_id']
                w=np.array(e['whitening']);cov=np.array(e['covariance'])
                assert np.allclose(w@cov@w.T,np.eye(2),atol=1e-10)
        chi2=np.array([e['chi2'] for e in audit['events']]);ndf=sum(e['stored_ndf'] for e in audit['events'])
        assert ndf==10*args.events
        residuals[name]={l:{'u':[],'v':[],'rec_minus_truth_global_y':[]} for l in range(5)}
        gid_to_layer={m['geometry_id']:i for i,m in enumerate(audit['events'][0]['measurement_details'])}
        for event in audit['events']:
            assert event['measurements']==5 and event['outliers']==0 and event['holes']==2
            for state in event['smoothed_states']:
                layer=gid_to_layer[state['geometry_id']]
                residuals[name][layer]['u'].append(state['residual_mm'][0])
                residuals[name][layer]['v'].append(state['residual_mm'][1])
            if name!='control':
                for layer,hit in enumerate(event['measurement_details']):
                    actual=truth['events'][event['event_number']]['channels'][layer]['physical_intersection_mm'][1]
                    residuals[name][layer]['rec_minus_truth_global_y'].append(hit['position_mm'][1]-actual)
        # Verify serialized event relations and a seed inferred from RecHits only.
        reader=reading.get_reader(str(args.result/name/'reco.root'))
        frames=list(reader.get('events'));assert len(frames)==args.events
        for i,frame in enumerate(frames):
            assert frame.get('EventHeader')[0].getEventNumber()==i
            hits=frame.get('TelescopeHits');tracks=frame.get('TelescopeTracks');seeds=frame.get('TelescopeSeeds')
            assert len(hits)==5 and len(tracks)==len(seeds)==1
            track=tracks[0];assert len(track.getMeasurements())==5 and track.getPdg()==11
            assert track.getTrajectory().getSeed()==seeds[0]
            points=np.array([[h.getPosition().x,h.getPosition().y,h.getPosition().z] for h in hits])
            direction=(points[-1]-points[0]);direction/=np.linalg.norm(direction)
            seed=seeds[0];params=seed.getParams();center=seed.getPerigee()
            expected=points[0]+(249.-points[0,0])/direction[0]*direction
            assert np.allclose([center.x,center.y,center.z],expected,atol=2e-6,rtol=0)
            assert abs(params.getPhi()-math.atan2(direction[1],direction[0]))<1e-6
            assert abs(params.getTheta()-math.acos(direction[2]))<1e-6
            assert len(frame.get('TelescopeHitAssociations'))==0
            for hit in hits:assert hit.getRawHit().isAvailable()
        summaries[name]={'processed':args.events,'accepted':args.events,'rejected':0,'mille_records':len(blocks),
          'acts_chi2_sum':float(chi2.sum()),'stored_ndf_sum':ndf,'acts_chi2_per_stored_ndf':float(chi2.sum()/ndf),
          'four_geometric_parameter_reference_ndf':6*args.events,'per_track_chi2':chi2.tolist(),
          'residuals_mm':{str(l):{axis:{'mean':float(np.mean(values)),'rms':float(np.std(values)),
            'values':values} for axis,values in components.items() if values} for l,components in residuals[name].items()}}
    assert summaries['corrected']['acts_chi2_sum']<summaries['nominal']['acts_chi2_sum']
    # Independently whitelist the XML differences, including cloned per-layer modules.
    def structure(node):return node.tag,dict(node.attrib),(node.text or '').strip(),tuple(structure(c) for c in node)
    nominal_xml=ET.parse(args.result/'geometry/fixtures/nominal.xml').getroot()
    for xml in [args.result/'geometry/truth.xml',args.result/'correction/corrected.xml']:
        candidate=ET.parse(xml).getroot();detector=candidate.find("./detectors/detector[@name='SiMAPS']")
        original=nominal_xml.find("./detectors/detector[@name='SiMAPS']")
        for layer in [1,2]:
            a=original.find(f"./layer[@id='{layer}']");b=detector.find(f"./layer[@id='{layer}']")
            module=detector.find(f"./module[@name='{b.get('module')}']")
            reference=original.find(f"./module[@name='{a.get('module')}']")
            normalized=copy.deepcopy(module);normalized.set('name',reference.get('name'))
            pos=normalized.find('./module_component/position');pos.attrib.clear();pos.attrib.update(reference.find('./module_component/position').attrib)
            assert structure(normalized)==structure(reference)
            detector.remove(module);b.set('module',a.get('module'))
        assert structure(candidate)==structure(nominal_xml)
    parameters=solution['parameters_mm'];post_parameters=post['parameters_mm']
    for a,b in zip(before['events'],after['events']):
        assert a['event_number']==b['event_number']
        for layer,(ha,hb) in enumerate(zip(a['measurement_details'],b['measurement_details'])):
            assert ha['cell_id']==hb['cell_id'] and ha['volume_id']==hb['volume_id'] and ha['geometry_id']==hb['geometry_id']
            assert np.allclose(ha['loc_mm'],hb['loc_mm'],atol=2e-6,rtol=0)
            assert np.allclose(ha['covariance_mm2'],hb['covariance_mm2'],atol=1e-12,rtol=0)
            delta=parameters[str(700002+100*layer)] if layer in (1,2) else 0.
            assert np.allclose(np.array(hb['position_mm'])-ha['position_mm'],[0,delta,0],atol=2e-6,rtol=0)
    control_values=channel_values(args.result/'data/control.root')
    for (_,shifted),(_,unshifted) in zip(input_values,control_values):
        for layer in [0,3,4]:assert shifted[layer]==unshifted[layer]
        for layer in [1,2]:assert shifted[layer][0]!=unshifted[layer][0]
    # Worst-case deterministic quantization bound, separately from nominal sigma.
    blocks=list(records(args.result/'nominal/mille.dat'))
    total=sum((profile(block,LABELS)[0] for block in blocks),np.zeros((2,2)))
    quantization_bound=np.zeros(2)
    for block in blocks:
        local=np.array([[row[2].get(k,0.) for k in range(1,5)] for row in block])
        global_=np.array([[row[3].get(k,0.) for k in LABELS] for row in block])
        basis,_=np.linalg.qr(local);projector=np.eye(10)-basis@basis.T
        response=np.linalg.solve(total,global_.T@projector)
        quantization_bound+=np.sqrt(3.)*np.abs(response).sum(axis=1)
    assert all(abs(parameters[str(k)]-value)<bound for k,value,bound in zip(LABELS,[.150,.200],quantization_bound))
    # Predeclared engineering tolerance: five nominal errors from unchanged pitch.
    # This deterministic sample does not establish frequentist uncertainty coverage.
    tolerances=[5*sigma for sigma in solution['nominal_sigma_mm']]
    for i,(label,injected) in enumerate(zip(LABELS,[.150,.200])):
        assert abs(parameters[str(label)]-injected)<tolerances[i]
        assert abs(control_solution['parameters_mm'][str(label)])<5*control_solution['nominal_sigma_mm'][i]
        assert abs(post_parameters[str(label)])<2e-5
    # Independent absolute-coordinate GLS oracle, using reconstructed measurements
    # and reconstruction Geometry only; never used to produce the correction.
    absolute_solutions={}
    for name in ['nominal','corrected','control']:
        native=json.loads((args.result/name/'mille.json').read_text())
        normal=np.zeros((2,2));rhs=np.zeros(2)
        for event in native['events']:
            local=[];global_=[];measurement=[]
            for e in event['equations']:
                x,y,z=e['center_mm'];dx=x-250.
                design=np.array([[1.,0.,dx,0.],[0.,1.,0.,dx]])
                covariance=np.array(e['covariance']);w=np.linalg.inv(np.linalg.cholesky(covariance))
                vector=np.array(e['measurement']).ravel()-[y,z]
                g=np.zeros((2,2))
                if e['layer'] in [1,2]:g[0,e['layer']-1]=1.
                local.extend(w@design);global_.extend(w@g);measurement.extend(w@vector)
            local=np.array(local);global_=np.array(global_);measurement=np.array(measurement)
            basis,_=np.linalg.qr(local);projector=np.eye(10)-basis@basis.T
            normal+=global_.T@projector@global_;rhs+=global_.T@projector@measurement
        inferred=np.linalg.solve(normal,rhs)
        solver=json.loads((args.result/{'nominal':'solve','corrected':'postsolve','control':'controlsolve'}[name]/'independent.json').read_text())
        assert np.allclose(inferred,solver['schur_solution_mm'],atol=1e-8,rtol=0)
        assert np.allclose(normal,solver['normal'],atol=1e-5,rtol=1e-9)
        absolute_solutions[name]=inferred.tolist()
    warnings={}
    for name in ['solve','postsolve','controlsolve']:
        log=(args.result/name/'stdout.log').read_text();iteration_rejects=[]
        for line in log.splitlines():
            parts=line.split()
            if len(parts)>=7 and parts[0].isdigit() and parts[1].isdigit() and parts[-1] in ('FMS','FM','F','MS') and parts[-2].isdigit():
                iteration_rejects.append(int(parts[-3]))
        assert iteration_rejects and max(iteration_rejects)==0
        warnings[name]={'end_status':(args.result/name/'millepede.end').read_text().strip(),
          'rank':2,'rejected_local_fits_by_iteration':iteration_rejects,
          'error_rescaling_recommended':'multiply all input standard deviations' in log,'error_rescaling_applied':False}
    # ROOT-only diagnostic distributions, stored for TBrowser inspection.
    ROOT.gROOT.SetBatch(True);root=ROOT.TFile.Open(str(p/'closure.root'),'NEW')
    canvases=[]
    for layer in range(5):
        canvas=ROOT.TCanvas(f'L{layer}_residuals',f'SiMAPS L{layer} residuals',1200,400);canvas.Divide(3,1)
        for panel,axis in enumerate(('u','v','rec_minus_truth_global_y'),1):
            canvas.cd(panel)
            for k,name in enumerate(('nominal','corrected')):
                hist=ROOT.TH1D(f'L{layer}_{axis}_{name}',f'L{layer} {axis};Residual [mm];Entries',120,-.3,.3)
                for value in residuals[name][layer][axis]:hist.Fill(value)
                hist.SetLineColor(ROOT.kRed if k==0 else ROOT.kBlue);hist.Draw('HIST' if k==0 else 'HIST SAME');hist.Write()
        canvas.Write();canvases.append(canvas)
    for name,summary in summaries.items():
        hist=ROOT.TH1D(name+'_acts_chi2_stored_ndf',name+';ACTS chi2 / stored NDF;Tracks',100,0.,max(2.,max(summary['per_track_chi2'])/10.*1.05))
        for value in summary['per_track_chi2']:hist.Fill(value/10.)
        hist.Write()
    geometry_canvas=ROOT.TCanvas('sensor_centers','Physical sensor centers',800,500)
    truth_sensors=truth['sensors'];nominal_sensors=nominal_geometry['sensors']
    corrected_sensors=json.loads((args.result/'correction/geometry_audit/geometry.json').read_text())['sensors']
    graphs=[];legend=ROOT.TLegend(.68,.72,.90,.90)
    all_y=[s['center_mm'][1] for group in [nominal_sensors,truth_sensors,corrected_sensors] for s in group]
    for index,(name,sensors,color) in enumerate([('Nominal',nominal_sensors,ROOT.kBlack),('Truth',truth_sensors,ROOT.kRed),('Corrected',corrected_sensors,ROOT.kBlue)]):
        graph=ROOT.TGraph(len(sensors));graph.SetName(name+'_global_y_centers')
        graph.SetTitle('Sensor placements;Layer;Global Y center [mm]');graph.SetLineColor(color);graph.SetMarkerColor(color);graph.SetMarkerStyle(20+index)
        for i,sensor in enumerate(sensors):graph.SetPoint(i,sensor['layer'],sensor['center_mm'][1])
        graph.SetMinimum(min(all_y)-.02);graph.SetMaximum(max(all_y)+.02)
        graph.Draw('ALP' if index==0 else 'LP SAME');graph.Write();legend.AddEntry(graph,name,'lp');graphs.append(graph)
    legend.Draw();geometry_canvas.Write();root.Close()
    result={'passed':True,'events':args.events,'input_channel_sha256':channel_digest(input_values),
      'immutable_input_file_sha256':digest(args.result/'data/shifted.root'),'injected_global_y_mm':[.150,.200],
      'recovered_global_y_mm':[parameters[str(k)] for k in LABELS],
      'remaining_geometry_bias_mm':[parameters[str(k)]-v for k,v in zip(LABELS,[.150,.200])],
      'nominal_sigma_mm':solution['nominal_sigma_mm'],'closure_tolerance_mm':tolerances,'deterministic_quantization_bound_mm':quantization_bound.tolist(),
      'post_correction_mm':[post_parameters[str(k)] for k in LABELS],
      'control_correction_mm':[control_solution['parameters_mm'][str(k)] for k in LABELS],
      'summaries':summaries,'pede_diagnostics':warnings,
      'absolute_coordinate_data_only_schur_mm':absolute_solutions,
      'tracks_with_lower_chi2':sum(b['chi2']<a['chi2'] for a,b in zip(before['events'],after['events'])),'truth_used_for_inference':False,'geometry_activated':False,
      'scope':'quantized-channel synthetic, zero field, material-free; actual JANA CKF and second reconstruction'}
    write_json(p/'report.json',result);done(p,passed=True)



def regressions(args):
    """Rebuild preserved standalone sources and exercise the same current plugin in benchmark mode."""
    p=stage(args.result,args.validation_name+'_regressions');env=environment(args.build)
    def command(name,argv,cwd=None,selected_env=None):
        q=stage(p,name);execute(argv,q,cwd=cwd,env=selected_env or env);return q
    builds={}
    for name,source in [('geometry','telescope_geometry'),('benchmark','telescope_one_track')]:
        build=args.build.parent/(args.build.name+'_'+p.name+'_'+name)
        if build.exists():raise ValueError('Regression build must be new: '+str(build))
        command(name+'_configure',['cmake','-S',REPO/'validation'/source,'-B',build,'-DCMAKE_BUILD_TYPE=Release'])
        command(name+'_build',['cmake','--build',build,'-j2'])
        builds[name]=build
    geometry=args.result/'geometry/fixtures/nominal.xml'
    command('geometry_probe',[builds['geometry']/'TelescopeGeometryProbe',geometry,p/'geometry.json','official','none','nominal'],selected_env=environment(builds['geometry']))
    command('geometry_check',[sys.executable,REPO/'validation/telescope_geometry/check.py','--report',p/'geometry.json','--fixture',geometry,'--integration'])
    command('standalone',[builds['benchmark']/'TelescopeOneTrack',geometry,p/'reference.json'],selected_env=environment(builds['benchmark']))
    command('fixture_input',[sys.executable,REPO/'validation/telescope_factories/prepare.py','--output',p/'input.root'])
    q=stage(p,'one_event')
    previous=json.loads((args.result/'nominal/command.json').read_text())['argv']
    argv=[]
    for argument in previous[:-1]:
        if argument.startswith(('-PTelescopeTracking:channelInput=', '-PTelescopeAudit:multipleEvents=',
          '-PTelescopeMille:multipleEvents=','-PTelescopeTracking:TelescopeCKF:Chi2CutOff=')):continue
        if argument.startswith('-Pjana:nevents='):argument='-Pjana:nevents=1'
        for key,filename in [('TelescopeAudit:output','audit.json'),('TelescopeMille:output','mille.dat'),
          ('TelescopeMille:report','mille.json'),('podio:output_file','reco.root')]:
            if argument.startswith('-P'+key+'='):argument=f'-P{key}={q}/{filename}'
        if argument.startswith('-Ppodio:output_collections='):argument=argument.replace(',TelescopeChannels','')
        argv.append(argument)
    argv.append(str(p/'input.root'));execute(argv,q,env=env)
    command('one_event_check',[sys.executable,REPO/'validation/telescope_factories/check.py','--audit',q/'audit.json',
      '--root',q/'reco.root','--reference',p/'reference.json','--output',p/'one_event_comparison.json'])
    command('legacy_writer',[args.build/'LegacyTelescopeCrosscheck',q/'mille.json',p/'legacy.dat'])
    gate=args.result/'nominal/gate/derivatives.json'
    command('native_legacy_check',[sys.executable,REPO/'validation/telescope_alignment/check.py','--native',q/'mille.dat',
      '--report',q/'mille.json','--legacy',p/'legacy.dat','--gate',gate,'--output',p/'native_legacy.json'])
    command('mathematical_generate',[args.build/'TelescopeMilleFixture',geometry,q/'mille.json',p/'mathematical_fixture'])
    command('mathematical_pede',[REPO/'external/install/bin/pede','pede.txt'],cwd=p/'mathematical_fixture')
    command('mathematical_check',[sys.executable,REPO/'validation/telescope_alignment/check.py','--native',q/'mille.dat',
      '--report',q/'mille.json','--legacy',p/'legacy.dat','--gate',gate,'--fixture',p/'mathematical_fixture','--output',p/'mathematical_comparison.json'])
    command('unit_tests',[sys.executable,'-m','unittest','discover','-s','validation','-p','test_*.py'],cwd=REPO)
    command('safety',[sys.executable,REPO/'validation/check_safety.py'])
    command('preservation',[sys.executable,REPO/'validation/verify_preservation.py'])
    done(p,passed=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result',type=Path,required=True)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--validation-name',default='validation',help='New validation/regression output stage name; existing reports remain immutable')
    parser.add_argument('--events',type=int,default=32)
    parser.add_argument('--chi2-cut',type=float,default=None,help='Explicit alignment capture window; same setting in all closure passes')
    parser.add_argument('--step',choices=['geometry','data','pilot','nominal','solve','correct','corrected','postsolve','control','controlsolve','check','regressions','all'],required=True)
    args=parser.parse_args();args.result=args.result.resolve();args.build=args.build.resolve()
    if not args.validation_name.isidentifier():parser.error('Validation stage name must be an identifier')
    if not args.result.is_relative_to(REPO/'result') or not 16<=args.events<=64:parser.error('Use result/ and 16..64 deterministic events')
    args.result.mkdir(parents=True,exist_ok=True)
    os.chdir(REPO)
    steps=['geometry','data','nominal','solve','correct','corrected','postsolve','control','controlsolve','check'] if args.step=='all' else [args.step]
    for step in steps:
        if step=='geometry':geometry_step(args)
        elif step=='data':data_step(args)
        elif step=='pilot':reconstruct(args,'pilot',args.result/'geometry/fixtures/nominal.xml','shifted',4,args.chi2_cut)
        elif step=='nominal':reconstruct(args,'nominal',args.result/'geometry/fixtures/nominal.xml','shifted',cut=args.chi2_cut)
        elif step=='solve':solve(args,'nominal','solve')
        elif step=='correct':correct(args)
        elif step=='corrected':
            require(args.result,'correction');reconstruct(args,'corrected',args.result/'correction/corrected.xml','shifted',cut=args.chi2_cut)
        elif step=='postsolve':solve(args,'corrected','postsolve')
        elif step=='control':reconstruct(args,'control',args.result/'geometry/fixtures/nominal.xml','control',cut=args.chi2_cut)
        elif step=='controlsolve':solve(args,'control','controlsolve')
        elif step=='check':check(args)
        elif step=='regressions':regressions(args)
        print('Completed:',step,args.result)

if __name__=='__main__':main()

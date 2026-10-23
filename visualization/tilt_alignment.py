"""ROOT-only diagnostics of inactive tilt candidates and physical plane orientations."""
import argparse,json,math
from pathlib import Path
from array import array
import numpy as np
import uproot,awkward as ak
from geometry.placements import placement_transforms
from validation.rz_statistics import track_metrics
from visualization.z_alignment import pede_metrics,local_residuals
from research_common import write_json,digest,require
from geometry.transforms import rotation_log,multiply,transpose,orientation_distance
from correction.scope import SO3_MODES


def matched_residuals(reco,simulation,normal,layer=1,accepted_only=False):
    with uproot.open(reco) as f,uproot.open(simulation) as s:
        t,st=f['events'],s['events']
        get=lambda tree,coll,key:ak.to_list(tree[f'{coll}/{coll}.{key}'].array())
        for key in ('runNumber','eventNumber'):
            if get(t,'EventHeader',key)!=get(st,'EventHeader',key):raise ValueError('Event identity mismatch')
        accepted=ak.to_list(ak.num(t['LocalBeamTestTracks/LocalBeamTestTracks.chi2'].array())) if accepted_only else None
        si,ri=get(st,'SiMAPSHits','cellID'),get(t,'LocalSiMAPSRecHits','cellID')
        sx=[get(st,'SiMAPSHits','position.'+a) for a in 'xyz'];rx=[get(t,'LocalSiMAPSRecHits','position.'+a) for a in 'xyz']
    result={key:[] for key in ('x','y','z','normal')}
    for event in range(len(si)):
        if accepted is not None and not accepted[event]:continue
        a=[i for i,c in enumerate(si[event]) if c>>11&63==layer];b=[i for i,c in enumerate(ri[event]) if c>>11&63==layer]
        if len(a)!=1 or len(b)!=1:continue
        delta=np.array([rx[k][event][b[0]]-sx[k][event][a[0]] for k in range(3)])
        for k,axis in enumerate('xyz'):result[axis].append(float(delta[k]))
        result['normal'].append(float(np.dot(normal,delta)))
    return result


def render(a):
    import ROOT
    ROOT.gROOT.SetBatch(True);a.output.mkdir(parents=True,exist_ok=False)
    manual=getattr(a,'manual_run',None)
    if manual is not None:
        if a.survey is None or any(v is not None for v in (a.report,a.controller,a.candidate,a.final_reconstruction)):
            raise ValueError('Manual comparison requires --manual-run and --survey, without Controller arguments')
        for name in ('step3','step4','step5','step6'):require(manual,name)
        final=manual/'step5/corrected.xml';after=manual/'step6'
        correction=json.loads((manual/'step5/complete.json').read_text())
        if correction.get('mode') not in SO3_MODES:raise ValueError('Manual comparison requires an explicit coupled SO(3) mode')
        if correction['base_geometry_sha256']!=digest(a.survey):raise ValueError('Survey differs from the actual correction base')
        before_metadata=json.loads((manual/'step3/complete.json').read_text())
        metrics=track_metrics(manual/'step3/reco.root')
        report={'initial_geometry':'geo-'+digest(a.survey),'candidate_geometry':'geo-'+digest(final),
            'raw_sha256':before_metadata['raw_input_sha256'],
            'iterations':[dict(correction,iteration=1,run=str(manual),track_chi2_ratio=metrics['chi2_over_stored_ndf'])]}
    elif a.report is not None:
        if a.candidate is None or a.final_reconstruction is None:raise ValueError('Explicit plotting requires --report, --candidate and --final-reconstruction together')
        report=json.loads(a.report.read_text());final=a.candidate;after=a.final_reconstruction
    else:
        if a.controller is None:raise ValueError('Use explicit maintained outputs or the optional archived study-bundle shorthand')
        success=json.loads((a.controller/'success.json').read_text());report=json.loads(Path(success['report']).read_text());final=Path(success['candidate']);after=a.controller/'final/step3'
    before=Path(report['iterations'][0]['run'])/'step3'
    first_correction=json.loads((Path(report['iterations'][0]['run'])/'step5/complete.json').read_text())
    coupled=first_correction.get('mode') in SO3_MODES
    for path,geometry_hash in ((before,report['initial_geometry'][4:]),(after,digest(final))):
        metadata=json.loads((path/'complete.json').read_text())
        if metadata['geometry_sha256']!=geometry_hash or metadata['raw_input_sha256']!=report['raw_sha256']:raise ValueError('Plot inputs differ from the Controller Geometry or fixed RawHits')
    if 'geo-'+digest(final)!=report['candidate_geometry']:raise ValueError('Candidate differs from the reported final Geometry')
    geofiles=[a.survey if manual is not None else final.parent.parent/report['initial_geometry']/'geometry.xml',a.case/'step1/misaligned.xml',final]
    primary_layer=min(int(key.split('_')[0][1:]) for key in report['iterations'][0]['delta_rad_by_component'])
    transforms=[placement_transforms(path) for path in geofiles];normal=np.array(transforms[1][primary_layer].rotation)[:,2]
    simulation=a.case/'step2/events.edm4hep.root'
    if digest(a.case/'step2_digitization/rawhits.edm4eic.root')!=report['raw_sha256']:raise ValueError('Simulation case does not match the Controller RawHit input')
    rb,ra=[matched_residuals(p/'reco.root',simulation,normal,primary_layer) for p in (before,after)]
    file=ROOT.TFile(str(a.output/'tilt_alignment.root'),'CREATE');keep=[]
    summary={'before':track_metrics(before/'reco.root'),'after':track_metrics(after/'reco.root'),'iterations':[],
        'before_reconstruction':str(before),'after_reconstruction':str(after),'geometry_sha256':digest(final),'raw_sha256':report['raw_sha256'],'activation':'inactive candidate','hit_residuals':{}}
    def overlay(name,title,left,right):
        values=np.r_[left,right];pad=max(float(np.ptp(values))*.1,1e-8)
        canvas=ROOT.TCanvas('c_'+name,title,900,650);histograms=[]
        for data,color,label in ((left,ROOT.kRed,'before'),(right,ROOT.kBlue,'after')):
            h=ROOT.TH1D(name+'_'+label,title,60,float(np.min(values)-pad),float(np.max(values)+pad))
            for value in data:h.Fill(float(value))
            h.SetLineColor(color);h.SetLineWidth(2);h.Write();histograms.append(h)
        histograms[0].SetMaximum(1.15*max(h.GetMaximum() for h in histograms));histograms[0].Draw('HIST');histograms[1].Draw('HIST SAME')
        legend=ROOT.TLegend(.7,.76,.89,.89)
        for h,label in zip(histograms,('Before','After')):legend.AddEntry(h,label,'l')
        legend.Draw();canvas.Write();canvas.SaveAs(str(a.output/(name+'.pdf')));keep.extend([canvas,legend,*histograms])
    for axis in rb:
        overlay(f'L{primary_layer}_hit_'+axis,f'L{primary_layer} Hit Residual;RecHit - SimHit: {axis} [mm];Unique event/layer pairs',rb[axis],ra[axis])
        summary['hit_residuals'][axis]={label:{'pairs':len(v),'mean_mm':float(np.mean(v)),'rms_about_zero_mm':float(np.sqrt(np.mean(np.square(v))))} for label,v in (('before',rb[axis]),('after',ra[axis]))}
    lb,la=[local_residuals(p/'mille.dat') for p in (before,after)]
    for axis in ('x','y'):overlay(f'L{primary_layer}_whitened_'+axis,f'L{primary_layer} profiled track residual, whitened component {axis};Whitened measurement - prediction [dimensionless];Accepted tracks',lb[primary_layer][axis],la[primary_layer][axis])
    ratios=[]
    for p in (before,after):
        with uproot.open(p/'reco.root') as f:
            t=f['events'];ratios.append(np.asarray(ak.flatten(t['LocalBeamTestTracks/LocalBeamTestTracks.chi2'].array()/t['LocalBeamTestTracks/LocalBeamTestTracks.ndf'].array())))
    overlay('acts_chi2','ACTS quality;Track chi2 / stored-NDF;Accepted tracks',*ratios)
    for item in report['iterations']:
        run=Path(item['run']);summary['iterations'].append({'iteration':item['iteration'],'pede':pede_metrics(run/'step4'),
          'correction':json.loads((run/'step5/complete.json').read_text()),'acts':track_metrics(run/'step3/reco.root'),
          'observability':json.loads((run/'tilt_observability.json').read_text())['selected']})
    def graph(name,title,x,y):
        g=ROOT.TGraph(len(x),array('d',x),array('d',y));g.SetName(name);g.SetTitle(title);g.SetMarkerStyle(20)
        c=ROOT.TCanvas('c_'+name,title,900,650);g.Draw('APL');g.Write();c.Write();c.SaveAs(str(a.output/(name+'.pdf')));keep.extend([g,c])
    axis=next(iter(report['iterations'][0]['delta_rad_by_component'])).split('_')[1]
    component=lambda t: rotation_log(multiply(t.rotation,transpose(transforms[0][primary_layer].rotation)))['xyz'.index(axis[-1])] if coupled else (math.atan2(t.rotation[2][1],t.rotation[2][2]) if axis=='rx' else math.atan2(t.rotation[0][2],t.rotation[0][0]))
    graph(axis+'_correction',f'L{primary_layer} cumulative '+axis+' correction;Iteration;'+('Global relative rotation vector' if coupled else 'Global '+axis)+' [mrad]',[0]+[i['iteration'] for i in report['iterations']],
          [1000*component(transforms[0][primary_layer])]+[1000*i['applied_rad_by_component'][f'L{primary_layer}_'+axis] for i in report['iterations']])
    graph('acts_history','ACTS quality;Geometry iteration;ACTS chi2 / stored-NDF',list(range(len(report['iterations'])+1)),
          [i['track_chi2_ratio'] for i in report['iterations']]+[summary['after']['chi2_over_stored_ndf']])
    graph('pede_history','Pede quality;Iteration;Pede chi2 / NDF',[i['iteration'] for i in summary['iterations']],[i['pede']['chi2_ndf'] for i in summary['iterations']])
    selected_layers=sorted({int(key.split('_')[0][1:]) for key in report['iterations'][0]['delta_rad_by_component']})
    if len(report['iterations'][0]['delta_rad_by_component'])>1:
        for key in report['iterations'][0]['delta_rad_by_component']:
            if key==f'L{primary_layer}_'+axis:continue
            graph(key+'_diagnostic',('Global relative rotation vector ' if coupled else 'Archived experimental ')+key+';Iteration;'+('Log(Rcurrent Rsurvey^{T}) component' if coupled else 'Ordered-XYZ diagnostic')+' [mrad]',
                  [0]+[i['iteration'] for i in report['iterations']],
                  [0.]+[1000*i['applied_rad_by_component'][key] for i in report['iterations']])
        for layer in ([] if coupled else selected_layers):
            graph(f'L{layer}_unfitted_rz_drift',f'Archived experimental L{layer}: unfitted Rz drift;Iteration;Ordered-XYZ Rz diagnostic [mrad]',
                  [0]+[i['iteration'] for i in report['iterations']],
                  [0.]+[1000*i['correction']['diagnostic_ordered_xyz_rad'][str(layer)]['rz'] for i in summary['iterations']])
        summary['scientific_status']='Controlled coupled SO(3) diagnostic; uncertainty coverage requires separate statistical validation' if coupled else 'Combined Rx/Ry unsupported after failed noiseless finite-rotation closure; these plots retain the experiment'
    if coupled:
        summary['orientation_validation']={}
        summary['hit_residuals_by_layer']={}
        summary['accepted_hit_residuals_by_layer']={}
        summary['residual_selection']='All unique event/layer pairs are retained; separate accepted-track diagnostics select only reconstructed events, never Truth-based cuts'
        for layer in selected_layers:
            summary['orientation_validation'][str(layer)]={
                'before_error_rad':orientation_distance(transforms[1][layer].rotation,transforms[0][layer].rotation),
                'final_error_rad':orientation_distance(transforms[1][layer].rotation,transforms[2][layer].rotation),
                'truth_matrix':transforms[1][layer].rotation,'final_matrix':transforms[2][layer].rotation,
                'center_error_mm':float(np.linalg.norm(np.array(transforms[2][layer].translation)-transforms[1][layer].translation))}
            matrices=[placement_transforms(Path(i['run'])/'step5/corrected.xml')[layer].rotation for i in report['iterations']]
            graph(f'L{layer}_orientation_error',f'L{layer} orientation validation;Iteration;Relative SO(3) angle [mrad]',
                [0]+[i['iteration'] for i in report['iterations']],
                [1000*orientation_distance(transforms[1][layer].rotation,r) for r in [transforms[0][layer].rotation,*matrices]])
            normal=np.array(transforms[1][layer].rotation)[:,2]
            pair=[matched_residuals(p/'reco.root',simulation,normal,layer) for p in (before,after)]
            summary['hit_residuals_by_layer'][str(layer)]={}
            for key in pair[0]:
                summary['hit_residuals_by_layer'][str(layer)][key]={label:{'pairs':len(v[key]),'mean_mm':float(np.mean(v[key])),'rms_about_zero_mm':float(np.sqrt(np.mean(np.square(v[key]))))} for label,v in zip(('before','after'),pair)}
                if layer!=primary_layer:overlay(f'L{layer}_hit_{key}',f'L{layer} Hit Residual;RecHit - SimHit: {key} [mm];Unique event/layer pairs',pair[0][key],pair[1][key])
            accepted_pair=[matched_residuals(p/'reco.root',simulation,normal,layer,accepted_only=True) for p in (before,after)]
            summary['accepted_hit_residuals_by_layer'][str(layer)]={}
            for key in accepted_pair[0]:
                summary['accepted_hit_residuals_by_layer'][str(layer)][key]={label:{'pairs':len(v[key]),'mean_mm':float(np.mean(v[key])),'rms_about_zero_mm':float(np.sqrt(np.mean(np.square(v[key]))))} for label,v in zip(('before','after'),accepted_pair)}
                overlay(f'L{layer}_accepted_hit_{key}',f'L{layer} accepted-track Hit Residual;RecHit - SimHit: {key} [mm];Accepted event/layer pairs',accepted_pair[0][key],accepted_pair[1][key])

        for key in report['iterations'][0].get('delta_mm_by_component',{}):
            graph(key+'_translation',key+' Geometry Correction;Iteration;Global center [mm]',
                [0]+[i['iteration'] for i in report['iterations']],
                [transforms[0][int(key[1])].translation['xyz'.index(key[-1])]]+[i['applied_mm_by_component'][key] for i in report['iterations']])
    canvas=ROOT.TCanvas('c_geometry','Detector Geometry: plane corners and normals',1500,600);canvas.Divide(3,1)
    for pad,(placements,title) in enumerate(zip(transforms,('Survey G0','Simulation Truth (validation only)','Inactive final candidate')),1):
        canvas.cd(pad);frame=ROOT.TH3D('frame_'+str(pad),title+';Global X [mm];Global Y [mm];Global Z [mm]',1,-55,55,1,-55,55,1,-5,310);frame.SetStats(False);frame.Draw();keep.append(frame)
        for layer in range(7):
            t=placements[layer];poly=ROOT.TPolyLine3D(5)
            for index,p in enumerate(((-50,-50,0),(50,-50,0),(50,50,0),(-50,50,0),(-50,-50,0))):poly.SetPoint(index,*t.apply(p))
            poly.SetLineColor(ROOT.kRed if layer in selected_layers else ROOT.kGray+2);poly.SetLineWidth(2);poly.Draw();poly.Write('plane_'+str(pad)+'_'+str(layer));keep.append(poly)
            if layer in selected_layers:
                line=ROOT.TPolyLine3D(2);line.SetPoint(0,*t.translation);line.SetPoint(1,*t.apply((0,0,20)));line.SetLineColor(ROOT.kBlue);line.SetLineWidth(3);line.Draw();keep.append(line)
    canvas.Write();canvas.SaveAs(str(a.output/'geometry.pdf'));keep.append(canvas);file.Close()
    summary['injected_'+axis+'_rad']=component(transforms[1][primary_layer]);summary['final_'+axis+'_rad']=component(transforms[2][primary_layer])
    write_json(a.output/'summary.json',summary)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('case','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--manual-run',type=Path,help='Independent completed step3/4/5/6 run; requires tilt_observability.json and --survey')
    parser.add_argument('--survey',type=Path,help='Exact initial reconstruction Geometry for --manual-run')
    parser.add_argument('--controller',type=Path,help='Optional archived study bundle containing success.json; explicit maintained outputs need no bundle')
    parser.add_argument('--report',type=Path,help='Maintained Controller calibration_report.json')
    parser.add_argument('--candidate',type=Path,help='Exact inactive Geometry XML named by the report')
    parser.add_argument('--final-reconstruction',type=Path,help='Directory containing reco.root, mille.dat and complete.json for the exact final candidate')
    render(parser.parse_args())

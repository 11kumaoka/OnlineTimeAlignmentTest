"""ROOT validation of inactive Z candidates; Simulation Truth is read only here."""
import argparse,json,re
from pathlib import Path
import numpy as np
import awkward as ak
import uproot
from research_common import write_json,digest
from geometry.placements import placement_transforms
from validation.z_observability import measurements as mille_measurements
from validation.rz_statistics import track_metrics
from validation.metrics import measurements as hit_metrics



def pede_metrics(directory):
    complete=json.loads((directory/'complete.json').read_text());log=(directory/'millepede.log').read_text()
    match=re.search(r'Sum\(Chi\^2\)/Sum\(Ndf\)\s*=\s*([\d.Ee+\-]+)\s*/\s*\(\s*(\d+)\s*-\s*(\d+)\s*\)\s*=\s*([\d.Ee+\-]+)',log)
    if not match:raise ValueError('Missing Pede chi2 diagnostic')
    rows=[]
    for line in log.splitlines():
        m=re.match(r'^\s*(\d+)\s+(\d+)\s+.*?\s+(\d+)\s+\d{5,6}\s+([FMS ]*)$',line)
        if m:rows.append({'iteration':int(m[1]),'rejected_local_fits':int(m[3]),'flags':m[4].strip()})
    if not rows:raise ValueError('Missing Pede rejection diagnostics')
    return {'status':complete['status'],'process_exit':json.loads((directory/'exit.json').read_text()),
            'chi2':float(match[1]),'ndf':int(match[2])-int(match[3]),'chi2_ndf':float(match[4]),
            'nominal_sigma_by_label':complete.get('nominal_sigma_by_label',complete.get('tilt_sigma_rad',complete.get('rotation_sigma_rad',{}))),'parameters':complete['parameters_by_label'],
            'rejection_history':rows,'stdout_warning_lines':[v.strip() for v in (directory/'stdout.log').read_text().splitlines() if re.search('warn|should be|reject',v,re.I)]}


def z_residuals(reco,simulation):
    with uproot.open(reco) as f,uproot.open(simulation) as s:
        t,st=f['events'],s['events']
        for key in ('runNumber','eventNumber'):
            branch=f'EventHeader/EventHeader.{key}'
            assert ak.to_list(t[branch].array())==ak.to_list(st[branch].array())
        get=lambda tree,collection,key:ak.to_list(tree[f'{collection}/{collection}.{key}'].array())
        si,ri=get(st,'SiMAPSHits','cellID'),get(t,'LocalSiMAPSRecHits','cellID')
        sz,rz=get(st,'SiMAPSHits','position.z'),get(t,'LocalSiMAPSRecHits','position.z')
    result={l:[] for l in (1,2)}
    for event in range(len(si)):
        for layer in result:
            a=[z for c,z in zip(si[event],sz[event]) if c>>11&63==layer]
            b=[z for c,z in zip(ri[event],rz[event]) if c>>11&63==layer]
            if len(a)==len(b)==1:result[layer].append(b[0]-a[0])
    return result


def local_residuals(mille):
    residuals={l:{'x':[],'y':[]} for l in (1,2)}
    for rows in mille_measurements(mille):
        a=np.array([[r[2].get(k,0.) for k in range(1,5)] for r in rows]);m=np.array([r[0] for r in rows]);sigma=np.array([r[1] for r in rows])
        p=np.linalg.lstsq(a/sigma[:,None],m/sigma,rcond=None)[0];residual=m-a@p
        for layer in (1,2):
            for index,axis in enumerate(('x','y')):residuals[layer][axis].append(float(residual[2*layer+index]))
    return residuals


def render(output,before,after,simulation,report,geometry):
    import ROOT
    from array import array
    ROOT.gROOT.SetBatch(True);output.mkdir(parents=True,exist_ok=False)
    zb,za=z_residuals(before/'reco.root',simulation),z_residuals(after/'reco.root',simulation)
    rb,ra=local_residuals(before/'mille.dat'),local_residuals(after/'mille.dat')
    hb,ha=hit_metrics(before/'reco.root',simulation),hit_metrics(after/'reco.root',simulation)
    file=ROOT.TFile(str(output/'z_alignment.root'),'CREATE');keep=[];summary={'before':track_metrics(before/'reco.root'),'after':track_metrics(after/'reco.root'),'iterations':[],'layers':{}}
    def overlays(name,title,a,b):
        a=np.array(a);b=np.array(b);allvalues=np.r_[a,b];low,high=allvalues.min(),allvalues.max();pad=max((high-low)*.1,1e-6)
        canvas=ROOT.TCanvas('canvas_'+name,title,900,650);h=[]
        for values,color,label in [(a,ROOT.kRed,'before'),(b,ROOT.kBlue,'after')]:
            hist=ROOT.TH1D(name+'_'+label,title,70,low-pad,high+pad)
            for value in values:hist.Fill(float(value))
            hist.SetLineColor(color);hist.SetLineWidth(2);hist.Write();h.append(hist)
        h[0].SetMaximum(1.15*max(v.GetMaximum() for v in h));h[0].Draw('HIST');h[1].Draw('HIST SAME')
        legend=ROOT.TLegend(.7,.75,.89,.88)
        for hist,label in zip(h,('Before','After')):legend.AddEntry(hist,label,'l')
        legend.Draw();canvas.Write();canvas.SaveAs(str(output/(name+'.pdf')));keep.extend([canvas,legend,*h])
    for layer in (1,2):
        summary['layers'][str(layer)]={'matched_rec_minus_sim_z_mm':{'before_mean':float(np.mean(zb[layer])),'after_mean':float(np.mean(za[layer])),'pairs':len(zb[layer])},'local_fit_residual_rms_mm':{}}
        overlays(f'L{layer}_hit_z',f'L{layer} Hit Residual;RecHit Z - SimHit Z [mm];Unique event/layer pairs',zb[layer],za[layer])
        for axis in ('x','y'):
            overlays(f'L{layer}_track_{axis}',f'L{layer} track residual;RecHit - profiled straight-line prediction [mm];Accepted tracks',rb[layer][axis],ra[layer][axis])
            summary['layers'][str(layer)]['local_fit_residual_rms_mm'][axis]={'before':float(np.sqrt(np.mean(np.square(rb[layer][axis])))),'after':float(np.sqrt(np.mean(np.square(ra[layer][axis]))))}
            key='deltas' if axis=='x' else 'deltas_y'
            overlays(f'L{layer}_hit_{axis}',f'L{layer} Hit Residual;RecHit {axis.upper()} - SimHit {axis.upper()} [um];Unique event/layer pairs',hb[key][layer],ha[key][layer])
    for iteration in report['iterations']:
        run=Path(iteration['run']);summary['iterations'].append({'iteration':iteration['iteration'],'pede':pede_metrics(run/'step4'),'correction':json.loads((run/'step5/complete.json').read_text()),'acts':track_metrics(run/'step3/reco.root'),'observability':json.loads((run/'z_observability.json').read_text())['selected']})
    transforms=placement_transforms(geometry);initial=placement_transforms(geometry.parent.parent/report['initial_geometry']/'geometry.xml');summary['final_centers_mm']={str(l):list(transforms[l].translation) for l in (1,2)}
    summary['geometry_sha256']=digest(geometry);summary['raw_sha256']=report['raw_sha256'];summary['activation']='inactive candidate only'
    for layer in (1,2):
        if f'L{layer}_z' not in report['iterations'][0]['delta_mm_by_component']:continue
        x=array('d',[0]+[i['iteration'] for i in report['iterations']]);y=array('d',[initial[layer].translation[2]]+[i['applied_mm_by_component'][f'L{layer}_z'] for i in report['iterations']])
        graph=ROOT.TGraph(len(x),x,y);graph.SetName(f'L{layer}_geometry_z');graph.SetTitle(f'L{layer} Geometry Correction;Iteration;Sensitive center Global Z [mm]');graph.SetMarkerStyle(20);graph.Write()
        canvas=ROOT.TCanvas('canvas_'+graph.GetName(),'Geometry Correction',900,650);graph.Draw('APL');canvas.Write();canvas.SaveAs(str(output/(graph.GetName()+'.pdf')));keep.extend([graph,canvas])
    x=array('d',range(len(report['iterations'])+1));y=array('d',[i['track_chi2_ratio'] for i in report['iterations']]+[summary['after']['chi2_over_stored_ndf']])
    graph=ROOT.TGraph(len(x),x,y);graph.SetName('acts_quality');graph.SetTitle('ACTS quality;Geometry iteration;ACTS chi2 / stored-NDF');graph.SetMarkerStyle(20);graph.Write();canvas=ROOT.TCanvas('canvas_acts_quality','',900,650);graph.Draw('APL');canvas.Write();canvas.SaveAs(str(output/'acts_quality.pdf'));keep.extend([graph,canvas]);file.Close()
    write_json(output/'summary.json',summary)



def geometry_comparison(output,case,controller):
    """Supplement existing ROOT diagnostics without reopening their ROOT file."""
    import ROOT
    from array import array
    ROOT.gROOT.SetBatch(True)
    success=json.loads((controller/'success.json').read_text());report=json.loads(Path(success['report']).read_text());final=Path(success['candidate'])
    transforms=[placement_transforms(path) for path in [final.parent.parent/report['initial_geometry']/'geometry.xml',case/'step1/misaligned.xml',final]]
    path=output/'geometry.root'
    if path.exists():raise FileExistsError(path)
    file=ROOT.TFile(str(path),'CREATE');canvas=ROOT.TCanvas('c_z_geometry','Detector Geometry comparison',1400,500);canvas.Divide(3,1);keep=[canvas]
    canvas.cd(1);multi=ROOT.TMultiGraph('g_all_planes','Detector Geometry;Global Z [mm];Layer index');legend=ROOT.TLegend(.12,.7,.5,.89)
    for placement,color,marker,name in zip(transforms,(ROOT.kGray+2,ROOT.kRed,ROOT.kBlue),(24,25,20),('G0','Simulation','Final inactive candidate')):
        graph=ROOT.TGraph(7,array('d',[placement[l].translation[2] for l in range(7)]),array('d',range(7)));graph.SetName('planes_'+name.split()[0]);graph.SetMarkerColor(color);graph.SetMarkerStyle(marker);multi.Add(graph,'P');graph.Write();legend.AddEntry(graph,name,'p');keep.append(graph)
    multi.Draw('AP');legend.Draw();multi.Write();keep.extend([multi,legend])
    for pad,layer in [(2,1),(3,2)]:
        canvas.cd(pad);graph=ROOT.TGraph(3,array('d',[0,1,2]),array('d',[t[layer].translation[2] for t in transforms]));graph.SetName(f'L{layer}_geometry_comparison');graph.SetTitle(f'L{layer} sensitive center;Geometry: 0=G0, 1=Simulation, 2=Final;Global Z [mm]');graph.SetMarkerStyle(20);graph.Draw('APL');graph.Write();keep.append(graph)
    canvas.Write();canvas.SaveAs(str(output/'geometry_comparison.pdf'));file.Close()


def observability_plots(output,controller):
    """ROOT angular coverage and profiled global-parameter correlation diagnostics."""
    import ROOT
    from array import array
    ROOT.gROOT.SetBatch(True)
    success=json.loads((controller/'success.json').read_text());report=json.loads(Path(success['report']).read_text())
    diagnostic=json.loads((Path(report['iterations'][0]['run'])/'z_observability.json').read_text())
    path=output/'observability.root'
    if path.exists():raise FileExistsError(path)
    file=ROOT.TFile(str(path),'CREATE');values=np.array(diagnostic['tx_ty']['values']);keep=[]
    canvas=ROOT.TCanvas('c_slope_coverage','Reference slope coverage',1300,450);canvas.Divide(3,1)
    for index,axis in enumerate(('tx','ty')):
        canvas.cd(index+1);data=values[:,index];pad=max(float(np.ptp(data))*.1,1e-6)
        hist=ROOT.TH1D(axis,axis+' reference slope;'+axis+' [mm/mm];Accepted tracks',25,float(data.min()-pad),float(data.max()+pad))
        for value in data:hist.Fill(float(value))
        hist.Write();hist.Draw('HIST');keep.append(hist)
    canvas.cd(3);graph=ROOT.TGraph(len(values),array('d',values[:,0]),array('d',values[:,1]));graph.SetName('joint_slopes');graph.SetTitle('Joint slope coverage;tx [mm/mm];ty [mm/mm]');graph.SetMarkerStyle(20);graph.Draw('AP');graph.Write();canvas.Write();canvas.SaveAs(str(output/'slope_coverage.pdf'));keep.extend([canvas,graph])
    info=diagnostic['joint_xyz'];labels=info['labels'];matrix=info['correlation'];n=len(labels)
    if matrix is not None:
        canvas=ROOT.TCanvas('c_xyz_correlation','Profiled XYZ correlation',900,750);hist=ROOT.TH2D('xyz_correlation','Profiled XYZ design correlation',n,0,n,n,0,n);hist.SetStats(0)
        for i,label in enumerate(labels):
            hist.GetXaxis().SetBinLabel(i+1,str(label));hist.GetYaxis().SetBinLabel(i+1,str(label))
            for j in range(n):hist.SetBinContent(i+1,j+1,matrix[i][j])
        hist.SetMinimum(-1);hist.SetMaximum(1);hist.Draw('COLZ TEXT');hist.Write();canvas.Write();canvas.SaveAs(str(output/'xyz_correlation.pdf'));keep.extend([canvas,hist])
    file.Close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',type=Path,required=True);p.add_argument('--controller',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();success=json.loads((a.controller/'success.json').read_text());report=json.loads(Path(success['report']).read_text())
    render(a.output,a.case/'step3',a.controller/'final/step3',a.case/'step2/events.edm4hep.root',report,Path(success['candidate']))

    geometry_comparison(a.output,a.case,a.controller)

    observability_plots(a.output,a.controller)

"""ROOT-only plots for the focused independent-seed Rz study."""

def plot(out,records,design):
    import ROOT
    from array import array
    ROOT.gROOT.SetBatch(True);file=ROOT.TFile(str(out/'rz_statistics.root'),'CREATE')
    keep=[]
    def histogram(name,title,values,truth=None):
        values=list(map(float,values));lo=min(values);hi=max(values);width=max((hi-lo)*.15,1e-6)
        h=ROOT.TH1D(name,title,12,lo-width,hi+width)
        for v in values:h.Fill(v)
        h.Write();c=ROOT.TCanvas('canvas_'+name,title,900,650);h.Draw('HIST')
        if truth is not None:
            line=ROOT.TLine(truth,0,truth,max(h.GetMaximum()*1.1,1));line.SetLineColor(ROOT.kRed);line.Draw();keep.append(line)
        c.Write();c.SaveAs(str(out/(name+'.pdf')));keep.extend([h,c])
    for layer,truth in design['truth_rad'].items():
        x=array('d',range(1,len(records)+1));zero=array('d',[0]*len(records))
        y=array('d',[r['statistics'][layer]['initial_estimate_rad']*1000 for r in records])
        ey=array('d',[r['statistics'][layer]['initial_sigma_rad']*1000 for r in records])
        graph=ROOT.TGraphErrors(len(records),x,y,zero,ey);graph.SetName(layer+'_initial_estimates_by_seed')
        graph.SetTitle(layer+' initial estimates;Sample index (seed in samples.json);Physical Rz correction [mrad]')
        graph.SetMarkerStyle(20);graph.Write();canvas=ROOT.TCanvas('canvas_'+graph.GetName(),'',1000,650);graph.Draw('AP')
        line=ROOT.TLine(.5,truth*1000,len(records)+.5,truth*1000);line.SetLineColor(ROOT.kRed);line.Draw()
        canvas.Write();canvas.SaveAs(str(out/(graph.GetName()+'.pdf')));keep.extend([graph,canvas,line])
        for key,scale,title,reference in [('initial_estimate_rad',1000,'Initial physical Rz estimate;Rotation [mrad];Samples',truth*1000),('initial_sigma_rad',1000,'Initial Pede nominal uncertainty;Uncertainty [mrad];Samples',None),('pull',1,'Initial-fit pull;(Correction - injected rotation) / nominal uncertainty;Samples',0),('final_cumulative_rad',1000,'Final cumulative Geometry correction;Rotation [mrad];Samples',truth*1000)]:
            histogram(layer+'_'+key,layer+' '+title,[r['statistics'][layer][key]*scale for r in records],reference)
        for xname,xvalues in [('tracks',[r['iterations'][0]['acts']['tracks'] for r in records]),('initial_max_rejects',[r['iterations'][0]['pede']['max_rejected_local_fits'] for r in records])]:
            g=ROOT.TGraph(len(records),array('d',xvalues),array('d',[r['statistics'][layer]['pull'] for r in records]));g.SetName(layer+'_pull_vs_'+xname);g.SetTitle(layer+' pull dependence;'+xname+';Initial-fit pull');g.SetMarkerStyle(20);g.Write();c=ROOT.TCanvas('canvas_'+g.GetName(),'',900,650);g.Draw('AP');c.Write();c.SaveAs(str(out/(g.GetName()+'.pdf')));keep.extend([g,c])
    for which,index in [('initial',0),('last',-1)]:histogram('pede_'+which,'Pede '+which+';Pede #chi^{2}/NDF;Samples',[r['iterations'][index]['pede']['chi2_ndf'] for r in records])
    for which in ['before','after']:histogram('acts_'+which,'ACTS '+which+';ACTS #chi^{2}/stored-NDF;Samples',[(r['iterations'][0]['acts'] if which=='before' else r['final_acts'])['chi2_over_stored_ndf'] for r in records])
    file.Close()

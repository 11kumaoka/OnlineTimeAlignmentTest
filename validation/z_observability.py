"""Profile the actual Mille local design before assessing Global Z information.

This diagnostic uses the writer's frozen reconstructed-track reference slopes,
not Truth. The production fit and its input uncertainties are unchanged.
"""
import argparse,json
from pathlib import Path
import numpy as np
from validation.validate_rz_derivatives import records
from research_common import write_json,digest


def measurements(path):
    for record in records(path):
        pairs=list(record);i=1;rows=[]
        while i<len(pairs):
            value,label=pairs[i];assert label==0;i+=1;local={}
            while i<len(pairs) and pairs[i][1]!=0:
                derivative,index=pairs[i];local[index]=derivative;i+=1
            sigma,zero=pairs[i];assert zero==0 and sigma>0;i+=1;glob={}
            while i<len(pairs) and pairs[i][1]!=0:
                derivative,index=pairs[i];glob[index]=derivative;i+=1
            rows.append((value,sigma,local,glob))
        assert len(rows)==10
        yield rows


def information(blocks,labels,slope_scale=1.):
    total=np.zeros((len(labels),len(labels)))
    for rows in blocks:
        a=np.array([[row[2].get(k,0.)/row[1] for k in range(1,5)] for row in rows])
        assert np.linalg.matrix_rank(a)==4
        g=np.array([[row[3].get(k,0.)*(slope_scale if k>=4000 else 1.)/row[1] for k in labels] for row in rows])
        q=np.eye(10)-a@np.linalg.pinv(a)
        total+=g.T@q@g
    total=(total+total.T)/2;diag=np.sqrt(np.maximum(np.diag(total),0.));den=np.outer(diag,diag)
    normalized=np.divide(total,den,out=np.zeros_like(total),where=den>0)
    eigen=np.linalg.eigvalsh(normalized);rank=int(np.sum(eigen>1e-9))
    cov=np.linalg.inv(total) if rank==len(labels) and np.all(diag>0) else None
    return {'labels':labels,'information':total.tolist(),'rank':rank,'column_normalized_eigenvalues':eigen.tolist(),
        'weak_eigenvectors':np.linalg.eigh(normalized)[1][:,:min(2,len(labels))].tolist(),
        'sigma_mm':{str(k):float(np.sqrt(max(0.,cov[i,i]))) for i,k in enumerate(labels)} if cov is not None else None,
        'correlation':(cov/np.sqrt(np.outer(np.diag(cov),np.diag(cov)))).tolist() if cov is not None else None}


def diagnose(mille,mode):
    layers=[1] if mode=='l1_z' else [1,2]
    selected=[4000+l for l in layers] if mode!='l1_l2_xyz' else [k+l for l in layers for k in (1000,2000,4000)]
    blocks=list(measurements(mille));slopes=[]
    for rows in blocks:
        tx=rows[2*layers[0]][3].get(4000+layers[0],0.);ty=rows[2*layers[0]+1][3].get(4000+layers[0],0.);slopes.append([tx,ty])
        for l in range(5):
            rows[2*l][3][4000+l]=tx;rows[2*l+1][3][4000+l]=ty
    values=np.asarray(slopes);joint=[k+l for l in layers for k in (1000,2000,4000)]
    report={'mode':mode,'tracks':len(blocks),'mille_sha256':digest(mille),'units':'mm parameters; Z derivatives mm/mm',
        'local_model':'four local parameters profiled separately for each actual track (weighted Schur complement)',
        'tx_ty':{'mean':values.mean(0).tolist(),'sample_sd':values.std(0,ddof=1).tolist(),'min':values.min(0).tolist(),'max':values.max(0).tolist(),'covariance':np.cov(values.T).tolist(),'values':values.tolist()},
        'selected':information(blocks,selected),'joint_xyz':information(blocks,joint),
        'joint_xyz_with_L3_xy_nuisance':information(blocks,joint+[1003,2003]),
        'all_five_z_free':information(blocks,list(range(4000,4005))),
        'reference_layer_design_profiles':{
            'L0_L4_fixed_Z3_nuisance':information(blocks,[4001,4002,4003]),
            'hypothetical_L0_L3_fixed':information(blocks,[4001,4002,4004]),
            'hypothetical_L1_L4_fixed':information(blocks,[4000,4002,4003])},
        'zero_slope_negative_control':information(blocks,selected,0.),
        'narrow_slope_design_control':information(blocks,selected,1e-3)}
    return report


def enforce(report,max_sigma):
    info=report['selected']
    if info['rank']!=len(info['labels']) or info['sigma_mm'] is None:raise ValueError('Unobservable selected Z design')
    if any(info['sigma_mm'][str(k)]>max_sigma for k in info['labels'] if k>=4000):raise ValueError('Insufficient Z slope information for configured resolution bound')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mille',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mode',choices=['l1_z','l1_l2_z','l1_l2_xyz'],required=True)
    p.add_argument('--max-sigma-mm',type=float,default=.5)
    a=p.parse_args();report=diagnose(a.mille,a.mode)
    try:enforce(report,a.max_sigma_mm)
    except ValueError as error:
        report.update(passed=False,reason=str(error));write_json(a.output,report);raise
    report.update(passed=True,max_z_sigma_mm=a.max_sigma_mm);write_json(a.output,report)
    print('PASS',report['tracks'],'tracks; rank',report['selected']['rank'],'sigma',report['selected']['sigma_mm'])


if __name__=='__main__':main()

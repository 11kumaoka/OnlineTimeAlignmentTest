"""Straight-line Fisher diagnostics for L1 rotation coverage and translation correlations."""
import sys,json,argparse
from pathlib import Path
import numpy as np,uproot,awkward as ak
from research_common import write_json
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reco',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--mode',choices=['l1_rz','l1_l2_rz','l1_l2_xy_rz'],default='l1_rz')
args=parser.parse_args();p=args.reco
layers=(1,) if args.mode=='l1_rz' else (1,2)
parameters=[(l,c) for l in layers for c in ('x','y','rz')]
if args.mode=='l1_l2_xy_rz':parameters += [(3,'x'),(3,'y')]
with uproot.open(p) as f:
 t=f['events'];get=lambda c,x:ak.to_list(t[f'{c}/{c}.{x}'].array())
 ids=get('LocalSiMAPSRecHits','cellID');xs=get('LocalSiMAPSRecHits','position.x');ys=get('LocalSiMAPSRecHits','position.y');zs=get('LocalSiMAPSRecHits','position.z');tracks=get('LocalBeamTestTracks','ndf')
hits=[]
for ev,tr in enumerate(tracks):
 if not tr:continue
 h=sorted([(c>>11&63,x,y,z) for c,x,y,z in zip(ids[ev],xs[ev],ys[ev],zs[ev])])
 if [v[0] for v in h]!=list(range(5)):continue
 hits.append(np.asarray([v[1:] for v in h]))
def information(hits,scale=1.):
 total=np.zeros((len(parameters),len(parameters)));blocks=[]
 for h in hits:
  h=h.copy();h[:,:2]*=scale
  local=np.zeros((10,4));g=np.zeros((10,len(parameters)))
  for l,(x,y,z) in enumerate(h):
   local[2*l]=[1,0,z-100,0];local[2*l+1]=[0,1,0,z-100]
   for j,(layer,component) in enumerate(parameters):
    if layer!=l:continue
    if component=='x':g[2*l,j]=1
    if component=='y':g[2*l+1,j]=1
    if component=='rz':g[2*l,j]=-y;g[2*l+1,j]=x
  projector=np.eye(10)-local@np.linalg.solve(local.T@local,local.T)
  total+=g.T@projector@g/.01**2
  blocks.append((g,projector,h[:,:2].reshape(-1)))
 eig=np.linalg.eigvalsh(total);rank=int(np.linalg.matrix_rank(total))
 cov=np.linalg.pinv(total);norm=np.sqrt(np.outer(np.diag(cov),np.diag(cov)))
 angular=[i for i,p in enumerate(parameters) if p[1]=='rz']
 information_rz=total[np.ix_(angular,angular)]
 cov_rz=np.linalg.pinv(information_rz)
 conditional={f'L{parameters[i][0]}_rz':float(np.sqrt(cov_rz[j,j])) if np.linalg.matrix_rank(information_rz)==len(angular) else None for j,i in enumerate(angular)}
 std=np.sqrt(np.diag(total));scaled=total/np.outer(np.where(std>0,std,1),np.where(std>0,std,1))
 result={'parameters':[f'L{l}_{c}_'+('rad' if c=='rz' else 'mm') for l,c in parameters],'rank':rank,
 'eigenvalues_mixed_units':eig.tolist(),'eigenvalues_column_normalized':np.linalg.eigvalsh(scaled).tolist(),
 'sigma_rotation_only_rad':conditional,'sigma_rz_only_rad':conditional['L1_rz'],
 'sigma_joint_rad':float(np.sqrt(cov[2,2])) if rank==len(parameters) else None,
 'sigma_by_parameter':[float(v) for v in np.sqrt(np.diag(cov))] if rank==len(parameters) else None,
 'correlation':(cov/norm).tolist() if rank==len(parameters) and np.all(norm>0) else None}
 if scale==1.:
  indices=list(range(len(parameters))) if args.mode=='l1_l2_xy_rz' else angular
  matrix=total[np.ix_(indices,indices)]
  if np.linalg.matrix_rank(matrix)==len(indices):
   rhs=sum(g[:,indices].T@q@m/.01**2 for g,q,m in blocks)
   inverse=np.linalg.inv(matrix);bias=inverse@rhs
   scores=[g[:,indices].T@q@(m-g[:,indices]@bias)/.01**2 for g,q,m in blocks]
   meat=sum(np.outer(score,score) for score in scores)
   robust=inverse@meat@inverse*len(hits)/(len(hits)-1)
   result['independent_linearized_fit']={
       'parameters':[result['parameters'][i] for i in indices],'measurement_bias':bias.tolist(),
       'nominal_sigma':np.sqrt(np.diag(inverse)).tolist(),
       'track_cluster_sandwich_sigma':np.sqrt(np.diag(robust)).tolist(),
       'note':'Diagnostic fixed-track linearization; sandwich changes no input uncertainty or production fit'}
 return result
spatial=np.asarray([h[1,:2] for h in hits]);slopes=np.asarray([(h[-1,:2]-h[0,:2])/(h[-1,2]-h[0,2]) for h in hits])
report={'mode':args.mode,'tracks':len(hits),'L1_xy_mean_mm':spatial.mean(0).tolist(),'L1_xy_std_mm':spatial.std(0,ddof=1).tolist(),
 'L1_xy_min_mm':spatial.min(0).tolist(),'L1_xy_max_mm':spatial.max(0).tolist(),'slopes_mean':slopes.mean(0).tolist(),'slopes_std':slopes.std(0,ddof=1).tolist(),
 'information_model':'Independent straight-line design, 0.010 mm isotropic errors; no scattering; diagnostic, not a new fit',
 'statistics':{str(n):information(hits[:n]) for n in sorted(set(min(n,len(hits)) for n in (10,20,50,len(hits))))},
 'narrow_spot_design_only':{str(s):information(hits,s) for s in (1.,.1,.01,0.)}}
point_hits=[h.copy() for h in hits]
for h in point_hits:h[:,:2]=[3.,-2.]
report['point_spot_offset_design_only']=information(point_hits)
report['point_spot_offset_design_only']['impact_mm']=[3.,-2.]
write_json(args.output,report)
print(json.dumps(report,indent=2))

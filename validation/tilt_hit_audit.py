"""Post-fit Truth diagnostic: retain and report off-plane SimHits in tilt studies."""
import argparse,json
from pathlib import Path
import numpy as np
import uproot,awkward as ak
from research_common import write_json,digest


def audit(simulation,reco,contexts):
    geometry=json.loads(contexts.read_text())['layers']
    with uproot.open(reco) as f:
        accepted=ak.to_list(ak.num(f['events']['LocalBeamTestTracks/LocalBeamTestTracks.chi2'].array()))
    with uproot.open(simulation) as f:
        tree=f['events'];ids=ak.to_list(tree['SiMAPSHits/SiMAPSHits.cellID'].array())
        xyz=[ak.to_list(tree['SiMAPSHits/SiMAPSHits.position.'+axis].array()) for axis in 'xyz']
    if len(ids)!=len(accepted):raise ValueError('Simulation/Reconstruction event counts differ')
    anomalies=[];counts={str(l):0 for l in range(5)};max_distances={str(l):0. for l in range(5)}
    for event,identifiers in enumerate(ids):
        for index,identifier in enumerate(identifiers):
            l=(identifier>>11)&63
            if l not in range(5):raise ValueError('Unexpected SiMAPS layer')
            point=np.array([xyz[k][event][index] for k in range(3)])
            center=np.array(geometry[str(l)]['center_mm']);normal=-np.array(geometry[str(l)]['sensor_basis_columns'][1])
            distance=float(np.dot(normal,point-center));counts[str(l)]+=1
            max_distances[str(l)]=max(max_distances[str(l)],abs(distance))
            if abs(distance)>.0251:
                anomalies.append({'event_index':event,'accepted_tracks':accepted[event],'layer':l,'cell_id':identifier,
                                  'point_mm':point.tolist(),'signed_normal_distance_mm':distance})
    return {'simulation_sha256':digest(simulation),'reconstruction_sha256':digest(reco),'truth_usage':'Post-fit diagnostic only; never alignment inference',
            'events':len(ids),'accepted_tracks':sum(accepted),'sim_hits_by_layer':counts,'max_abs_plane_distance_mm':max_distances,
            'sensitive_half_thickness_mm':.025,'tolerance_mm':.0001,'anomalies':anomalies,
            'accepted_event_anomalies':[x for x in anomalies if x['accepted_tracks']],
            'passed':not any(x['accepted_tracks'] for x in anomalies),'filtered_events':0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('simulation','reco','contexts','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();report=audit(a.simulation,a.reco,a.contexts);write_json(a.output,report)
    print('Accepted-event off-plane anomalies:',len(report['accepted_event_anomalies']))
    if not report['passed']:raise SystemExit(1)

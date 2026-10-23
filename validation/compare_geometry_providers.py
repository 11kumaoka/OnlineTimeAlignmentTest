"""Compare local and converted-provider PODIO/Mille outputs without using Truth.

Tolerances are fixed for this integration test: atol=1e-6 in stored units and
rtol=1e-5. Positions are mm, position covariances mm^2, angles rad, q/p GeV^-1,
time ns, and chi2 dimensionless. Integer values and relation targets are exact.
Geometry IDs are mapped to sensor slots using the closed-Geometry probe report.
This does not replace the strict historical local-path byte/value regression.
"""
import argparse
import json
from pathlib import Path
import awkward as ak
import numpy as np
import uproot
from research_common import digest, write_json
from validation.compare_raw_paths import collections, id_names
from validation.validate_rz_derivatives import records


def compare(left, right, geometry_report):
    mapping=json.loads(geometry_report.read_text())
    assert mapping['passed'] and mapping['tracking_geometry_available']
    semantic=[{int(p[k]['geometry_id']):p['layer'] for p in mapping['planes']}
              for k in ('local','selected')]
    for m in semantic:m[0]=-1
    branches=[]
    with uproot.open(left/'reco.root') as lf, uproot.open(right/'reco.root') as rf:
        assert collections(lf)==collections(rf), 'Collection mismatch'
        trees=[f['events'] for f in (lf,rf)];maps=[id_names(f) for f in (lf,rf)]
        assert trees[0].num_entries==trees[1].num_entries
        keys=[k for k in trees[0].keys() if '/' in k]
        assert set(keys)=={k for k in trees[1].keys() if '/' in k}
        for key in keys:
            assert trees[0][key].typename==trees[1][key].typename,key
            arrays=[t[key].array() for t in trees]
            assert ak.to_list(ak.num(arrays[0]))==ak.to_list(ak.num(arrays[1])),key
            values=[ak.to_numpy(ak.flatten(v,axis=None)) for v in arrays]
            a,b=values
            maximum=0.
            if key.endswith('.collectionID'):
                assert [maps[0].get(int(x),str(x)) for x in a]==[maps[1].get(int(x),str(x)) for x in b],key
            elif key.endswith('.surface'):
                assert [semantic[0][int(x)] for x in a]==[semantic[1][int(x)] for x in b],key
            elif a.dtype.kind=='f':
                assert np.allclose(a,b,atol=1e-6,rtol=1e-5,equal_nan=True),key
                finite=np.isfinite(a)&np.isfinite(b)
                maximum=float(np.max(np.abs(a[finite]-b[finite]))) if np.any(finite) else 0.
            else:assert np.array_equal(a,b),key
            branches.append({'branch':key,'max_absolute_difference_stored_units':maximum})
    lrecords=[list(r) for r in records(left/'mille.dat')]
    rrecords=[list(r) for r in records(right/'mille.dat')]
    assert len(lrecords)==len(rrecords)
    max_mille=0.
    for a,b in zip(lrecords,rrecords):
        assert [p[1] for p in a]==[p[1] for p in b], 'Mille label/record structure mismatch'
        x=np.array([p[0] for p in a]);y=np.array([p[0] for p in b])
        assert np.allclose(x,y,atol=1e-6,rtol=1e-5), 'Mille residual/derivative mismatch'
        max_mille=max(max_mille,float(np.max(np.abs(x-y))))
    return {'passed':True,'truth_used':False,'podio_branches':branches,'mille_records':len(lrecords),
            'mille_bytes_identical':digest(left/'mille.dat')==digest(right/'mille.dat'),
            'max_mille_absolute_difference':max_mille,'geometry_report_sha256':digest(geometry_report),
            'criteria':{'absolute':1e-6,'relative':1e-5,'integer_relations':'exact','surface_ids':'sensor semantics'}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--local',type=Path,required=True,help='Local reconstruction stage directory')
    p.add_argument('--blueprint',type=Path,required=True,help='Experimental reconstruction stage directory')
    p.add_argument('--geometry-report',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=compare(a.local,a.blueprint,a.geometry_report)
    write_json(a.output,report);print('PASS:',len(report['podio_branches']),'PODIO branches;',report['mille_records'],'Mille records')


if __name__=='__main__':main()

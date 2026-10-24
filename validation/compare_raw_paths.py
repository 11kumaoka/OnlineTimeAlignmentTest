#!/usr/bin/env python3
"""Compare PODIO values and named relation targets, not only track counters."""
import argparse
import json
import math
from pathlib import Path
import awkward as ak
import uproot
from alignment.pede import read_pede
from digitization.contract import RAW_COLLECTIONS
from research_common import digest, write_json


def collections(file):
    return {k for k,v in file['events'].typenames().items() if 'Data>' in v and '/' not in k}


def id_names(file):
    metadata = file['podio_metadata']
    prefix = 'events___CollectionTypeInfo/events___CollectionTypeInfo.'
    return dict(zip(ak.to_list(metadata[prefix+'collectionID'].array())[0],
                    ak.to_list(metadata[prefix+'name'].array())[0]))


def canonical(value):
    if isinstance(value,list): return [canonical(v) for v in value]
    if isinstance(value,float) and math.isnan(value): return 'NaN'
    return value


def compare_files(left,right,selected=None):
    with uproot.open(left) as lf, uproot.open(right) as rf:
        common = selected or (collections(lf)&collections(rf))
        maps = [id_names(f) for f in (lf,rf)]
        def branch_keys(file):
            return {key for key in file['events'].keys() if '/' in key and
                    (key.split('/')[0] in common or any(key.split('/')[0].startswith('_'+c+'_') for c in common))}
        keys = sorted(branch_keys(lf))
        assert set(keys)==branch_keys(rf), 'Different field/relation branch schemas'
        for key in keys:
            if key not in rf['events']: raise AssertionError(f'Missing branch: {key}')
            assert lf['events'][key].typename==rf['events'][key].typename, f'Different branch type: {key}'
            values = [ak.to_list(f['events'][key].array()) for f in (lf,rf)]
            if key.endswith('.collectionID'):
                # PODIO collection IDs may be remapped; collection names are the stable identity.
                values = [[[mapping.get(x,f'unavailable:{x}') for x in event] for event in array]
                          for array,mapping in zip(values,maps)]
            assert canonical(values[0])==canonical(values[1]),f'Non-equivalent branch: {key}'
        return {'collections':sorted(common),'branches_compared':len(keys),'comparison':'exact values; relation collection IDs resolved to names'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('combined','split','raw','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    combined=a.combined/'step3/reco.root';split=a.split/'step3/reco.root'
    report={'raw_vs_combined':compare_files(combined,a.raw,set(RAW_COLLECTIONS)|{'EventHeader'}),
            'raw_vs_split':compare_files(a.raw,split,set(RAW_COLLECTIONS)|{'EventHeader'}),
            'downstream':compare_files(combined,split)}
    with uproot.open(a.raw) as f:
        assert collections(f)=={'EventHeader',*RAW_COLLECTIONS}
        report['raw_events']=f['events'].num_entries
        report['raw_counts']={c:int(ak.sum(ak.num(f['events'][f'{c}/{c}.cellID'].array()))) for c in RAW_COLLECTIONS}
    with uproot.open(split) as f:
        assert not any('MC' in c or c.endswith('Hits') and not c.startswith('Local') for c in collections(f))
        t=f['events'];report['tracks']=int(ak.sum(ak.num(t['LocalBeamTestTracks/LocalBeamTestTracks.chi2'].array())))
        report['acts_chi2_sum']=float(ak.sum(t['LocalBeamTestTracks/LocalBeamTestTracks.chi2'].array()))
    assert (a.combined/'step3/mille.dat').read_bytes()==(a.split/'step3/mille.dat').read_bytes()
    report['mille_bytes_identical']=True;report['mille_sha256']=digest(a.split/'step3/mille.dat')
    cp,sp=[read_pede(d/'step4/millepede.res') for d in (a.combined,a.split)]
    assert cp==sp;report['pede_parameters_mm']=sp;report['pede_parameters_identical']=True
    write_json(a.output,report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()

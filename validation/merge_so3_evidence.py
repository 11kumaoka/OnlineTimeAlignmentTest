"""Seal physical derivative and noiseless matrix-closure evidence for the Controller."""
import argparse
import json
from pathlib import Path
from research_common import REPO,digest,write_json


# Pin the adapters that select and physically place the supported scopes as well
# as the numerical model. Binary fingerprints remain independently mandatory.
IMPLEMENTATION_SOURCES=(
    'localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.cc',
    'localDetEICrecon/algorithms/tracking/BeamTestACTSFitter.h',
    'localDetEICrecon/algorithms/tracking/BeamTestACTSFitterConfig.h',
    'localDetEICrecon/factories/tracking/BeamTestACTSFitter_factory.h',
    'reconstruction/reconstruct.py',
    'correction/scope.py','correction/correct_geometry.py','geometry/transforms.py',
    'geometry/prepare.py','geometry/placements.py','calibration/settings.py',
    'localDetEICrecon/processors/BeamTestMilleProcessor.cc',
    'localDetEICrecon/geometry/SiTrackerEndcap2XY_geo.cpp',
    'localDetEICrecon/geometry/SurfacePlacements.h',
    'localDetEICrecon/alignment/src/BeamTestMilleWriter.cc',
    'localDetEICrecon/alignment/src/BeamTestMilleWriter.h',
    'localDetEICrecon/alignment/src/TiltMeasurementModel.h')


def merge(build,derivatives,noiseless):
    plugin=digest(build/'BeamTestReco.so');factory=digest(build/'libLocalTelescopeGeometry.so')
    labels=set();proofs=[];contexts=0;entries=0;cases=[]
    for path in derivatives:
        r=json.loads(path.read_text())
        if r.get('passed') is not True or r.get('linearization')!='so3_profiled_covariance_v1':raise ValueError('Missing coupled physical derivative validation')
        if r.get('plugin_sha256')!=plugin or r.get('geometry_plugin_sha256')!=factory:raise ValueError('Stale derivative evidence')
        if r.get('fresh_physical_contexts',0)<=0 or r.get('actual_binary_entries',0)<=0:raise ValueError('Missing physical contexts or actual binary checks')
        labels.update(r['labels']);contexts+=r['fresh_physical_contexts'];entries+=r['actual_binary_entries']
        proofs.append({'path':str(path.resolve()),'sha256':digest(path)})
    for path in sorted(noiseless.glob('*/report.json')):
        r=json.loads(path.read_text())
        if r.get('passed') is not True or not r.get('model_sources_sha256'):raise ValueError('Incomplete noiseless matrix validation')
        if any(digest(REPO/p)!=sha for p,sha in r['model_sources_sha256'].items()):raise ValueError('Noiseless validation uses a different model source')
        cases.append({'path':str(path.resolve()),'sha256':digest(path)})
    if not cases:raise ValueError('No noiseless cases')
    return {'passed':True,'linearization':'so3_profiled_covariance_v1','plugin_sha256':plugin,'geometry_plugin_sha256':factory,
        'labels':sorted(labels),'actual_binary_entries':entries,'fresh_physical_contexts':contexts,
        'derivative_reports':proofs,'noiseless_reports':cases,
        'implementation_sources_sha256':{p:digest(REPO/p) for p in IMPLEMENTATION_SOURCES},
        'writer_source_sha256':digest(REPO/'localDetEICrecon/alignment/src/BeamTestMilleWriter.cc'),
        'status':'Mathematical/physical derivative gate only; not statistical coverage or automatic Geometry approval'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-dir',type=Path,required=True)
    p.add_argument('--derivative-report',type=Path,action='append',required=True);p.add_argument('--noiseless',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    write_json(a.output,merge(a.build_dir,a.derivative_report,a.noiseless));print('PASS: sealed coupled rotation evidence')


if __name__=='__main__':main()

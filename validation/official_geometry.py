"""Isolated local/official Geometry audit; never selects a calibration provider.

The official-elements mode tests the surface converter component only.
This diagnostic performs no track fitting or alignment.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
from geometry.environment import geometry_environment
from research_common import REPO, digest, write_json


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry',type=Path,required=True)
    parser.add_argument('--build-dir',type=Path,required=True,help='New build containing TelescopeGeometryProbe')
    parser.add_argument('--geometry-build-dir',type=Path,help='Existing validated local detector-factory build; required for Local_SiTrackerEndcap2XY XML')
    parser.add_argument('--provider',choices=('local','official','official-elements'),default='local')
    parser.add_argument('--metadata',choices=('none','discovery','discovery-and-flags'),default='none',help='Explicit process-local metadata experiment; never edits XML/placements')
    parser.add_argument('--output-dir',type=Path,required=True,help='New diagnostic directory under result/; never reused')
    a=parser.parse_args();xml=a.geometry.resolve();out=a.output_dir.resolve()
    if not out.is_relative_to(REPO/'result') or out==REPO/'result':parser.error('output-dir must be a child of result/')
    binary=a.build_dir.resolve()/'TelescopeGeometryProbe'
    if not binary.is_file():parser.error('Build the optional TelescopeGeometryProbe target first')
    if a.geometry_build_dir:os.environ['TESTBENCH_BUILD_DIR']=str(a.geometry_build_dir.resolve())
    env=geometry_environment(xml)
    out.mkdir(parents=True,exist_ok=False)
    command=list(map(str,[binary,xml,out/'geometry.json',a.provider,a.metadata]))
    write_json(out/'command.json',{'argv':command,'cwd':str(REPO),'geometry_sha256':digest(xml),'probe_sha256':digest(binary),
        'probe_source_sha256':digest(REPO/'localDetEICrecon/geometry/OfficialGeometryProbe.cc'),
        'provider_selection':'Diagnostic only; production fitter and Controller remain unchanged',
        'image':env.get('TESTBENCH_IMAGE')})
    with (out/'stdout.log').open('x') as log:process=subprocess.run(command,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
    write_json(out/'exit.json',{'exit_code':process.returncode})
    report=json.loads((out/'geometry.json').read_text()) if (out/'geometry.json').exists() else {}
    if process.returncode:
        parser.exit(process.returncode,'Geometry probe failed: '+report.get('conversion_error',report.get('error','see stdout.log'))+'\nArtifacts retained: '+str(out)+'\n')
    print(report['status']+'; output: '+str(out))


if __name__=='__main__':main()

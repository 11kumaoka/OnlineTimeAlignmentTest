"""Build a private ACTS 45.3 converter experiment, never a production provider.

The installed EICrecon provider calls the executable-exported converter copy.
Only the singleton-endcap guard is relaxed when explicitly requested. All
installed libraries, production fitting and physical XML inputs remain intact.
"""
import argparse
import difflib
import json
import os
from pathlib import Path
import subprocess
from geometry.environment import geometry_environment
from research_common import REPO, digest, write_json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--converter-source',type=Path,required=True,help='Unmodified ConvertDD4hepDetector.cpp from ACTS d1323a298569942d98ff46ee413031ebd604290d')
    p.add_argument('--geometry',type=Path,required=True)
    p.add_argument('--geometry-build-dir',type=Path,required=True)
    p.add_argument('--build-dir',type=Path,required=True,help='New isolated directory under build/')
    p.add_argument('--output-dir',type=Path,required=True,help='New evidence directory under result/')
    p.add_argument('--metadata',choices=['none','discovery','discovery-and-flags'],default='none')
    p.add_argument('--allow-single-endcap',action='store_true')
    p.add_argument('--zero-inner-envelope',action='store_true',help='Diagnostic only: use zero inner radial layer envelope for sensors touching r=0')
    a=p.parse_args()
    a.build_dir=a.build_dir.resolve();a.output_dir=a.output_dir.resolve()
    if not a.build_dir.is_relative_to(REPO/'build') or a.build_dir==REPO/'build':p.error('build-dir must be a child of build/')
    if not a.output_dir.is_relative_to(REPO/'result') or a.output_dir==REPO/'result':p.error('output-dir must be a child of result/')
    if a.build_dir.exists() or a.output_dir.exists():p.error('Both build and output directories must be new')
    source=a.converter_source.resolve();original=source.read_text()
    expected='1ee6b01aa7de2d6357781e1bcdaef366480bd6aa63fa1e1c9a83fde645e93231'
    if digest(source)!=expected:p.error('Converter does not match the audited ACTS 45.3 source')
    old='''      throw std::logic_error(
          "Only one Endcap is given for the current "
          "hierarchy! Endcaps should always occur in "
          "pairs. Please check your detector "
          "construction.");'''
    if original.count(old)!=1:p.error('Expected exactly one paired-endcap guard')
    modified=original
    if a.allow_single_endcap:modified=modified.replace(old,'      ACTS_WARNING("TESTBENCH: allow one real endcap; downstream construction must still pass");')
    marker='  ACTS_WARNING("TESTBENCH: executable-local converter; installed libraries unchanged");\n'
    modified=modified.replace('  // create local logger for conversion\n',marker+'  // create local logger for conversion\n',1)
    a.output_dir.mkdir(parents=True,exist_ok=False)
    private=a.output_dir/'converter';private.mkdir()
    (private/'ConvertDD4hepDetector.cpp').write_text(modified)
    (private/'converter.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),modified.splitlines(True),fromfile='ACTS-45.3/ConvertDD4hepDetector.cpp',tofile='private/ConvertDD4hepDetector.cpp')))
    probe=(REPO/'localDetEICrecon/geometry/OfficialGeometryProbe.cc').read_text()
    if a.zero_inner_envelope:
        old_envelope='p.set<double>(key,.01);'
        if probe.count(old_envelope)!=1:p.error('Cannot locate the diagnostic envelope assignment')
        probe=probe.replace(old_envelope,'p.set<double>(key,std::string(key)=="envelope_r_min"?0.:.01);')
    (private/'Probe.cc').write_text(probe)
    cmake='''cmake_minimum_required(VERSION 3.20)
project(LegacyEndcapExperiment LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(EICrecon CONFIG REQUIRED)
find_package(Acts REQUIRED COMPONENTS Core PluginDD4hep)
find_package(DD4hep REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(fmt REQUIRED)
find_package(spdlog REQUIRED)
find_path(EICRECON_INCLUDE_DIR algorithms/tracking/ActsGeometryProvider.h HINTS /opt/local/include/EICrecon REQUIRED)
add_executable(TelescopeLegacyEndcapProbe Probe.cc ConvertDD4hepDetector.cpp)
target_include_directories(TelescopeLegacyEndcapProbe PRIVATE "GEOMETRY_INCLUDE" ${EICRECON_INCLUDE_DIR})
target_compile_definitions(TelescopeLegacyEndcapProbe PRIVATE Acts_VERSION_MAJOR=${Acts_VERSION_MAJOR})
target_link_options(TelescopeLegacyEndcapProbe PRIVATE -Wl,--export-dynamic)
target_link_libraries(TelescopeLegacyEndcapProbe PRIVATE EICrecon::algorithms_tracking_library Acts::Core Acts::PluginDD4hep DD4hep::DDCore DD4hep::DDRec nlohmann_json::nlohmann_json fmt::fmt spdlog::spdlog)
'''.replace('PROBE_SOURCE',str(REPO/'localDetEICrecon/geometry/OfficialGeometryProbe.cc')).replace('GEOMETRY_INCLUDE',str(REPO/'localDetEICrecon/geometry'))
    (private/'CMakeLists.txt').write_text(cmake)
    commands=[]
    def call(command,name,env=None):
        commands.append(list(map(str,command)))
        with (a.output_dir/(name+'.log')).open('x') as log:
            return subprocess.run(list(map(str,command)),cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    write_json(a.output_dir/'provenance.json',{'original_source':str(source),'original_source_sha256':expected,'patched_source_sha256':digest(private/'ConvertDD4hepDetector.cpp'),'probe_source_sha256':digest(REPO/'localDetEICrecon/geometry/OfficialGeometryProbe.cc'),'allow_single_endcap':a.allow_single_endcap,'zero_inner_envelope':a.zero_inner_envelope,'generated_probe_sha256':digest(private/'Probe.cc'),'geometry':str(a.geometry.resolve()),'geometry_sha256':digest(a.geometry),'geometry_factory_sha256':digest(a.geometry_build_dir/'libLocalTelescopeGeometry.so'),'metadata':a.metadata,'installed_libraries_modified':False,'reconstruction_enabled':False})
    rc=call(['cmake','-S',private,'-B',a.build_dir,'-DCMAKE_BUILD_TYPE=RelWithDebInfo'],'configure')
    if not rc:rc=call(['cmake','--build',a.build_dir,'-j','2'],'build')
    if rc:write_json(a.output_dir/'commands.json',commands);p.exit(rc,'Private build failed; partial artifacts retained\n')
    os.environ['TESTBENCH_BUILD_DIR']=str(a.geometry_build_dir.resolve())
    rc=call([a.build_dir/'TelescopeLegacyEndcapProbe',a.geometry.resolve(),a.output_dir/'geometry.json','official',a.metadata],'probe',geometry_environment(a.geometry))
    log=(a.output_dir/'probe.log').read_text()
    interposed='TESTBENCH: executable-local converter' in log
    write_json(a.output_dir/'exit.json',{'probe_exit_code':rc,'private_converter_called':interposed})
    write_json(a.output_dir/'commands.json',commands)
    if not interposed:p.exit(1,'Private converter interposition was not demonstrated; no valid experiment\n')
    print('Private converter exercised; probe exit',rc,'; evidence:',a.output_dir)
    if rc:p.exit(rc)


if __name__=='__main__':main()

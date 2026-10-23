"""Explicit local detector-factory discovery for the focused telescope Geometry."""
import os
from pathlib import Path
from research_common import REPO


def geometry_environment(xml):
    env=os.environ.copy()
    if 'Local_SiTrackerEndcap2XY' in Path(xml).read_text():
        build=Path(env.get('TESTBENCH_BUILD_DIR',REPO/'build/local_eicrecon_external')).resolve()
        if not (build/'libLocalTelescopeGeometry.so').is_file():raise FileNotFoundError('Build local Geometry plugin and set TESTBENCH_BUILD_DIR: '+str(build))
        env['LD_LIBRARY_PATH']=str(build)+':'+env.get('LD_LIBRARY_PATH','')
    return env

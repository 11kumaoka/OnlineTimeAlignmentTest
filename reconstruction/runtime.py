"""Shared EICrecon environment setup; no reconstruction or detector algorithms."""
import os
from research_common import prefix


def runtime(build_dir):
    plugin = build_dir/'BeamTestReco.so'
    if not plugin.is_file(): raise FileNotFoundError(f'Build plugin first: {plugin}')
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(build_dir)+':'+str(prefix()/'lib')+':'+env.get('LD_LIBRARY_PATH','')
    env['JANA_PLUGIN_PATH'] = f'{build_dir}:/opt/local/lib/EICrecon/plugins:/opt/local/lib/JANA/plugins'
    return plugin, env

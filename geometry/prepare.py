"""Prepare and verify telescope Geometry without running Simulation."""
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from geometry.environment import geometry_environment
from research_common import REPO, cli_parser, run, stage, done, digest, write_json, execute

DEFAULT_NOMINAL = REPO/'geometry/nominal/seven_layer_telescope.xml'
DEFAULT_GEOMETRY_CONFIG = REPO/'geometry/scenarios/L2_x200um.json'

def ring(root, lid):
    det = root.find("./detectors/detector[@name='SiMAPS']")
    if det is None or det.get('type') not in ('DD4hep_SiTrackerEndcap2','Local_SiTrackerEndcap2XY'): raise ValueError('Unsupported detector builder')
    matches = det.findall(f"./layer[@id='{lid}']/ring")
    if len(matches)!=1 or matches[0].get('nmodules')!='1' or float(matches[0].get('phi0','0'))!=0:
        raise ValueError('Only a single phi0=0 SiMAPS module is supported')
    return matches[0]

def load_geometry_config(path, nominal_root):
    config = json.loads(path.read_text())
    if not isinstance(config, dict) or not {'detector','global_x_shifts_mm'} <= set(config) or set(config)-{'detector','global_x_shifts_mm','global_y_shifts_mm','global_rz_rad','global_z_shifts_mm','global_rx_rad','global_ry_rad'}:
        raise ValueError('Geometry scenario supports detector, Global X/Y/Z mm, and L1/L2/L3 Global Rx/Ry/Rz rad mappings only')
    if config['detector'] != 'SiMAPS' or not isinstance(config['global_x_shifts_mm'], dict):
        raise ValueError('Only a SiMAPS global_x_shifts_mm mapping is supported')
    if not isinstance(config.get('global_y_shifts_mm',{}),dict):raise ValueError('Expected a Global Y mapping')
    for key,value in config.get('global_y_shifts_mm',{}).items():
        if key not in {'1','2','3'} or type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Y translation supports finite SiMAPS L1/L2/L3 values only')
        if float(f'{value:.8f}')!=value:raise ValueError('Geometry shifts support at most eight decimal places in mm')
    if not isinstance(config.get('global_rz_rad',{}),dict):raise ValueError('Expected a Global Rz radian mapping')
    for key,value in config.get('global_rz_rad',{}).items():
        if key not in ('1','2','3') or type(value) not in (int,float) or not math.isfinite(value) or abs(value) > .1:
            raise ValueError('Experimental Rz supports only finite SiMAPS L1/L2/L3 angles within 0.1 rad')
        ring(nominal_root,int(key))
    if not isinstance(config.get('global_z_shifts_mm',{}),dict):raise ValueError('Expected a Global Z mapping')
    for key,value in config.get('global_z_shifts_mm',{}).items():
        if key not in ('1','2','3') or type(value) not in (int,float) or not math.isfinite(value) or abs(value)>10:
            raise ValueError('Global Z supports finite L1/L2/L3 displacements within 10 mm')
        if float(f'{value:.8f}')!=value:raise ValueError('Global Z supports eight decimal places in mm')
        ring(nominal_root,int(key))
    for axis in ('rx','ry'):
        values=config.get('global_'+axis+'_rad',{})
        if not isinstance(values,dict):raise ValueError('Expected a tilt mapping in radians')
        for key,value in values.items():
            if key not in ('1','2','3') or type(value) not in (int,float) or not math.isfinite(value) or abs(value)>.1:
                raise ValueError('Physical tilt preparation supports finite SiMAPS L1/L2/L3 angles within 0.1 rad only')
            ring(nominal_root,int(key))
    shifts = {}
    for key, value in config['global_x_shifts_mm'].items():
        if key not in {'0', '1', '2', '3', '4'}:
            raise ValueError(f'Unsupported SiMAPS layer identifier: {key}; expected 0..4')
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'Layer {key} shift must be a finite number in mm')
        if float(f'{value:.8f}') != value:
            raise ValueError('Geometry shifts support at most eight decimal places in mm')
        ring(nominal_root, int(key))
        shifts[int(key)] = float(value)
    return config, shifts


def write_shifted_xml(source, dest, shifts, y_shifts=None, rz_rad=None, z_shifts=None, rx_rad=None, ry_rad=None, rotations=None):
    text = Path(source).read_text()
    parsed = ET.fromstring(text)
    for layer in shifts:
        ring(parsed, layer)
    detector = re.search(r'<detector\b[^>]*name="SiMAPS"[\s\S]*?</detector>', text)
    if not detector:
        raise ValueError('SiMAPS XML block not found')
    block = detector.group()
    for layer, x_mm in sorted(shifts.items()):
        pattern = rf'(<layer\s+id="{layer}"[^>]*>[\s\S]*?<ring\b[^>]*\br=")[^"]*(")'
        block, count = re.subn(pattern, lambda match:match[1]+f'{-x_mm:.8f}*mm'+match[2], block)
        if count != 1:
            raise ValueError('Expected exactly one placement edit per requested layer')
    if y_shifts is not None:
        block=block.replace('type="DD4hep_SiTrackerEndcap2"','type="Local_SiTrackerEndcap2XY"')
        for layer,value in y_shifts.items():
            pattern=rf'(<layer\s+id="{layer}"[^>]*>[\s\S]*?<ring\b)([^>]*)(/>)'
            def place(match):
                attributes=re.sub(r'\s+global_y="[^"]*"','',match[2]).rstrip()
                return match[1]+attributes+f' global_y="{value:.8f}*mm"'+match[3]
            block,count=re.subn(pattern,place,block)
            if count!=1:raise ValueError('Expected exactly one Global Y placement edit')
    if rz_rad is not None:
        block=block.replace('type="DD4hep_SiTrackerEndcap2"','type="Local_SiTrackerEndcap2XY"')
        for layer,value in rz_rad.items():
            if layer not in (1,2,3) or not math.isfinite(value) or abs(value) > .1:
                raise ValueError('Only bounded SiMAPS L1/L2/L3 Global Rz is enabled')
            pattern=rf'(<layer\s+id="{layer}"[^>]*>[\s\S]*?<ring\b)([^>]*)(/>)'
            def rotate(match):
                attributes=re.sub(r'\s+global_rz="[^"]*"','',match[2]).rstrip()
                return match[1]+attributes+f' global_rz="{value:.14f}"'+match[3]
            block,count=re.subn(pattern,rotate,block)
            if count!=1:raise ValueError('Expected exactly one Global Rz placement edit')
    if z_shifts is not None:
        block=block.replace('type="DD4hep_SiTrackerEndcap2"','type="Local_SiTrackerEndcap2XY"')
        for layer,value in z_shifts.items():
            if layer not in (1,2,3) or not math.isfinite(value) or abs(value)>10:raise ValueError('Unsupported Global Z offset')
            pattern=rf'(<layer\s+id="{layer}"[^>]*>[\s\S]*?<ring\b)([^>]*)(/>)'
            def place_z(match):
                attributes=re.sub(r'\s+global_z="[^"]*"','',match[2]).rstrip()
                return match[1]+attributes+f' global_z="{value:.8f}*mm"'+match[3]
            block,count=re.subn(pattern,place_z,block)
            if count!=1:raise ValueError('Expected one independent Global Z placement edit')
    for axis,values in (('rx',rx_rad),('ry',ry_rad)):
        if values is None:continue
        block=block.replace('type="DD4hep_SiTrackerEndcap2"','type="Local_SiTrackerEndcap2XY"')
        for layer,value in values.items():
            if layer not in (1,2,3) or not math.isfinite(value) or abs(value)>.1:raise ValueError('Unsupported physical tilt placement')
            if any(f'global_r{i}{j}=' in block for i in range(3) for j in range(3)):raise ValueError('Use full-matrix composition for an existing matrix placement')
            pattern=rf'(<layer\s+id="{layer}"[^>]*>[\s\S]*?<ring\b)([^>]*)(/>)'
            def tilt(match):
                attributes=re.sub(r'\s+global_'+axis+r'="[^"]*"','',match[2]).rstrip()
                return match[1]+attributes+f' global_{axis}="{value:.17g}"'+match[3]
            block,count=re.subn(pattern,tilt,block)
            if count!=1:raise ValueError('Expected one physical tilt edit')
    if rotations is not None:
        from geometry.transforms import RigidTransform
        block=block.replace('type="DD4hep_SiTrackerEndcap2"','type="Local_SiTrackerEndcap2XY"')
        for layer,matrix in rotations.items():
            if layer not in (1,2,3):raise ValueError('Unsupported matrix placement layer')
            matrix=RigidTransform(rotation=matrix).rotation
            pattern=rf'(<layer\s+id="{layer}"[^>]*>[\s\S]*?<ring\b)([^>]*)(/>)'
            def rotate_matrix(match):
                attributes=re.sub(r'\s+global_r(?:x|y|z|[0-2][0-2])="[^"]*"','',match[2]).rstrip()
                return match[1]+attributes+''.join(f' global_r{i}{j}="{matrix[i][j]:.17g}"' for i in range(3) for j in range(3))+match[3]
            block,count=re.subn(pattern,rotate_matrix,block)
            if count!=1:raise ValueError('Expected one full-matrix placement edit')
    with Path(dest).open('x') as output:

        output.write(text[:detector.start()]+block+text[detector.end():])
    result = ET.parse(dest).getroot()
    for layer, x_mm in shifts.items():
        if ring(result, layer).get('r') != f'{-x_mm:.8f}*mm':
            raise ValueError(f'Incorrect XML placement for layer {layer}')


def modified_xml(source, dest, layer, x_mm):
    # Preserve the existing L2 correction's sign, precision, and nominal-based update.
    write_shifted_xml(source, dest, {layer: x_mm})


def gdml_positions(path):
    root = ET.parse(path).getroot()
    definition = root.find('define')
    if definition is None:
        raise ValueError('Unsupported GDML: missing placement definitions')
    scale = {'mm':1.0, 'cm':10.0, 'm':1000.0, 'um':0.001}
    def position(node):
        factor = scale[node.get('unit', 'mm')]
        return [float(node.get(axis, '0'))*factor for axis in ('x', 'y', 'z')]
    # This verifier is deliberately restricted to the current origin-centered hierarchy.
    for detector in ('SiMAPS', 'MPGDPlane', 'ACLGADPlane'):
        parents = [n for n in definition.findall('position')
                   if re.fullmatch(detector+r'_\d+inworld_volumepos', n.get('name', ''))]
        if len(parents) != 1 or any(abs(v)>1e-9 for v in position(parents[0])):
            raise ValueError('Unsupported translated detector parent in GDML')
        for rotation in definition.findall('rotation'):
            if re.fullmatch(detector+r'_\d+inworld_volumerot', rotation.get('name', '')):
                if any(float(rotation.get(axis, '0')) != 0 for axis in ('x', 'y', 'z')):
                    raise ValueError('Unsupported rotated detector parent in GDML')
    names = {layer:f'SiMAPSModule_{layer}inSiMAPSpos' for layer in range(5)}
    names.update({5:'MPGDModule_0inMPGDPlanepos', 6:'ACLGADModule_0inACLGADPlanepos'})
    result = {}
    for layer, name in names.items():
        nodes = definition.findall(f"position[@name='{name}']")
        if len(nodes) != 1:
            raise ValueError(f'Unsupported GDML module placement: {name}')
        result[layer] = position(nodes[0])
    return result


def verify_positions(directory, shifts, y_shifts=None, z_shifts=None):
    nominal = gdml_positions(directory/'nominal_qa/geometry.gdml')
    misaligned = gdml_positions(directory/'misaligned_qa/geometry.gdml')
    rows = []
    for layer in range(7):
        requested = shifts.get(layer, 0.0)
        expected = [nominal[layer][0]+requested, nominal[layer][1]+(y_shifts or {}).get(layer,0.),nominal[layer][2]+(z_shifts or {}).get(layer,0.)]
        if not all(math.isclose(a, b, rel_tol=0.0, abs_tol=1e-8)
                   for a, b in zip(misaligned[layer], expected)):
            raise ValueError(f'DD4hep placement does not match the requested Global X shift for L{layer}')
        rows.append({'layer':layer, 'nominal_xyz_mm':nominal[layer],
                     'misaligned_xyz_mm':misaligned[layer], 'requested_global_x_shift_mm':requested})
        if y_shifts:rows[-1]['requested_global_y_shift_mm']=y_shifts.get(layer,0.)
        if z_shifts:rows[-1]['requested_global_z_shift_mm']=z_shifts.get(layer,0.)
    write_json(directory/'placement_check.json', {'verified':True, 'source':'DD4hep geoConverter GDML module placements', 'layers':rows})


def prepare(a):
    nominal = a.nominal
    root = ET.parse(nominal).getroot()
    constant = root.find("./define/constant[@name='plane_ring_r']")
    if constant is None or constant.get('value') != '0*mm':
        raise ValueError('This backend requires the existing zero-centered nominal telescope')
    for layer in range(5):
        if ring(root, layer).get('r') != 'plane_ring_r':
            raise ValueError('This backend requires the existing zero-centered nominal telescope')
    config, shifts = load_geometry_config(a.geometry_config, root)
    a.run_dir.mkdir(parents=True, exist_ok=True)
    p = stage(a.run_dir, 'step1')
    shutil.copyfile(nominal, p/'nominal.xml')
    write_json(p/'geometry_config.json', config)
    y_shifts={int(k):v for k,v in config.get('global_y_shifts_mm',{}).items()}
    write_shifted_xml(nominal, p/'misaligned.xml', shifts, y_shifts if 'global_y_shifts_mm' in config else None, {int(k):v for k,v in config['global_rz_rad'].items()} if 'global_rz_rad' in config else None, {int(k):v for k,v in config['global_z_shifts_mm'].items()} if 'global_z_shifts_mm' in config else None, rx_rad={int(k):v for k,v in config.get('global_rx_rad',{}).items()} or None, ry_rad={int(k):v for k,v in config.get('global_ry_rad',{}).items()} or None)
    for name in ('nominal', 'misaligned'):
        qa = p/(name+'_qa'); qa.mkdir()
        execute(['geoConverter', '-compact2gdml', '-input', p/(name+'.xml'), '-output', qa/'geometry.gdml'], qa,env=geometry_environment(p/(name+'.xml')))
    verify_positions(p, shifts,y_shifts,{int(k):v for k,v in config.get('global_z_shifts_mm',{}).items()})
    version = {}
    for key in ['Acts', 'DD4hep', 'EICrecon', 'JANA']:
        path = Path('/opt/local/include')/key
        if path.exists():
            version[key] = str(path.resolve())
    done(p, nominal_sha256=digest(nominal), source=str(nominal), installed_paths=version,
         geometry_config_source=str(a.geometry_config), geometry_config_sha256=digest(a.geometry_config),
         git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
         git_status=subprocess.check_output(['git','status','--short'],cwd=REPO,text=True),
         dirty_plugin_sources={str(q.relative_to(REPO)):digest(q) for q in (REPO/'localDetEICrecon').rglob('*') if q.is_file() and q.suffix in {'.h','.cc','.txt','.py'}},
         image=os.environ.get('TESTBENCH_IMAGE','record image ID on host: docker image inspect'))


if __name__ == '__main__':
    parser = cli_parser(__doc__)
    parser.add_argument('--nominal', type=Path, default=DEFAULT_NOMINAL, help='Nominal telescope XML; copied without modification')
    parser.add_argument('--geometry-config', type=Path, default=DEFAULT_GEOMETRY_CONFIG,
                        help='SiMAPS Global X and optional L1/L2/L3 Global Y/Z/Rx/Ry/Rz physical scenario (mm/rad); independent of beam/reconstruction settings')
    run(prepare, parser)

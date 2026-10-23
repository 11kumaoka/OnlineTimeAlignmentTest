"""Validated correction scopes for the existing SiMAPS telescope model."""
import xml.etree.ElementTree as ET
from geometry.placements import geometry

# Coupled modes use a full matrix state and left Global SO(3) increments.
SO3_SCOPES={
    'l1_rotations': (1,), 'l1_l2_rotations': (1,2),
    'l1_six_dof': (1,), 'l1_l2_six_dof': (1,2),
    'l3_six_dof': (3,), 'l1_l2_l3_six_dof': (1,2,3),
}
SO3_MODES=tuple(SO3_SCOPES)


def fixed_layers_for(mode):
    """Fixed SiMAPS references; MPGD/AC-LGAD are never alignment measurements."""
    return tuple(l for l in range(5) if l not in layers_for(mode))


def selected_labels(mode):
    return tuple(family+l for l in layers_for(mode) for _,family,_ in parameter_spec(mode))

def parameter_spec(mode):
    axes=axes_for(mode)
    return tuple((axis,label,sign) for axis,label,sign in
        (('x',1000,-1),('y',2000,-1),('z',4000,1),('rx',5000,1),('ry',6000,1),('rz',3000,-1)) if axis in axes)



def layers_for(mode):
    if mode in SO3_MODES:return SO3_SCOPES[mode]
    if mode in ('l1_rx_ry','l1_l2_rx_ry'):
        raise ValueError('Combined Rx/Ry disabled after failed finite-rotation closure; see docs/TILT_ALIGNMENT_VALIDATION.md')
    if mode in ('l1_rx','l1_ry','l1_rx_ry','l1_rz','l1_z'):return (1,)
    if mode=='l2_x':return (2,)
    if mode in ('l1_l2_rx_ry','l1_l2_x','l1_l2_xy','l1_l2_rz','l1_l2_xy_rz','l1_l2_z','l1_l2_xyz'):return (1,2)
    raise ValueError('Unsupported correction mode; use explicit validated X/Y/Rz or l1_z/l1_l2_z/l1_l2_xyz scope')


def verify_scope(nominal,other,layers,axes=('x',)):
    if 'rx' in axes or 'ry' in axes:
        from geometry.placements import placement_transforms
        from geometry.transforms import multiply,transpose,axis_rotation
        import math
        a,b=placement_transforms(nominal),placement_transforms(other)
        for l in layers:
            for i,axis in enumerate('xyz'):
                if axis not in axes and abs(a[l].translation[i]-b[l].translation[i])>1e-12:
                    raise ValueError('Translation exceeds selected rotation scope')
            q=multiply(b[l].rotation,transpose(a[l].rotation))
            if len(axes)==1:
                axis=axes[0][-1];angle=math.atan2(q[2][1],q[1][1]) if axis=='x' else math.atan2(q[0][2],q[0][0])
                expected=axis_rotation(axis,angle)
                if any(abs(q[i][j]-expected[i][j])>1e-12 for i in range(3) for j in range(3)):raise ValueError('Rotation exceeds selected Global tilt scope')
    roots=[ET.parse(p).getroot() for p in (nominal,other)]
    for root in roots:
        if 'y' in axes or 'rz' in axes or 'z' in axes or 'rx' in axes or 'ry' in axes:
            detector=root.find("./detectors/detector[@name='SiMAPS']")
            if detector.get('type') not in ('DD4hep_SiTrackerEndcap2','Local_SiTrackerEndcap2XY'):raise ValueError('Unsupported detector builder')
            detector.set('type','DD4hep_SiTrackerEndcap2')
        for layer in layers:
            node=root.find(f"./detectors/detector[@name='SiMAPS']/layer[@id='{layer}']/ring")
            if node is None:raise ValueError('Missing supported SiMAPS placement')
            if 'rx' in axes or 'ry' in axes:
                for key in list(node.attrib):
                    if key in ('global_rx','global_ry','global_rz') or key in {f'global_r{i}{j}' for i in range(3) for j in range(3)}:node.attrib.pop(key)
            if 'x' in axes:node.set('r','SUPPORTED_X')
            if 'rz' in axes:node.attrib.pop('global_rz',None)
            if 'z' in axes:node.attrib.pop('global_z',None)
            if 'y' in axes or 'rz' in axes or 'z' in axes:node.attrib.pop('global_y',None)
    if ET.tostring(roots[0])!=ET.tostring(roots[1]):
        raise ValueError('Geometry differences exceed the selected SiMAPS correction scope')
    geometry(other)


def axes_for(mode):
    layers_for(mode)
    if mode in SO3_MODES:return ('x','y','z','rx','ry','rz') if mode.endswith('six_dof') else ('rx','ry','rz')
    if mode in ('l1_rx_ry','l1_l2_rx_ry'):return ('rx','ry')
    if mode=='l1_rx':return ('rx',)
    if mode=='l1_ry':return ('ry',)
    if mode in ('l1_rz','l1_l2_rz'):return ('rz',)
    if mode in ('l1_z','l1_l2_z'):return ('z',)
    if mode=='l1_l2_xyz':return ('x','y','z')
    if mode=='l1_l2_xy_rz':return ('x','y','rz')
    return ('x','y') if mode=='l1_l2_xy' else ('x',)


def verify_survey(nominal,survey,rotation_layers=(),orientation_layers=()):
    """Allow surveyed centers and explicitly selected Rz while retaining the validated hierarchy/readout."""
    roots=[ET.parse(path).getroot() for path in (nominal,survey)]
    for root in roots:
        for detector in root.findall('./detectors/detector'):
            if detector.get('name') not in ('SiMAPS','MPGDPlane','ACLGADPlane'):continue
            if detector.get('name')=='SiMAPS':
                if detector.get('type') not in ('DD4hep_SiTrackerEndcap2','Local_SiTrackerEndcap2XY'):raise ValueError('Unsupported survey builder')
                detector.set('type','DD4hep_SiTrackerEndcap2')
            for layer in detector.findall('layer'):
                for ring in layer.findall('ring'):
                    for attr in ('r','zstart','dz'):ring.set(attr,'SURVEY_CENTER')
                    if detector.get('name')=='SiMAPS':
                        ring.attrib.pop('global_y',None)
                        ring.attrib.pop('global_z',None)
                        if int(layer.get('id')) in rotation_layers:ring.attrib.pop('global_rz',None)
                        if int(layer.get('id')) in orientation_layers:
                            for key in list(ring.attrib):
                                if key in ('global_rx','global_ry','global_rz') or key in {f'global_r{i}{j}' for i in range(3) for j in range(3)}:ring.attrib.pop(key)
    if ET.tostring(roots[0])!=ET.tostring(roots[1]):raise ValueError('Survey exceeds supported center-placement representation')
    geometry(survey)

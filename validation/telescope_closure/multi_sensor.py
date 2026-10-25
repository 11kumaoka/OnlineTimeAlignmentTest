"""Bounded L1/L2 selection and geometry checks using the existing native model."""
import math


def is_multi(mode):
    return mode in ('l1_y_rx_ry_rz_l2_y','l1_y_rx_ry_rz_l2_y_negative','l1_l2_y_rx_ry_rz','l1_l2_y_rx_ry_rz_negative')


def labels(mode):
    if not is_multi(mode):raise ValueError('Unsupported multi-sensor scope')
    selected=[700102,700104,700105,700106,700202]
    return selected+[700204,700205,700206] if mode.startswith('l1_l2_') else selected


def mapping(label):
    table={700102:(1,1),700104:(1,3),700105:(1,4),700106:(1,5),700202:(2,1),700204:(2,3),700205:(2,4),700206:(2,5)}
    if label not in table:raise ValueError('Unsupported physical parameter label')
    return table[label]


def fixture(mode):
    labels(mode)
    sign=-1 if mode.endswith('_negative') else 1
    rotations={1:[sign*v for v in (.001,.0005,-.0005)]}
    if mode.startswith('l1_l2_'):rotations[2]=[sign*v for v in (-.0012,.0006,.0006)]
    return {1:.080,2:-.060},rotations


def pose_increments(values):
    shifts={};rotations={}
    for label,value in values.items():
        layer,column=mapping(int(label))
        if not math.isfinite(value):raise ValueError('Nonfinite physical update')
        if column==1:shifts[layer]=value
        else:rotations.setdefault(layer,[None,None,None])[column-3]=value
    if any(any(v is None for v in w) for w in rotations.values()):
        raise ValueError('A selected SO(3) update requires all three components')
    return shifts,rotations


def injection(mode):
    shifts,rotations=fixture(mode)
    return {k:(shifts[layer] if column==1 else rotations[layer][column-3])
            for k in labels(mode) for layer,column in [mapping(k)]}


def xml_identity(parent,candidate,selected):
    """Whitelist placed component position/orientation; preserve every other node."""
    import copy
    import xml.etree.ElementTree as ET
    def structure(n):return n.tag,dict(n.attrib),(n.text or '').strip(),tuple(structure(c) for c in n)
    a=ET.parse(parent).getroot();b=ET.parse(candidate).getroot()
    da=a.find("./detectors/detector[@name='SiMAPS']");db=b.find("./detectors/detector[@name='SiMAPS']")
    for layer in sorted({mapping(k)[0] for k in selected}):
        la=da.find(f"./layer[@id='{layer}']");lb=db.find(f"./layer[@id='{layer}']")
        reference=da.find(f"./module[@name='{la.get('module')}']")
        module=db.find(f"./module[@name='{lb.get('module')}']")
        normalized=copy.deepcopy(module);normalized.set('name',reference.get('name'))
        normalized.find('./module_component/position').set('x',reference.find('./module_component/position').get('x'))
        if any(mapping(k)==(layer,3) for k in selected):
            for key in 'xyz':normalized.find('./module_component/rotation').set(key,reference.find('./module_component/rotation').get(key))
        assert structure(normalized)==structure(reference)
        db.remove(module);lb.set('module',la.get('module'))
    assert structure(a)==structure(b)


def pose_gate(args):
    """Real-constructor simultaneous left composition and inverse, both sensors."""
    import json
    import numpy as np
    from research_common import stage,execute,done,write_json
    from validation.telescope_closure.closure import displaced_xml,environment
    from validation.telescope_closure.rotation import pose_checks
    p=stage(args.result,'coupled_pose')
    base=json.loads((args.result/'data/control/channels_truth.json').read_text())['sensors']
    shifts,rotations=fixture(args.mode)
    truth=json.loads((args.result/'data/shifted/channels_truth.json').read_text())['sensors']
    pose_checks(base,truth,shifts,rotations,axis='xyz')
    parent=args.result/'geometry/fixtures/nominal.xml';previous=base
    cross_shifts={1:-.015,2:.020};cross_rotations={1:[-.0003,.0004,.0002]}
    if 2 in rotations:cross_rotations[2]=[.0002,-.0003,.0004]
    chain=[(shifts,rotations),(cross_shifts,cross_rotations),
           ({l:-v for l,v in cross_shifts.items()},{l:[-v for v in w] for l,w in cross_rotations.items()}),
           ({l:-v for l,v in shifts.items()},{l:[-v for v in w] for l,w in rotations.items()})]
    for i,(dy,dw) in enumerate(chain):
        q=stage(p,'pose_'+str(i));displaced_xml(parent,q/'geometry.xml',dy,rotations=dw,rotation_axis='xyz')
        execute([args.build/'TelescopeChannels',q/'geometry.xml',0,q/'geometry.json'],q,env=environment(args.build))
        actual=json.loads((q/'geometry.json').read_text())['sensors'];pose_checks(previous,actual,dy,dw,axis='xyz')
        xml_identity(parent,q/'geometry.xml',labels(args.mode));previous=actual;parent=q/'geometry.xml'
    for a,b in zip(base,actual):
        np.testing.assert_allclose(b['center_mm'],a['center_mm'],atol=1e-9,rtol=0)
        np.testing.assert_allclose(b['acts_rotation'],a['acts_rotation'],atol=2e-12,rtol=0)
    write_json(p/'report.json',{'passed':True,'independent_sensor_updates':True,'left_global_composition_and_inverse':True,'geometry_activated':False})
    done(p,passed=True)

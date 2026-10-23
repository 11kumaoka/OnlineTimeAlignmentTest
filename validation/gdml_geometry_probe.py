"""Import exported GDML in a fresh ROOT process and verify actual module matrices."""
import argparse
from array import array
from pathlib import Path
import re
import ROOT
import numpy as np
from geometry.placements import placement_transforms
from research_common import write_json


def validate(a):
    ROOT.TGeoManager.SetDefaultUnits(ROOT.TGeoManager.kG4Units)
    manager=ROOT.TGeoManager.Import(str(a.gdml.resolve()))
    if not manager:raise RuntimeError('ROOT GDML import failed')
    expected=placement_transforms(a.geometry);found={}
    def walk(node,parent):
        transform=ROOT.TGeoHMatrix(parent);transform.Multiply(node.GetMatrix())
        name=node.GetName();match=re.match(r'SiMAPSModule_(\d+)(?:_|$)',name)
        layer=int(match[1]) if match else (5 if re.match(r'MPGDModule_0(?:_|$)',name) else (6 if re.match(r'ACLGADModule_0(?:_|$)',name) else None))
        if layer is not None:
            def world(point):
                output=array('d',[0.,0.,0.]);transform.LocalToMaster(array('d',point),output)
                return np.asarray(output)
            center=world((0,0,0));sensor=[world(p)-center for p in [(1,0,0),(0,1,0),(0,0,1)]]
            plane=np.column_stack((-sensor[2],sensor[0],np.cross(-sensor[2],sensor[0])))
            target=expected[layer]
            if not np.allclose(center,target.translation,rtol=0,atol=1e-8):raise AssertionError('GDML sensitive-center mismatch')
            if not np.allclose(plane,target.rotation,rtol=0,atol=1e-10):raise AssertionError('GDML plane orientation mismatch')
            if layer in found:raise AssertionError('Duplicate telescope module')
            found[layer]={'center_mm':center.tolist(),'plane_rotation':plane.tolist()}
        for index in range(node.GetNdaughters()):walk(node.GetDaughter(index),transform)
    walk(manager.GetTopNode(),ROOT.TGeoHMatrix())
    if set(found)!=set(range(7)):raise AssertionError('Missing telescope modules in GDML')
    report={'passed':True,'units':'ROOT kG4Units: mm','layers':found,'matrix_tolerance':1e-10,'center_tolerance_mm':1e-8}
    tolerance=getattr(a,'check_overlaps_mm',None)
    if tolerance is not None:
        import math
        if not math.isfinite(tolerance) or tolerance<=0:raise ValueError('Expected a positive overlap tolerance in mm')
        manager.CheckOverlaps(tolerance)
        count=manager.GetListOfOverlaps().GetEntries()
        report.update(overlap_tolerance_mm=tolerance,overlap_or_extrusion_count=count,passed=count==0)
    write_json(a.output,report)
    if not report['passed']:raise ValueError('Physical overlaps or extrusions detected')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('geometry','gdml','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--check-overlaps-mm',type=float,help='Optional independent ROOT overlap/extrusion check in mm')
    validate(parser.parse_args())

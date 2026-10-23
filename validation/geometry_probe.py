"""Fresh-process DD4hep positions, sensor bases and Cell ID samples for geometry validation."""
import argparse,json
from pathlib import Path

def probe(xml,reco=None,log_path=None,track_points=False):
    import ROOT,dd4hep
    ROOT.gSystem.Load('libDDRec')
    if 'Local_SiTrackerEndcap2XY' in xml.read_text():
        import os
        from research_common import REPO
        library=Path(os.environ.get('TESTBENCH_BUILD_DIR',REPO/'build/local_eicrecon_external'))/'libLocalTelescopeGeometry.so'
        if ROOT.gSystem.Load(str(library.resolve()))<0:raise RuntimeError('Cannot load local XY detector factory')
    detector=dd4hep.Detector.getInstance();detector.fromXML(str(xml))
    detector.apply('DD4hepVolumeManager',0,ROOT.nullptr)
    converter=ROOT.dd4hep.rec.CellIDPositionConverter(detector)
    scale=ROOT.dd4hep.mm
    def xyz(p):return [p.x()/scale,p.y()/scale,p.z()/scale]
    layers={};samples={}
    for layer in range(7):
        system=31 if layer<5 else (100 if layer==5 else 92)
        cell=system|(1<<8)|(layer<<11)|(1<<22)|(1<<28)
        context=converter.findContext(cell)
        origin=xyz(context.localToWorld(ROOT.dd4hep.Position(0,0,0)))
        basis=[]
        for point in [(scale,0,0),(0,scale,0),(0,0,scale)]:
            world=xyz(context.localToWorld(ROOT.dd4hep.Position(*point)))
            basis.append([world[i]-origin[i] for i in range(3)])
        layers[str(layer)]={'center_mm':origin,'sensor_basis_columns':basis}
        if layer in (1,2,3):
            for x,z in [(-300,120),(0,0),(175,-240)]:
                identifier=cell|((x&65535)<<32)|((z&65535)<<48)
                samples[f'L{layer}_{x}_{z}']=xyz(converter.position(identifier))
    report={'layers':layers,'samples':samples}
    if log_path:
        import re,numpy as np
        text=log_path.read_text();checked=[]
        for match in re.finditer(r'BeamTestGeometry layer=(\d+) center_mm=(.*?) u=(.*?) v=(.*?) n=(.*?)$',text,re.M):
            layer,center,u,v,n=match.groups();context=layers[layer]
            actual=[list(map(float,values.split())) for values in (center,u,v,n)]
            columns=np.asarray(context['sensor_basis_columns'])
            expected=[context['center_mm'],-columns[2],columns[0],np.cross(-columns[2],columns[0])]
            if not np.allclose(actual[0],expected[0],rtol=0,atol=1e-6):raise AssertionError('Surface center/log mismatch')
            if not np.allclose(actual[1:],expected[1:],rtol=0,atol=1e-12):raise AssertionError('Surface orientation mismatch')
            checked.append(int(layer))
        if sorted(set(checked))!=list(range(7)):raise AssertionError('Missing actual selected-Geometry surface diagnostics')
        errors=re.findall(r'ACTSGeometryCheck layer=(\d+) round_trip_error_mm=(\S+)',text)
        actual_layers=[int(layer) for layer,_ in errors]
        # Mille also reads the shared placement helper; it does not construct ACTS surfaces.
        from collections import Counter
        counts=Counter(actual_layers)
        if set(counts)!=set(range(7)) or len(set(counts.values()))!=1 or any(float(e)>1e-10 for _,e in errors):raise AssertionError('ACTS round-trip checks missing/failed')
        extra=Counter(checked)-counts
        if extra and (set(extra)!=set(range(7)) or set(extra.values())!={1} or not any(mode in text for mode in ('l1_rz','l1_l2_rz','l1_l2_xy_rz'))):raise AssertionError('Unexplained placement diagnostics without actual ACTS checks')
        report['acts_layers_verified']=sorted(set(checked));report['surface_instances_checked']=len(errors)
        report['placement_context_instances_checked']=len(checked)
    if reco:
        import uproot,awkward as ak,numpy as np
        with uproot.open(reco) as file:
            tree=file['events']
            branch=lambda coll,field:ak.to_list(tree[f'{coll}/{coll}.{field}'].array())
            ids=branch('LocalSiMAPSRecHits','cellID')
            positions=[branch('LocalSiMAPSRecHits','position.'+axis) for axis in 'xyz']
            count=0
            for event,identifiers in enumerate(ids):
                for hit,identifier in enumerate(identifiers):
                    expected=xyz(converter.position(identifier))
                    for index in range(3):
                        if float(np.float32(expected[index]))!=positions[index][event][hit]:raise AssertionError('RecHit differs from fresh DD4hep position')
                    count+=1
            surfaces=branch('LocalBeamTestFitMeasurements','surface')
            coordinates=[branch('LocalBeamTestFitMeasurements','loc.'+axis) for axis in ('a','b')]
            unique=sorted({value for event in surfaces for value in event})
            if len(unique)!=5:raise AssertionError('Expected the five selected SiMAPS surfaces')
            surface_layers={value:layer for layer,value in enumerate(unique)}
            hit_var=[branch('LocalSiMAPSRecHits','positionError.'+axis) for axis in ('xx','yy')]
            measurement_var=[branch('LocalBeamTestFitMeasurements','covariance.'+axis) for axis in ('xx','yy','xy')]
            local_count=0
            for event,event_surfaces in enumerate(surfaces):
                for index,surface in enumerate(event_surfaces):
                    layer=surface_layers[surface]
                    choices=[i for i,value in enumerate(ids[event]) if ((value>>11)&63)==layer]
                    if len(choices)!=1:raise AssertionError('Ambiguous associated RecHit in accepted track')
                    hit=choices[0];center=layers[str(layer)]['center_mm']
                    columns=np.asarray(layers[str(layer)]['sensor_basis_columns'])
                    offset=np.asarray([positions[j][event][hit]-center[j] for j in range(3)])
                    for axis,basis in enumerate((-columns[2],columns[0])):
                        expected=float(np.float32(np.dot(offset,basis)))
                        actual=coordinates[axis][event][index]
                        if abs(expected-actual)>2*abs(float(np.spacing(np.float32(expected))))+1e-12:raise AssertionError('Measurement2D local coordinate mismatch')
                    expected_cov=[hit_var[1][event][hit],hit_var[0][event][hit],0.]
                    if [v[event][index] for v in measurement_var]!=expected_cov:raise AssertionError('Sensor X/Z to ACTS u/v covariance mismatch')
                    local_count+=1
            report['rechits_exact_float32']=count;report['measurement2d_local_checks']=local_count;report['measurement_covariance_checks']=local_count
            if track_points:
                checked_points={}
                for family in ('Predicted','Filtered','Smoothed'):
                    coll='_LocalBeamTest'+family+'Segments_points';meas='LocalBeamTest'+family+'Measurements'
                    point_surfaces=branch(coll,'surface');point_layers=branch(coll,'system')
                    point_xyz=[branch(coll,'position.'+axis) for axis in 'xyz']
                    point_cov=[branch(coll,'positionError.'+axis) for axis in ('xx','yy','zz','xy','xz','yz')]
                    measurement_surfaces=branch(meas,'surface');cov=[branch(meas,'covariance.'+axis) for axis in ('xx','yy','xy')]
                    total=0;max_distance=0.;max_covariance_error=0.;max_quantization_fraction=0.
                    for event,event_points in enumerate(point_surfaces):
                        for index,surface in enumerate(event_points):
                            layer=point_layers[event][index];context=layers[str(layer)]
                            basis=np.array(context['sensor_basis_columns']);uv=np.column_stack((-basis[2],basis[0]));normal=np.cross(uv[:,0],uv[:,1])
                            point=np.array([v[event][index] for v in point_xyz]);distance=abs(float(np.dot(normal,point-np.array(context['center_mm']))))
                            bound=2*float(np.dot(np.abs(normal),np.spacing(np.maximum(np.abs(point),1.).astype(np.float32))))+1e-9
                            if distance>bound:raise AssertionError('Stored ACTS intersection is off the selected sensitive plane')
                            matches=[j for j,value in enumerate(measurement_surfaces[event]) if value==surface]
                            if len(matches)!=1:raise AssertionError('Missing unique Measurement2D for stored track point')
                            j=matches[0];xx,yy,xy=[v[event][j] for v in cov];local=np.array([[xx,xy],[xy,yy]])
                            xx,yy,zz,xy,xz,yz=[v[event][index] for v in point_cov]
                            actual=np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]]);expected=uv@local@uv.T
                            # Both matrices were independently rounded to EDM float32. Propagate
                            # local half-ULPs through the rotation, including cancellation.
                            local_half_ulp=.5*np.abs(np.spacing(local.astype(np.float32))).astype(float)
                            output_half_ulp=.5*np.abs(np.spacing(actual.astype(np.float32))).astype(float)
                            bound=np.abs(uv)@local_half_ulp@np.abs(uv).T+output_half_ulp
                            bound+=4e-12*max(float(np.max(np.abs(local))),1e-12)
                            error=np.abs(actual-expected)
                            if np.any(error>bound):raise AssertionError(f'TrackPoint Global XYZ covariance mismatch beyond propagated float32 rounding: {family} event={event} layer={layer} actual={actual.tolist()} expected={expected.tolist()} bound={bound.tolist()}')
                            max_quantization_fraction=max(max_quantization_fraction,float(np.max(error/bound)))
                            total+=1;max_distance=max(max_distance,distance);max_covariance_error=max(max_covariance_error,float(np.max(np.abs(actual-expected))))
                    if total!=local_count:raise AssertionError('Missing predicted/filtered/smoothed intersections')
                    checked_points[family]={'points':total,'max_plane_distance_mm':max_distance,'max_global_covariance_error_mm2':max_covariance_error,'max_fraction_of_propagated_float32_bound':max_quantization_fraction}
                report['track_point_geometry_and_covariance_checks']=checked_points
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--geometry',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reco',type=Path);parser.add_argument('--log',type=Path)
    parser.add_argument('--check-track-points',action='store_true',help='Validate post-fit Global XYZ point covariance and actual intersections; requires the corrected diagnostic serializer')
    args=parser.parse_args()
    with args.output.open('x') as output:json.dump(probe(args.geometry.resolve(),args.reco,args.log,args.check_track_points),output,indent=2)

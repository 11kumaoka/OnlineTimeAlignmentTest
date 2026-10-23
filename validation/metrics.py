"""Numerical residual and Closure metrics; no ROOT rendering dependency."""
import json
import math
import awkward as ak
import numpy as np
import uproot
from geometry.placements import geometry

def root_branch(tree, coll, field):
    key = f"{coll}/{coll}.{field}"
    if key not in tree:
        raise RuntimeError(f"Missing PODIO branch {key}")
    return tree[key].array(library="ak")


def measurements(path, sim_path=None):
    """Keep historical pooled means AND uniquely matched per-hit distributions."""
    with uproot.open(path) as f, uproot.open(sim_path or path) as sf:
        t = f["events"]
        st = sf["events"]
        if sim_path:
            for field in ('runNumber','eventNumber'):
                if ak.to_list(root_branch(t,'EventHeader',field)) != ak.to_list(root_branch(st,'EventHeader',field)):
                    raise RuntimeError('Simulation/RawHit event identifiers differ; no positional truth matching is allowed')
        sc = root_branch(st, "SiMAPSHits", "cellID")
        rc = root_branch(t, "LocalSiMAPSRecHits", "cellID")
        coords = {a: (root_branch(st,"SiMAPSHits","position."+a),
                      root_branch(t,"LocalSiMAPSRecHits","position."+a)) for a in ("x","y")}
        chi2 = root_branch(t, "LocalBeamTestTracks", "chi2")
        ndf = root_branch(t, "LocalBeamTestTracks", "ndf")
    sl, rl = (sc >> 11) & 63, (rc >> 11) & 63
    result = {"events":len(sc), "tracks":int(ak.sum(ak.num(chi2))),
              "chi2":float(ak.sum(chi2)), "stored_ndf":float(ak.sum(ndf))}
    if result["stored_ndf"]<=0: raise RuntimeError("No fitted track dimensions")
    result["chi2ndf"]=result["chi2"]/result["stored_ndf"]
    for axis,(sim,rec) in coords.items():
        pairs=[[] for _ in range(5)]; pooled=[]; skipped=[]
        for layer in range(5):
            sv=ak.to_numpy(ak.flatten(sim[sl==layer]));rv=ak.to_numpy(ak.flatten(rec[rl==layer]))
            if not len(sv) or not len(rv):raise RuntimeError("Empty layer")
            pooled.append(float(1000*(rv.mean()-sv.mean())))
            excluded=0
            for ev in range(len(sc)):
                a=ak.to_numpy(sim[ev][sl[ev]==layer]);b=ak.to_numpy(rec[ev][rl[ev]==layer])
                if len(a)==len(b)==1:pairs[layer].append(float(1000*(b[0]-a[0])))
                else:excluded+=1
            if not pairs[layer]:raise RuntimeError("No unique hit pairs")
            skipped.append(excluded)
        result["deltas" if axis=="x" else "deltas_y"]=[np.asarray(v) for v in pairs]
        result["pooled_mean_"+axis+"_um"]=pooled
        result["excluded_"+axis+"_by_layer"]=skipped
    result["skipped"]=sum(result["excluded_x_by_layer"])
    return result


def mean_error(a):
    return float(a.mean()), float(a.std(ddof=1) / math.sqrt(len(a))) if len(a)>1 else 0.


def serializable(data):
    return {k: ([a.tolist() for a in v] if k in ("deltas","deltas_y") else v) for k,v in data.items()}


def calculate(args):
    nominal,simulated,corrected=[geometry(getattr(args,k)) for k in ("nominal","misaligned","corrected")]
    before,after=measurements(args.before,getattr(args,'simulation',None)),measurements(args.after,getattr(args,'simulation',None))
    bias=None
    for line in args.pede.read_text().splitlines():
        fields=line.split()
        if fields and fields[0]=="1002":bias=float(fields[1])*1000
    if bias is None:raise RuntimeError("Missing L2 pede bias")
    applied=(corrected[2][0]-nominal[2][0])*1000
    if abs(applied+bias)>0.01:raise RuntimeError("Geometry/pede correction sign mismatch")
    summary={"before":serializable(before),"after":serializable(after),
             "pede_l2_bias_um":bias,"applied_geometry_correction_um":applied,
             "note":"Geometry update step, not internal pede iteration. stored ACTS nDoF convention retained.",
             "metric_definition":"Historical pooled Rec mean minus Sim mean; per-hit plots use unique event/layer pairs."}
    if getattr(args,'correction_mode','l2_x') in ('l1_l2_x','l1_l2_xy','l1_l2_xy_rz'):
        from alignment.align import read_pede
        parameters=read_pede(args.pede)
        applied_by_layer={str(layer):(corrected[layer][0]-nominal[layer][0])*1000 for layer in (1,2)}
        for layer in (1,2):
            if abs(applied_by_layer[str(layer)]+1000*parameters[1000+layer])>0.01:
                raise RuntimeError('Geometry/pede correction sign mismatch for L'+str(layer))
        summary['applied_geometry_correction_um_by_layer']=applied_by_layer
        summary['correction_mode']=args.correction_mode
        if args.correction_mode in ('l1_l2_xy','l1_l2_xy_rz'):
            from geometry.placements import placement_transforms
            transforms=placement_transforms(args.corrected);original=placement_transforms(args.nominal)
            components={}
            for layer in (1,2):
                for index,axis,label in [(0,'x',1000+layer),(1,'y',2000+layer)]:
                    value=1000*(transforms[layer].translation[index]-original[layer].translation[index])
                    if abs(value+1000*parameters[label])>.01:raise RuntimeError('X/Y Geometry/pede sign mismatch')
                    components[f'L{layer}_{axis}']=value
            summary['applied_geometry_correction_um_by_component']=components
        if args.reference:raise ValueError('Historical L2-only reference cannot validate a two-layer sample')
    if 'rz' in getattr(args,'correction_mode','l2_x'):
        from geometry.placements import placement_transforms
        from correction.scope import layers_for
        from alignment.align import read_pede
        rotations={}
        for layer in layers_for(args.correction_mode):
            transforms=[placement_transforms(p)[layer] for p in (args.nominal,args.misaligned,args.corrected)]
            angles=[math.atan2(t.rotation[1][0],t.rotation[0][0]) for t in transforms]
            update=angles[2]-angles[0]
            if abs(update+read_pede(args.pede)[3000+layer])>1e-12:raise RuntimeError('Rotation/pede sign mismatch')
            rotations[str(layer)]={'layer':layer,'axis':'Global +Z','pivot_mm':list(transforms[0].translation),
                'reference_rad':angles[0],'simulation_rad':angles[1],'corrected_rad':angles[2],'update_rad':update}
        summary['rotation_by_layer']=rotations
        summary['rotation']=rotations['1']
        summary['correction_mode']=args.correction_mode
        if args.reference:raise ValueError('Historical translation reference does not validate rotation')
    if args.reference:
        ref=json.loads(args.reference.read_text());checks=[]
        for side in ("before","after"):
            d=summary[side];target=ref[side]
            checks.extend([d["tracks"]==target["tracks"],d["events"]==target["events"],
                           abs(d["pooled_mean_x_um"][2]-target["l2_mean_um"])<=ref["tolerance_residual_um"],
                           abs(d["chi2ndf"]-target["chi2ndf"])<=ref["tolerance_chi2ndf"]])
        checks.append(abs(applied-ref["correction_um"])<=ref["tolerance_correction_um"])
        summary["reference_passed"]=all(checks)
    return summary

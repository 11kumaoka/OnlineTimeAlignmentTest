# Geometry and measurement conventions

## Baseline audit before changing the interface

The validated L1/L2 X baseline used `DD4hep_SiTrackerEndcap2` with one module per ring and phi0=0. The builder places the module center at `(-r,0,zstart+dz)`; changing ring radius changes Global X with the opposite sign. Sensor-local axes, measured from installed DD4hep 1.36 VolumeManager contexts, are **sensor X → global Y, sensor Y → −global Z, sensor Z → −global X**. SiMAPS uses CartesianGridXZ: channel x maps to global Y and channel z maps to −global X. These are not interchangeable names.

RecHits use DDRec CellIDPositionConverter positions from the loaded reconstruction Geometry; their variance entries describe the sensor's segmentation axes. Previously ACTS constructed fixed identity-oriented planes at (0,0,z), then projected global RecHits into those planes. Translation-only data could therefore align successfully while the surface centers remained nominal. Mille Writer operates on global RecHit x/y/z, not the ACTS local measurements. It writes x = x0 + tx(z−zref) + a_x and y = y0 + ty(z−zref) + a_y, with global derivatives +1 for measurement-bias labels 1000+layer and 2000+layer. Physical Geometry updates negate these fitted biases. This sign must be verified separately for X and Y.

## Rigid transforms and scope

`geometry/transforms.py` defines active, right-handed rigid transforms in mm and radians: column-vector `p_parent = R p_child + t`. Composition `A @ B` applies B first and checks parent/child frame names. Inverse uses R transpose. A parent-frame correction about pivot c maps p to Q(p−c)+c+d and is left-composed; a child-frame update is right-composed. Rotation matrices are validated proper orthonormal matrices; Euler angles are not alignment state and are never added. The mathematical representation supports all six rigid-body degrees of freedom, including nonzero pivots. The preserved translation modes are `l2_x`, `l1_l2_x`, and `l1_l2_xy`; the experimental L1 rotation extension is described below.

The focused `Local_SiTrackerEndcap2XY` detector factory is adapted from the official DD4hep v01-36 Endcap2 builder. Its translation path adds independent per-ring `global_y` without altering phi, module orientation, material, segmentation or IDs. The experimental `global_rz` extension below changes orientation explicitly. The original nominal XML is unchanged. Generated XY XML selects that factory only for SiMAPS. Modifying phi to obtain Y would rotate the detector and is deliberately avoided.

`SurfacePlacements.h` obtains each actual sensitive context through the selected DD4hep converter. Its ACTS basis is u=−sensor Z, v=sensor X, n=u×v, so nominal u/v/n are global X/Y/Z. Surface centers and orientations follow the loaded Geometry. Trigonometric roundoff is snapped only within 1e−12 of 0 or ±1 for nominal translation-only basis equivalence. The KF, seed covariance, particle hypothesis and material model are unchanged. The SiMAPS covariance entries are permuted from sensor X/Z into plane u/v; existing equal pitch makes this numerically unchanged for the validated baseline. Surface diagnostic logs record all seven centers and axes.

Global Z translation is opt-in under the validated Z modes described below. Individually validated L1 Rx/Ry use the separate tilt model below. Combined rotations and six-DOF inference remain disabled; a general surface adapter alone does not establish observability.

## Readout, survey and truth

Readout Geometry defines IDs, segmentation, topology and channel-to-local-coordinate encoding. Survey/reference Geometry is an explicit approximate G0. Reconstruction Geometry is the selected immutable version used for both RecHits and ACTS. Simulation Truth Geometry is optional provenance used only outside the correction inference to evaluate closure.

RawHit schema v2 requires readout and topology fingerprints, RawHit checksum, units, producer and conditions. Optional `simulation_truth_geometry_sha256` explicitly identifies simulated physical placement. Schema v1 remains accepted with its original `measured_geometry_sha256` field; that legacy field is not silently relabeled as survey Geometry. `calibration.measured_geometry`, when supplied, is an optional legacy simulation-provenance verification, not a required physical-truth input. A truth-free calibration accepts compatible RawHits and an explicitly configured survey fallback; selected Geometry hashes remain mandatory in queue records and iteration provenance.

## Observability and gauges

For straight tracks, simultaneous displacement of every plane is absorbed into track intercepts; a displacement linear in z is absorbed into slopes. Thus unconstrained translation alignment has two null modes per transverse projection. Fixing L0/L4 as in the unchanged steering removes those gauges; L1–L3 X/Y remain fitted, while correction applies only the selected components. Releasing all planes is not supported.

Z derivatives scale with transverse track slopes; a narrow angular range makes Z weak and correlated with transverse translations. Rotation around the normal couples to transverse impact position, requiring spatial coverage. Tilts couple position, slope and propagation distance; a small beam spot and narrow slope range produce weak modes. Overall telescope orientation cannot be established absolutely by tracks whose intercepts and directions are free. External survey/beam constraints and validated Jacobians are needed before enabling these parameters. A good fit chi2 alone does not demonstrate identifiability.

The validated electron configuration uses only the five SiMAPS measurements. MPGD and AC-LGAD therefore provide no alignment information in these tests, despite their Geometry and RawHit collections being present. No observability claim for their alignment is made. In XY mode, fixed surveyed centers can be retained while L1/L2 are updated; fixed reference planes define the relative alignment gauge and are not assumed to be known physical truth.

## Experimental in-plane rotation extension

The experimental scope is developed in stages, starting with **SiMAPS L1 only**, then L1/L2 Rz and combined X/Y/Rz. The opt-in modes are `l1_rz`, `l1_l2_rz`, and `l1_l2_xy_rz`.
A right-handed active Global +Z rotation has matrix
`Qz(theta) = [[cos(theta),-sin(theta),0],[sin(theta),cos(theta),0],[0,0,1]]`.
Its angle is in radians. Sensor +Y points along Global −Z, so positive sensor-Y
rotation has the opposite sign. `global_rz` is a dedicated module-orientation
attribute; ring `phi0` remains zero. The physical pivot is the selected sensitive
center, and pure rotation retains that center. This is limited to the existing
single-module telescope hierarchy, rather than arbitrary detector layouts.

The ACTS adapter continues to use `u = -sensor Z`, `v = sensor X`, and
`n = u cross v`, evaluated in the selected DD4hep context. Sensor-local covariance
is expressed in that rotating basis. Equal SiMAPS X/Z pitches make the Global
X/Y measurement covariance isotropic; this phase does not establish support for
anisotropic rotated Mille measurements or tilts.

For pivot `(cx,cy)`, physical displacement is
`dm/dtheta = (-(y-cy), x-cx)`. Mille uses residual
`F = prediction + bias - measurement` and labels **3001/3002** for L1/L2 rotational
measurement bias in radians. The physical correction is `-bias`, so its stored
derivatives are `dF/da_rz = (-(y-cy), x-cx)` in mm/rad. Labels 1000+layer and
2000+layer retain their original translation meanings and defaults. Rotation-only steering fixes translations and releases only the selected Rz labels. Combined steering retains fixed L0/L4 and L3 X/Y nuisance parameters, applies L1/L2 X/Y/Rz, and never releases L3 rotation.
Corrections left-compose `Qz` with the **current** matrix about the current center;
`atan2` is used only to serialize the resulting SO(2) orientation to XML.
The Rz-only writer does not support tilted planes. Individual L1 tilts require the separately validated covariance-aware path below. Global Z translation follows the extension below.

Fresh DD4hep finite differences and actual Mille Binary checks are provided by
`python3 -m validation.validate_rz_derivatives --help`. Validation results and
whether subsequent modes may be released must be established by the rotation
validation report; mathematical transform support alone is not evidence of
alignment observability or permission to activate Geometry.

## Opt-in Global Z translation

The focused telescope factory accepts independent `global_z` in mm. It adds to
Global `zstart + dz` without changing ring radius/azimuth or module orientation.
Sensor +Y points along Global −Z: a positive Global Z correction is not a
positive sensor-Y displacement. Only the existing centered, non-reflected,
one-module-per-layer SiMAPS L1/L2 hierarchy is validated; offsets are bounded
to ±10 mm to retain layer ordering and large clearances. The nominal XML,
materials, readout and unselected placements remain unchanged.

Modes `l1_z` and `l1_l2_z` fit only selected Z corrections. `l1_l2_xyz` fits
selected X/Y/Z translations; all unselected sensors are fixed, including L3.
L0/L4 anchors are retained. No combined Z/Rz, mixed translation/tilt, combined Rx/Ry, or all-layer fit is enabled.
The default remains `l2_x` / legacy Mille writing.

For current selected Geometry z_g and physical increment c_z, the model is
`m_x = x0 + tx*(z_g-zref) + tx_ref*c_z + a_x`, and analogously for Y.
Labels **4000+layer** are physical Global Z corrections in **mm**, applied with
**positive** sign. Their derivatives are `(tx_ref, ty_ref)` in mm/mm. Labels
1000+layer and 2000+layer remain measurement biases applied with negative sign.
The writer obtains reference slopes by profiling the existing four-local-
parameter weighted straight-line model on current ACTS-associated RecHits.
Each Pede solve freezes these slopes; each external Geometry/reconstruction
iteration recomputes them. The second-order product `delta_tx * c_z` is not
passed to the linear solver. No Truth slopes or new tracking model are used.

Correction uses the current frame-aware transform and accumulates `global_z`.
`applied_mm_by_component` contains absolute sensitive-center coordinates;
`global_z_offsets_mm` in step5 records the serialized placement offsets.
RecHit Z and ACTS surfaces both follow the selected DD4hep sensitive contexts.
The fixed numerical z reference (100 mm) is a track coordinate origin, not a
hard-coded layer placement. Layer order remains valid for the bounded shifts.

The Controller requires same-plugin and same-Geometry-library finite-difference
proofs and profiles actual per-track local parameters before checking selected
global rank and Z information. Zero/narrow slopes and constant-angle XYZ can be
unobservable even when a numerical solver terminates. Nominal covariance is not
statistically certified: retain the Rz ensemble findings and do not rescale
errors. See [Z validation](Z_ALIGNMENT_VALIDATION.md).

## Individually validated Global Rx/Ry and covariance

Physical SiMAPS L1/L2 placement can represent Rx/Ry, but inference is validated
only for **L1 Rx or L1 Ry separately**. Initial placement constructors use
`Q = Rz(gamma) Ry(beta) Rx(alpha)`. Dedicated `global_rx`/`global_ry` attributes
are in radians; ring phi and radius are not used to imitate tilt. A full proper
3x3 Global matrix can instead be serialized as `global_r00` through `global_r22`,
without simultaneous axis-angle attributes. Correction state is that matrix.
The focused factory requires a single centered sensitive SiMAPS L1/L2 module,
phi0=0 and no reflection. Readout, material, thickness, IDs and nominal XML are
preserved. Bounded axis-angle preparation is limited to 0.1 rad. Arbitrary
layouts and arbitrary-angle tracking are not validated by matrix support.

A physical Global correction about actual center c is
`p_new = Q (p_current-c) + c + d`; pure tilt fixes c. When translation is
explicitly supplied by the mathematical transform, it occurs after rotation.
The current validated tilt solvers change no translations. With current point
`r=m-c` and frozen reconstructed reference slopes, residuals are
`F=(x0+tx*(mz-zref)-mx, y0+ty*(mz-zref)-my)`. Their physical derivatives are:

| Family | dF_x / dtheta | dF_y / dtheta | Units and correction sign |
|---|---|---|---|
| 5000+layer, Global Rx | tx*r_y | ty*r_y+r_z | mm/rad; apply positive fitted value |
| 6000+layer, Global Ry | -tx*r_x-r_z | -ty*r_x | mm/rad; apply positive fitted value |

At a nominal horizontal plane r_z=0. At nonzero orientations, current rotated
points and current pivots are required. These are **Global**, not identically
named sensor-local, axes. In particular nominal sensor Y is Global -Z.

RecHit error entries retain their existing **sensor X/Z segmentation** contract.
ACTS u=-sensor Z and v=sensor X, so local covariance is the corresponding
permutation. A consumer must not treat those legacy RecHit entries as a Global
XYZ covariance. For sensor-plane covariance C_uv and basis columns u,v, the
Global residual covariance is `S=H C_uv H^T`, with
`H=[[tx*u_z-u_x,tx*v_z-v_x],[ty*u_z-u_y,ty*v_z-v_y]]`.
The experimental tilt writer profiles the same four local straight-line
parameters, recomputing the slope-dependent covariance for its reference
trajectory. Each Pede solve freezes slopes and `W=chol(S)^-1`. It writes
`W*m`, `W*A` and `W*B` together with scalar sigma=1 in dimensionless units.
This invertible whitening is not an empirical error rescaling. Canonical
measurement errors, seed covariance, material and numerical KF are unchanged.
No independent Z measurement or bilinear local/global parameter is introduced.

Post-fit `TrackPoint.positionError` now contains actual Global XYZ covariance
`[u v] C_uv [u v]^T`, including cross terms. Previously this diagnostic field
received local u/v and time variances. Measurement2D retains local u/v/time
covariance, with the predicted/filtered/smoothed u/v cross term preserved. Both
serialized forms use the same symmetric projection of the floating-point state
covariance; this projection is applied only after fitting.
The correction affects serialization after fitting; it does not feed the KF or
Mille. Fresh tests validate float32-quantized global/local covariance using a
propagated half-ULP bound, including cancellation of large local entries.

Two fixed Global rotation generators do not form a closed two-dimensional
finite-rotation subgroup: `[Kx,Ky]=Kz`. The tested repeated `Ry(delta_y)
Rx(delta_x)` updates generated an unfitted Rz component and failed noiseless
orientation closure despite tiny updates. Combined Rx/Ry is therefore refused.
A future constrained two-coordinate model needs an explicitly defined finite
rotation chart and its transported Jacobians; alternatively a three-rotation
model needs its own full validation. Do not silently project away Rz, add Euler
angles as state, or regard a full-rank design as a validated six-DOF solver.
See [the scientific evidence](TILT_ALIGNMENT_VALIDATION.md).

## Coupled Global rotations: SO(3) increments

The explicit coupled modes `l1_rotations`, `l1_l2_rotations`, `l1_six_dof`
and `l1_l2_six_dof` use a complete proper rotation matrix as Geometry state.
Their mathematical and physical derivative evidence must pass before the
Controller accepts a calibration configuration. Their controlled-simulation
status and capture-range limits are recorded separately in
[the SO(3) validation report](SO3_ALIGNMENT_VALIDATION.md).

For column vectors, `p_global = R p_plane + c`. One correction rotates about
that sensor's **current sensitive center**, then translates it:

```
w = (parameter[5000+layer], parameter[6000+layer], -parameter[3000+layer])
d = (-parameter[1000+layer], -parameter[2000+layer], parameter[4000+layer])
R_new = Exp([w]x) R_current
c_new = c_current + d
```

Here `[w]x v = w cross v`; w is a Global-frame rotation vector in radians.
Translation entries are used only by the explicit six-DOF modes. The Rz label
retains its historical measurement-bias sign. Rx/Ry remain physical positive
increments, and X/Y remain measurement biases. Existing single-axis and
historical correction paths retain their conventions and numerical behavior.
The finite matrix is serialized with `global_r00` through `global_r22`;
axis-angle placement attributes are removed for that sensor to prevent mixed
representations. No Euler angles are accumulated, and no Rz component is
projected away.

For residual `F = (x0 + tx*(mz-zref)-mx, y0 + ty*(mz-zref)-my)`, freeze the
reconstructed reference slopes for one solve. A physical rotation about
Global unit axis k has `dm = k cross (m-c)` and
`dF = (tx*dmz-dmx, ty*dmz-dmy)`. The Rz bias column is **minus** this derivative.
The covariance factor W, measurements and all local/global columns are
whitened together using the existing sensor uncertainties. Relinearize at the
next current Geometry; do not differentiate a different finite parameterization
while retaining these fixed Global generators.

The relative Global rotation is `R_target R_current^T`. Orientation error is
the norm of its principal SO(3) logarithm, evaluated with stable quaternion
extraction near identity. Cumulative diagnostic components are
`Log(R_current R_survey^T)`, not ordered Euler angles or sums of increments.
They are correlated coordinates of one matrix and are not three independent
cumulative uncertainties.

A constrained two-coordinate chart is also mathematically possible:
`R = Ry(beta) Rx(alpha) R_reference`. Its alpha generator is
`Ry(beta) eX`, while its beta generator is `eY`. The exact chart retraction is
`Ry(db) Exp(da * Ry(beta)eX) R`. Thus alpha is **not** an instantaneous pure
Global Rx increment. The mathematical helper rejects orientations outside the
specified chart instead of discarding twist. This chart is tested as a
mathematical alternative; it is not an enabled two-parameter alignment mode.
The older `l1_rx_ry` and `l1_l2_rx_ry` interfaces remain disabled to avoid
silently changing their parameter meanings. Three independent rotations are
needed for generic orientations, alternative orders and unconstrained Survey
orientations. Their necessity is a model choice, not evidence of an erroneous
DD4hep left/right transform.

## Explicit three-layer six-DOF scope

The implementation prototypes `l3_six_dof` and `l1_l2_l3_six_dof` use the same current-sensitive-center SO(3) convention above. The latter releases 18 parameters on L1/L2/L3 while L0/L4 fix the reference frame; unselected detector placements remain fixed. Label families, signs and units are unchanged. Geometry preparation and the focused local DD4hep factory admit L3 using its actual sensitive context, with no new nominal-position constant. Scope selection is explicit, not a claim of generic detector support. See [the checkpoint](L3_SIX_DOF_IMPLEMENTATION.md) and [manual](L3_SIX_DOF_MANUAL.md).

# EDU06 R05 — engineering review

This editable educational-arm prototype uses exactly **four AX-12A and two XM430-W350-T motors**: five arm joints and one powered gripper. It has not been physically assembled, powered or load tested. No operating payload, service life, accuracy or production qualification is assigned.

The delivered native model passed the recorded digital mesh, control, interface and motion-sampling checks below. These checks do not establish a physical operating rating.

## Architecture

| Coordinate | Function | Motor | External transmission |
|---|---|---|---|
| J1 | Base yaw | AX-12A | 20/60 teeth, 3:1 |
| J2 | Shoulder pitch | XM430-W350-T | 20/100 teeth, 5:1 |
| J3 | Elbow pitch | XM430-W350-T | 20/80 teeth, 4:1 |
| J4 | Wrist pitch | AX-12A | 20/60 teeth, 3:1 |
| J5 | Tool roll | AX-12A | Direct, with external printed support |
| GRIP | Opposed parallel jaws | AX-12A | One 20-tooth pinion and two racks |

R05 removes the previous forearm-roll actuator and fixes a shorter wrist fork directly to the forearm. Curved cheeks, continuous structural ribs and rounded openings reduce the block-like appearance while retaining the motor and screw datums. The neutral forearm mount, wrist-pitch centre, tool-roll axis and gripper centreline lie on one line. The transverse pitch axis uses two removable trunnions, leaving room for the tool motor between them. The remaining roll support uses a 16 mm printed sleeve. Long fingers use removable pads with flat lands and a shallow V for round objects.

The green structure, gears, sleeves, journals, spacers and gripper parts are printed. Motors retain their supplied components; additional metal hardware is screws and nuts. Purchased metal bearings or shafts are not specified.

The R04 open service base is retained, including its printed turntable, yaw motor and U2D2 space. An independent mesh comparison checks that the functional base geometry and assembly placement remain identical. The removed service panel is checked for shape but its display placement is excluded. Gear reduction changes motor torque and travel; it does not eliminate bearing friction. U2D2 supplies communication, not motor power.

The saved output ranges are J1 −40…40°, J2 45…90°, J3 30…75°, J4 −25…25° and J5 −60…60°. GRIP is the clear pad opening from 20 to 70 mm. The required AX motor spans are 240° at J1, 150° at J4, 120° at J5 and approximately 95.49° at GRIP, each below the nominal 300° position-mode span. Real horn indexing, encoder offsets and end margins still need calibration.

## Dimensions and physical fits

All native geometry and STL coordinates use **millimetres**. STL imports must be interpreted as millimetres. The printer check uses the Bambu A1's 256 mm cube, with parts permitted to rotate to fit.

General M3 clearance bores are nominally 3.4 mm; captive hexagonal nut pockets are nominally 5.8 mm across flats. Printed rotary interfaces generally use 0.25 mm radial allowance, and parallel slides use 0.35 mm nominal face clearance. These are modeled allowances rather than measured fits. Printer calibration, layer orientation, seams, material and shrinkage affect the final clearances.

The annular supports are intended to carry external loads separately from the motor horn. Spacers and retainers must clamp the rotating parts without clamping stationary sleeves. Nut pockets need a supporting roof and insertion access. Screw lengths, horn fasteners and connector access are listed in the motor interface schedule and hardware BOM; the real motor revision must match those interfaces.

The fixed wrist fork, removable side trunnions and gripper guide caps allow staged assembly. Test fit coupons and one bearing/slide interface before printing the whole set. A digital collision result does not replace this physical check.

## Independent digital checks

The assembly and timeline reports reference `EDU06_R05.blend` saved on **23 September 2026 at 18:22:52 Singapore time**, **14,967,037 bytes**. Independent Blender processes opened it without resaving or changing its keyframes. A later documentation-only delivery save may change the file size; `delivery-integrity.json` records whether its mesh, controls, drivers and sampled animation remain unchanged.

| Check | Final R05 result |
|---|---|
| Actual motor references and arm axes | Exactly four AX-12A, two XM430-W350-T, five arm axes and one gripper control; no stale J6 |
| Functional base geometry versus R04 | All 60 scoped meshes match, including assembled placement at J1 = 0°; removed panel shape checked separately from its display placement |
| STL topology and A1 fit | 177/177 passed; 273,926 triangles; no failures or review cases |
| Spur profiles | 244 phase samples across J1/J2/J3/J4 passed; all four deliberately incorrect phases detected |
| Gripper rack profiles | 101 gap samples passed; deliberately incorrect phase detected |
| Control response, gear ratios and AX travel | Six controls, three values each; all passed |
| Neutral forearm-to-tool alignment | Passed within 0.05 mm; fixed wrist mount to distal tip 250.45 mm |
| Assembly motion and motor interfaces | 20 sampled poses; no unresolved crossings or penetration |
| Elbow pinion support assembly | No unresolved crossings; three intended zero-volume mating contacts retained with plane-bound evidence |
| Actual saved timeline | 31 snapshots; no unresolved crossings, motor-interface conflicts or limit violations |
| Physical testing | Not performed |

The assembly plan samples home, individual control endpoints, combined endpoints and intermediate tool-roll positions at wrist-pitch limits. It also records an explicitly out-of-range horizontal stress case. The saved 360-frame animation is sampled every 12 frames and at its final frame without replacing its keyframes. Each snapshot also checks gravity loads and static centre-of-mass projection.

The collision classifier compares meshes on different moving rigid bodies. It uses exact triangle intersections, then up to 64 sampled vertices per direction for interior-depth screening. Object-local bounds reject impossible containment before three-ray parity and outward-normal checks. Regression checks include rotated thin solids with positive interior probes and negative probes 0.25 mm beyond their faces. The recorded zero-volume elbow-support contacts are justified by projection intervals meeting within 0.001 mm along a world or object coordinate axis; aligned and rotated regression tests distinguish exact contact from real 0.2 mm overlap. Intended matching motor-case/horn contacts remain explicitly identified.

The motion pass excludes same-body mating parts and fixed-to-fixed pairs. A separate motor-interface pass compares every purchased case with every structural print, including same-body and fixed-to-fixed pairs, without exempting whole motors or cradles. Both passes exclude the removed panel, fit coupons, decorative fasteners and visual cables. Fastener stack review is separate. Discrete collision samples do not prove continuously clear motion, cable clearance, structural strength or free movement after printing. STL edge closure does not prove every triangle is free of self-intersection. The shoulder and elbow wheels have measured separating-plane gaps of approximately 0.25 mm from their XM cradle ends; physical tolerance and deflection can consume those small nominal gaps.

Reports: `stl-audit.json`, `gear-profile-audit.json`, `gripper-math-check.json`, `mass-load-audit.json` and `demo-trajectory-audit.json`. The two Blender audit scripts retain their methods and limitations for review.

## Gravity and mass assumptions

The audit uses calculation payloads of **0, 25 and 50 g at the distal tool-tip datum**. These are calculation inputs, not recommended payloads. No object dimensions are needed to inspect the prototype.

Printed mass comes from signed mesh volume at PLA density **1.24 g/cm³**. Real slicer walls, infill and weighed mass can differ. Each motor mass is assigned once to its case reference; its centre of mass is approximated from that external mesh. Moving components receive a **10% mass allowance** for wiring and screws. The removed service panel and fit samples are excluded.

`joint gravity moment = axis · Σ[(centre of mass − joint origin) × mass × gravity]`

`estimated motor gravity torque = |joint gravity moment| / (reduction × assumed efficiency)`

The calculations use each pose's evaluated world-space axes and mass centres. Assumed transmission efficiencies are 0.65 for geared pitch joints and 0.85 for direct tool roll. AX and XM planning comparisons are **0.30 and 0.82 N·m**, respectively, derived from 20% of published stall values. They are not guaranteed continuous ratings. A separate 1.5 multiplier is an illustrative allowance rather than dynamic simulation. Manufacturer references: [AX-12A manual](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/) and [XM430-W350 manual](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/).

Printed structural **solid-volume mass is 2,524.8 g**. Purchased references total 391.4 g: 382.4 g of motors and 9.0 g for U2D2. Moving mass before/after the 10% allowance is **1,811.9 / 1,993.1 g**. These are model estimates, not slicer filament totals or weighed parts.

The table uses a **25 g calculation input**. Maxima include the 19 in-range assembly poses and 31 actual timeline snapshots; the horizontal stress pose is excluded from these maxima.

| Joint | Ratio | Home gravity, N·m | Sampled maximum, N·m | Maximum ×1.5, N·m | Planning comparison, N·m |
|---|---:|---:|---:|---:|---:|
| J2 | 5:1 | 0.458 | 0.566 | 0.849 | 0.82 |
| J3 | 4:1 | 0.431 | 0.440 | 0.660 | 0.82 |
| J4 | 3:1 | 0.197 | 0.198 | 0.297 | 0.30 |
| J5 | 1:1 | <0.001 | 0.012 | 0.017 | 0.30 |

No sampled gravity case at 0, 25 or 50 g exceeds its planning comparison. At 50 g, the largest relative demand is **0.225 N·m at J4**, about **25.0% below** its 0.30 N·m comparison. This is only a margin to an assumed comparison, with unmeasured friction, acceleration and temperature effects. The illustrative 1.5 multiplier already takes the 25 g shoulder maximum above its comparison. The out-of-range horizontal stress calculation also remains below the gravity comparisons, but does not define an allowed operating pose. No payload rating follows from these calculations.

The report also retains complete bending-moment vectors at the bearings. A small torque about a motor axis does not imply a small bearing load. Ideal gravity creates no torque around the vertical yaw axis, but friction, cable pull and acceleration still do. Printed-journal friction is unmeasured.

Static stability projects the model centre of mass, including the 25 g calculation case, onto the foot-centre rectangle X ±108 mm and Y ±73 mm. The foot screws retain the feet; dedicated bench anchors are not provided. The smallest sampled margin is **39.63 mm inside** that rectangle in the assembly sweep and **46.28 mm inside** during the sampled timeline. This screening does not evaluate sliding, cable forces, impacts or acceleration.

## Remaining physical validation

There is no finite-element stress analysis, calibrated friction model, thermal-duty validation, fatigue/creep model or physical payload test. The scene demonstrates constrained kinematics, not the full physics of a printed assembly.

Measure the supplied motors, horns, nuts and screws. Confirm printed hole fits, free joint motion and nut access, then establish motor zeros and protective limits on the assembled prototype. Begin powered tests unloaded, checking deflection, friction and temperature before adding a load. These measurements are necessary to assign an operating payload or duty cycle.

AX position mode offers approximately 300° total motor travel; external reduction reduces the available output travel. AX wheel mode does not give the same absolute position control. The eventual controller must handle AX Protocol 1.0 and XM Protocol 2.0 and use a suitable separate motor supply.

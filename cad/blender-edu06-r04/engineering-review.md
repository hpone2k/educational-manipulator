# EDU06 R04 — engineering review

This is an editable, dimensioned engineering prototype for an educational arm. It has not been physically assembled, powered or load tested. The STL files describe prototype parts; no operating payload, service life, accuracy or production qualification is assigned.

The final native model passed the recorded digital geometry, control and motion-sampling checks below. Earlier debug results are not acceptance results for this release. The checks do not establish a physical operating rating.

## Architecture and actual motion

The arm has six independent joint coordinates and a separate gripper actuator: **seven motors, six arm degrees of freedom**. J1, J4, J5, J6 and the gripper use AX-12A motors; J2 and J3 use XM430-W350-T motors. The green structure, gears, bearing sleeves, journals, spacers and gripper parts are fabricated by printing. Motors retain their supplied components; additional metal hardware is screws and nuts.

| Coordinate | Function | External transmission | Model control |
|---|---|---|---|
| J1 | Base yaw | 20/60 teeth, 3:1 | Output angle in degrees |
| J2 | Shoulder pitch | 20/100 teeth, 5:1 | Output angle in degrees |
| J3 | Elbow pitch | 20/80 teeth, 4:1 | Output angle in degrees |
| J4 | Forearm roll | Direct, with printed external journal | Output angle in degrees |
| J5 | Wrist pitch | 20/60 teeth, 3:1 | Output angle in degrees |
| J6 | Tool roll | Direct, with printed external journal | Output angle in degrees |
| GRIP | Opposed parallel jaws | One 20-tooth pinion and two racks | Clear pad gap in millimetres |

The neutral wrist places the J4 roll axis, J5 pivot centre, J6 roll axis and tool centreline on one straight line. J5 is transverse to that line. Two removable side trunnions support the pitch cradle, leaving space for the tool motor between them. The J4 and J6 printed roll sleeves are 16 mm long. The gripper uses 75 mm long fingers with replaceable keyed pads, flat contact lands and a shallow V for round objects.

The base is an open service enclosure containing the yaw motor and U2D2. Its printed turntable uses separated journal surfaces and a thrust surface. Gear reduction changes the torque and travel required from the motor; it does not remove bearing friction. U2D2 provides communication, not motor power.

Motor exteriors are tessellated from manufacturer STEP geometry. Mesh appearance is not a substitute for checking the supplied motor and horn revision. Interface datums, hole patterns, screw stacks and connector access are recorded in `motor-interface-schedule.json`. `hardware-bom.json` lists the modeled hardware; `README.md` describes assembly and file use.

Configured output ranges are J1 −40…40°, J2 60…85°, J3 30…75°, J4 −40…40°, J5 −25…25° and J6 −60…60°. The gripper pad opening is 20…70 mm. The shoulder's 60° lower operating limit keeps the sampled gravity cases within the planning comparisons; it is an operating restriction, not a payload rating. AX motor travel required over these configured ranges is 240° at J1, 80° at J4, 150° at J5, 120° at J6 and approximately 95.49° at the gripper.

## Dimensions, mating fits and assembly

All model and STL coordinates use **millimetres**. Bambu A1 placement is checked against a 256 mm cube. STL files carry no reliable unit label; import them into the slicer as millimetres.

General M3 clearance bores are nominally 3.4 mm and captive hexagonal nut pockets are nominally 5.8 mm across flats. Printed rotary interfaces generally use 0.25 mm radial allowance; the parallel slide uses 0.35 mm nominal face clearances. These are modeled allowances, not measured print clearances. Hole shrinkage, layer orientation, seam position and filament condition can change the fit.

The printed journals carry the intended external loads independently of the stock motor output horn where an external support is provided. Retaining screws and spacers clamp the rotating members without deliberately clamping the stationary bearing sleeve. Captive-nut pockets require a load-bearing roof, actual nut insertion access and the specified screw length. Tightening a screw must not lock its moving interface.

The elbow support cheeks use shared bolts and printed spacers. The wrist uses separate removable trunnions and rear-access captive nuts. The gripper guide caps are removable so the captured slides can be installed; keyed pads slide out after their tip caps are removed. Follow the assembly guide and verify the fit coupon before printing the complete set.

## Recorded digital checks

The assembly and animation reports reference the final `EDU06_R04.blend` saved on 23 September 2026 at 15:20:55 Singapore time, 16,248,174 bytes. They were produced by independent fresh-load processes without resaving that file.

The delivery subsequently embeds the completed documentation in Blender Text blocks. `delivery-integrity.json` records the before/after file hashes and verifies that mesh geometry, control limits, drivers and 31 evaluated animation snapshots are unchanged by this documentation-only save.

| Check | Final result | What it establishes |
|---|---|---|
| STL topology and A1 bounds | 186/186 passed; 250,714 triangles; no failures or review cases | Finite nondegenerate triangles, edge closure/winding, positive volume, connectedness and build-volume fit |
| Spur-pair profile checks | 244 phase samples across J1/J2/J3/J5 passed; deliberately incorrect phases detected | Current 20/60, 20/100, 20/80 and 20/60 tooth pairs |
| Rack profile checks | 101 gap samples passed; deliberately incorrect phase detected | Mathematical rack/pinion engagement through the 20–70 mm opening range |
| Control, reduction and AX travel checks | Seven controls, three values each; all passed | Evaluated joint/pinion response, pad gap and required AX motor travel span |
| Neutral wrist centreline | Passed; J4-to-tip station 293.45 mm | Actual evaluated joint and tool datums align within 0.05 mm tolerance |
| Assembly mesh sampling | 22 poses; no unresolved intersections | Includes four intermediate tool-roll corner sweeps and one explicitly out-of-range horizontal stress case |
| Delivered timeline sampling | 31 snapshots; no unresolved intersections or limit violations | Actual saved keyframes evaluated without replacing their animation |
| Physical testing | Not performed | Friction, fit, strength, heat, wear, creep and powered behavior remain unmeasured |

Reports: `stl-audit.json`, `gear-profile-audit.json`, `gripper-math-check.json`, `mass-load-audit.json` and `demo-trajectory-audit.json`. Their file timestamps and native-model references identify the checked version. Spur-pair parameters are in `gear-pairs.json`; their drivers and sampled physical mesh poses are also checked by the assembly audit.

The collision check compares different moving rigid bodies using triangle intersections and sampled inside/outside probes. It excludes same-body mating parts, the removed service panel, fit coupons, decorative fasteners and visual cable routes. Matching manufacturer motor/horn interface contacts are explicitly identified. Fastener stack review is separate. Sampling does not establish continuous collision freedom or cable bend clearance. STL edge tests do not prove every triangle is free of self-intersection or that a wall is strong enough.

The containment classifier is checked against cubes, hollow sleeves, rotated sleeves and rotated thin-solid positive/negative cases. It rejects points outside a solid's own local bounds before ray testing. Separating-plane measurements from the final meshes confirm the shoulder/elbow wheel faces remain approximately 0.25 mm in front of the XM cradle ends. These small nominal gaps require physical tolerance checks; they are not deflection allowances.

## Gravity, mass and motor comparison

The load cases use **0, 25 and 50 g** at the distal tool-tip datum. These are calculation inputs, not payload recommendations. No object weight or geometry is required to inspect this prototype.

Printed mass is integrated from the modeled solid volume using PLA density **1.24 g/cm³**. Real slicer walls/infill and measured print mass may differ. Manufacturer motor mass is assigned once per motor; its centre of mass is approximated from the external case mesh. Moving components receive a **10% mass allowance** for screws and wiring.

For each pose, the audit uses the actual world-space axis and centres of mass:

`joint gravity moment = axis · Σ[(centre of mass − joint origin) × mass × gravity]`

`estimated motor gravity torque = |joint gravity moment| / (reduction × assumed efficiency)`

Assumed efficiencies are 0.65 for the geared pitch joints and 0.85 for direct wrist roll. The AX and XM comparison values are **0.30 and 0.82 N·m**, respectively, derived from 20% of published stall values. They are screening comparisons, not guaranteed continuous-duty ratings. An additional 1.5 multiplier is an illustrative allowance, not a dynamic simulation. Manufacturer references: [AX-12A manual](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/) and [XM430-W350 manual](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/).

The printed structural **solid-volume mass is 2,681.6 g**. Purchased references total 446.0 g, including the motors and U2D2. Moving mass before/after the 10% allowance is **2,023.3 / 2,225.7 g**. The removed service panel and fit samples are excluded. These are model estimates, not slicer filament totals or weighed parts.

The following motor-shaft values use the 25 g calculation case. Maxima include only the 21 sampled poses inside the configured joint limits.

| Joint | Ratio | Home gravity, N·m | Sampled maximum, N·m | Maximum ×1.5, N·m | Planning comparison, N·m |
|---|---:|---:|---:|---:|---:|
| J2 | 5:1 | 0.726 | 0.768 | 1.151 | 0.82 |
| J3 | 4:1 | 0.740 | 0.753 | 1.129 | 0.82 |
| J4 | 1:1 | 0.060 | 0.223 | 0.334 | 0.30 |
| J5 | 3:1 | 0.203 | 0.204 | 0.306 | 0.30 |
| J6 | 1:1 | <0.001 | 0.015 | 0.022 | 0.30 |

No sampled in-range gravity case at 0, 25 or 50 g exceeds the stated comparison. However, the limiting 50 g shoulder case reaches **0.803 N·m**, leaving only about **2.1%** below its comparison before unmodeled friction, acceleration or measurement error. The illustrative 1.5 multiplier exceeds several comparisons. The out-of-range horizontal stress case exceeds the shoulder comparison even unloaded and is not part of the configured operating workspace. These results support no certified or tested payload claim.

The report separately records complete bending-moment vectors at bearings; a small motor-axis moment does not imply a small structural bearing load.

The base-yaw axis is vertical, so ideal gravity generates no torque around J1. Breakaway friction, cable forces and acceleration still require motor torque. Printed journal friction is unmeasured and can be substantial under bending load. Longer roll sleeves reduce the idealized edge-force couple; they do not establish a friction coefficient, acceptable backlash or lifetime.

The static stability check projects the combined model centre of mass, including the 25 g calculation case, onto the foot-centre rectangle at X ±108 mm and Y ±73 mm. The smallest sampled margin is **23.78 mm inside** that rectangle. The foot screws attach the feet; dedicated bench anchorage is not provided. Static projection does not evaluate sliding, sudden acceleration, cable pulls or impacts.

## What remains before an operating rating

The project has no finite-element stress analysis, experimentally calibrated joint friction, thermal duty-cycle validation, fatigue/creep model or physical payload test. The scene demonstrates constrained kinematics; it is not a physics simulation of a printed machine.

Print the fit coupons and one bearing/slide interface first. Measure the actual motor, horn, nut and screw interfaces, and check free movement before tightening or powering each module. Establish motor zero offsets, end margins and current/torque settings with the real assembly. Then test the assembled arm progressively, beginning unloaded, while measuring motion, deflection and motor temperature. Those observations are necessary before assigning a useful payload or duty cycle.

AX position mode has approximately 300° total motor travel; external reduction reduces the available output travel. The report checks the required span, but real horn indexing and encoder-zero calibration remain necessary. AX wheel mode does not provide the same absolute position control. The implementation must account for AX Protocol 1.0 and XM Protocol 2.0 communication and a suitable separate motor supply.

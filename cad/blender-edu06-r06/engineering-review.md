# EDU06 R06 — engineering review

This editable educational-arm prototype uses exactly **four AX-12A and two XM430-W350-T motors**: five arm joints and one powered gripper. It has not been physically assembled, powered or load tested. No operating payload, service life, accuracy or production qualification is assigned.

**The integrated R06 geometry passes the stated digital checks at 19 operating poses and 31 animation snapshots.** The additional all-zero horizontal diagnostic pose is obstructed and outside the saved shoulder/elbow limits; it is not an available operating position. The digital results establish the sampled geometry, kinematics and nominal interfaces only.

## Architecture

| Coordinate | Function | Motor | External transmission |
|---|---|---|---|
| J1 | Base yaw | AX-12A | 20/60 teeth, 3:1 |
| J2 | Shoulder pitch | XM430-W350-T | 20/100 teeth, 5:1 |
| J3 | Elbow pitch | XM430-W350-T | 20/80 teeth, 4:1 |
| J4 | Wrist pitch | AX-12A | 20/60 teeth, 3:1 |
| J5 | Tool roll | AX-12A | Direct, with external printed support |
| GRIP | Opposed parallel jaws | AX-12A | One 20-tooth pinion and two racks |

R06 uses paired printed links on both sides of the shoulder and elbow output axes. The intended load path runs through the independent printed shaft and two bushings, positive keyed flanges, both side plates and both sides of the next stationary housing. The motor horn supplies drive through the gear pair; it is not the intended sole external bending support. A keyed rear output flange couples the rear plate without relying on central-screw friction alone. This architecture does not imply an equal 50/50 force split: actual load sharing depends on stiffness, fit and assembly preload, none of which has been measured.

The shoulder and elbow bearing midplanes are centred. At zero yaw and neutral wrist, the evaluated centres, wrist mount and tool centreline share one fore-aft plane within 0.00003 mm of numerical lateral error. The paired upper-link midplanes are ±57.5 mm; the paired forearm midplanes are ±44.5 mm. All four plates are 6 mm thick. Their common drive hierarchy and positive mesh volumes were checked independently. The transverse wrist crossmember physically joins both forearm plates to the central flange.

Shoulder-to-elbow pivot spacing is 100 mm. Elbow-to-fixed-wrist-mount distance is 78.8 mm along the neutral forearm. The neutral fixed wrist mount to distal tool-tip datum is **270.45 mm**, including the 20 mm open cable-service gap behind the gripper. The latter gap uses four printed spacer posts and longer fasteners; it also increases the modelled gravity moment.

The green structure, gears, sleeves, journals, spacers and gripper parts are printed. Motors retain their supplied components; additional metal hardware is screws and nuts. Purchased metal bearings or shafts are not specified.

The enlarged open service base reserves space for a controller, a separate unselected power module and the installed U2D2. Nominal shell/lid width is 240 × 240 mm; the front tab arms extend the measured enclosure envelope to **241 × 240 × 95 mm**. It has removable service access and printed cable clamps. Slotted mounting trays avoid inventing a PCB hole pattern. Electronics reservation boxes are clearance references and add no imaginary installed mass. Actual boards, cables and connector revisions still need fitting.

Daisy-chain routes and joint service loops show the intended connection order. Their display alone does not establish cable flexibility, adequate slack through every pose or electrical suitability. Gear reduction changes motor torque and travel; it does not eliminate bearing friction. U2D2 supplies communication, not motor power.

The saved output ranges are J1 −40…40°, J2 45…90°, J3 30…75°, J4 −25…25° and J5 −60…60°. GRIP is the clear pad opening from 20 to 70 mm. The required AX motor spans are 240° at J1, 150° at J4, 120° at J5 and approximately 95.49° at GRIP, each below the nominal 300° position-mode span. Real horn indexing, encoder offsets and end margins still need calibration.

## Dimensions and physical fits

All native geometry and STL coordinates use **millimetres**. STL imports must be interpreted as millimetres. The printer check uses the Bambu A1's 256 mm cube, with parts permitted to rotate to fit.

General M3 clearance bores are nominally 3.4 mm; captive hexagonal nut pockets are nominally 5.8 mm across flats. Printed rotary interfaces generally use 0.25 mm radial allowance, and parallel slides use 0.35 mm nominal face clearance. These are modeled allowances rather than measured fits. Printer calibration, layer orientation, seams, material and shrinkage affect the final clearances.

The annular supports are intended to carry external loads separately from the motor horn. Spacers and retainers must clamp the rotating parts without clamping stationary sleeves. Nut pockets need a supporting roof and insertion access. Screw lengths, horn fasteners and connector access are listed in the motor interface schedule and hardware BOM; the real motor revision must match those interfaces.

The fixed wrist fork, removable side trunnions and gripper guide caps allow staged assembly. Test fit coupons and one bearing/slide interface before printing the whole set. A digital collision result does not replace this physical check.

## Independent digital checks

The mechanical reports independently opened `EDU06_R06.blend`, saved 24 September 2026 at 00:35:35 Singapore time (16:35:35 UTC on 23 September), 15,345,704 bytes. This includes the final bilateral structures, enlarged base, gripper service gap and bored pedestal. Reference-only wiring refreshes are reviewed separately and must preserve the engineering-mesh fingerprint.

The final reference-wiring refresh at 01:34:26 preserved all 716 engineering mesh objects with identical before/after SHA-256 `cdcce62fb95fb822fc2f46373a3932d345892deeb570f1e495857a63475a136c`. The independent wire-driver and fixed-jacket checks then freshly opened the 01:34:49 presentation save. Those read-only checks did not resave the native file.

| Check | R06 status |
|---|---|
| Actual motor references and five arm axes | Pass: four AX-12A, two XM430-W350-T; five arm axes plus gripper |
| Paired links on both sides and common drive hierarchy | Pass: two actual side plates per stage, symmetric midplanes |
| Full-arm top-view alignment and wrist centreline | Pass: 0.05 mm tolerance; actual numerical errors below 0.00004 mm |
| Installed motor cases versus all structural prints, including same-body pairs | Pass at all operating samples and animation snapshots |
| Elbow support, positive keys and coupling interfaces | Pass for explicitly reported shaft, cheek, bridge and wrist-crossmember checks |
| Reserved electronics and USB withdrawal envelopes | Pass: three actual boxes against structural parts and tagged fasteners |
| STL topology and A1 fit | Pass: 186/186, 294,160 triangles; finite, nondegenerate, closed, consistent winding, positive volume, grounded and within build dimensions |
| Spur and rack profiles with deliberately incorrect-phase controls | Pass: 244 spur phases and 101 jaw gaps; incorrect-phase negative controls detected overlap |
| Six controls, reductions and AX travel spans | Pass: three tested values per control, actual output/pinion movement |
| Assembly collision/gravity samples | 19 in-range operating poses clear; one out-of-range horizontal diagnostic retained as obstructed |
| Actual saved keyframe trajectory | Pass: 31 snapshots, no reported structural or motor-case penetration; all controls in range |
| Native wire graph and evaluated curve drivers | Pass on final refreshed native: seven bus edges, six actual motor cases, 28 curves across 31 saved frames and 19 poses |
| Cable route clearance, bends and strands | Pass on final refreshed native: all seven harnesses, 31 animation snapshots and 19 operating poses; minimum conductor bend 12.176 mm, within-harness strand spacing 1.481 mm, bundle-to-structure gap 0.596 mm |
| Fixed USB and external DC jackets | Pass: 501 stations each; 703 structural/hardware meshes; minimum bends 13.47/19.17 mm, respectively |
| Physical testing | Not performed |

The assembly plan samples home, individual control endpoints, combined endpoints and intermediate tool-roll positions at wrist-pitch limits. The extra all-zero horizontal stress case produces actual intersections between the forearm structure and elbow housing/supports. Its J2=0° and J3=0° settings are below the saved lower limits of 45° and 30°. Do not command that pose. The saved 360-frame animation is sampled at frames 1, 13, …, 349 and 360 without replacing its keyframes. Each snapshot also checks gravity loads and static centre-of-mass projection.

The collision classifier compares meshes on different moving rigid bodies. It uses exact triangle intersections, then up to 64 sampled vertices per direction for interior-depth screening. Object-local bounds reject impossible containment before three-ray parity and outward-normal checks. Regression checks include rotated thin solids with positive interior probes and negative probes 0.25 mm beyond their faces. A coordinate-plane proof distinguishes intended mating contact from material overlap: aligned and rotated regression tests compare exact contact, real 0.2 mm overlap and a real 0.2 mm gap. For ambiguous nested static fits, a separate EXACT Boolean intersection measures common solid volume in a local coordinate frame. Its contact, 0.2 mm overlap and 0.2 mm gap cube regressions return 0, 20 and 0 mm³. The numerical 0.01 mm³ threshold is not a manufacturing allowance. Matching motor-case/horn contacts remain explicitly identified.

The motion pass excludes same-body mating parts and fixed-to-fixed pairs. A separate motor-interface pass compares every purchased case with every structural print, including same-body and fixed-to-fixed pairs, without exempting whole motors or cradles. Additional static checks inspect both keyed shafts, the elbow cheeks/bushings, pinion support and centred wrist crossmember against all included solids. Critical bilateral-link, root, retention and crossmember fasteners are included in motion screening; their meshes use simplified nominal hardware geometry. Electronics envelopes are also checked against all tagged fasteners and socket heads. The removed panel, fit coupons, other decorative fasteners and visual cables are excluded from structural collision screening. Discrete samples do not prove continuously clear motion, structural strength or free movement after printing. STL edge closure does not prove every triangle is free of self-intersection. Both actual XM wheel-to-cradle coordinate-plane gaps measure approximately **0.25 mm**. Physical tolerance and deflection can consume those small gaps.

The wire-driver check separately compares the native seven-edge daisy-chain graph with all six installed motor cases, and verifies that all 28 route/conductor curves follow their actual anchors in every sampled pose. Correct connectivity and driver motion do not establish cable clearance, minimum bend radius, real connector engagement or electrical suitability.

The separate cable screen samples each evaluated NURBS curve at 121 stations. At each station it measures the actual conductor offsets plus the modelled 0.72 mm insulation radius, then compares that bundle envelope with printed surfaces and motor cases. Object-local bounds and three-ray parity check potential interior points. Clearance outside connector mouths is at least 0.5 mm in accepted samples. Each actual conductor is screened for a 12 mm geometric bend radius, and 241 stations per strand support nearest-segment spacing checks within each three-wire harness. The final reports pass all five criteria: endpoint attachment, gear clearance, structure clearance, conductor bends and strand separation. Their 31-frame routing sample list is recorded explicitly in `wiring-audit.json`; it is separate from the mechanical snapshot list. Virtual guide empties are spline control points, not physical cable clips. These discrete screens are not continuous collision proofs or a complete contact analysis between separate harnesses.

The fixed USB and external DC jackets have a separate 501-station screen using their own 2.35 and 2.8 mm radii. It includes same-body printed structure and tagged hardware. The actual printed cable saddles intentionally provide 0.25 and 0.4 mm radial clearances; only those coaxial clamp locations use their nominal allowance, with 0.01 mm numerical/facet tolerance. Other structure retains the 0.5 mm clearance target. The immediate outward USB connector face remains a provisional interface.

The native cable curves change arc length as the joints move. Real cables have fixed cut lengths and require measured slack, secure strain relief and a verified cable bend specification. The routed geometry does not simulate stretch, contact forces, stiffness, fatigue, cyclic flex life or electrical current capacity. The H05 wrist loop uses an external route; H06 uses the wrist heel bore. Physical routing still needs inspection through the intended range.

Reports: `stl-audit.json`, `gear-profile-audit.json`, `gripper-math-check.json`, `mass-load-audit.json`, `demo-trajectory-audit.json`, `wiring-kinematics-audit.json`, `wiring-audit.json`, `wiring-operating-range-audit.json` and `fixed-jacket-audit.json`. The Blender audit scripts retain their methods and limitations for review.

## Gravity and mass assumptions

The audit uses calculation payloads of **0, 25 and 50 g at the distal tool-tip datum**. These are calculation inputs, not recommended payloads. No object dimensions are needed to inspect the prototype.

Printed mass comes from signed mesh volume at PLA density **1.24 g/cm³**. Real slicer walls, infill and weighed mass can differ. Each motor mass is assigned once to its case reference; its centre of mass is approximated from that external mesh. Moving components receive a **10% mass allowance** for wiring and screws. The removed service panel and fit samples are excluded.

`joint gravity moment = axis · Σ[(centre of mass − joint origin) × mass × gravity]`

`estimated motor gravity torque = |joint gravity moment| / (reduction × assumed efficiency)`

The calculations use each pose's evaluated world-space axes and mass centres. Assumed transmission efficiencies are 0.65 for geared pitch joints and 0.85 for direct tool roll. AX and XM planning comparisons are **0.30 and 0.82 N·m**, respectively, derived from 20% of published stall values. They are not guaranteed continuous ratings. A separate 1.5 multiplier is an illustrative allowance rather than dynamic simulation. Manufacturer references: [AX-12A manual](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/) and [XM430-W350 manual](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/).

The final solid-mesh inventory is **3,013.9 g printed structure** plus **391.4 g assigned purchased components**. Moving mass is 2,053.6 g before the allowance and 2,258.9 g after it; fixed mass is 1,351.7 g. These are geometric planning masses, not a slicer estimate or a weighed robot.

Maximum estimated motor-axis gravity torque over the 19 operating poses and 31 animation snapshots is:

| Motor axis | 0 g tip input | 25 g tip input | 50 g tip input | Planning comparison |
|---|---:|---:|---:|---:|
| J2 shoulder | 0.606 N·m | 0.638 N·m | 0.669 N·m | 0.82 N·m |
| J3 elbow | 0.444 N·m | 0.476 N·m | 0.509 N·m | 0.82 N·m |
| J4 wrist pitch | 0.200 N·m | 0.229 N·m | 0.259 N·m | 0.30 N·m |
| J5 tool roll | 0.012 N·m | 0.012 N·m | 0.012 N·m | 0.30 N·m |

The centreline tip load contributes essentially no torque about its own roll axis; its bearing bending load still increases. All raw gravity cases are below the assumed comparison values, but the illustrative 1.5 multiplier exceeds the shoulder comparison even without a tip load (0.910 N·m), and exceeds wrist-pitch comparison at 25 and 50 g (0.344 and 0.388 N·m). This is a material limitation of the planning model, not a passed dynamic-duty test. No payload rating follows from this table.

The report also retains complete bending-moment vectors at the bearings. A small torque about a motor axis does not imply a small bearing load. Ideal gravity creates no torque around the vertical yaw axis, but friction, cable pull and acceleration still do. Printed-journal friction is unmeasured.

Static stability projects the complete modeled centre of mass, including the 25 g calculation case, onto the convex hull of the actual printed foot centres at X ±108 mm and Y ±103 mm. The smallest inside-edge distance is **71.83 mm** across operating assembly samples and **82.48 mm** across animation snapshots. Foot contact radius is omitted conservatively. The foot screws retain the feet; dedicated bench anchors are not provided. This screening does not evaluate sliding, cable forces, impacts, acceleration or the stability of a lower-infill printed build.

## Remaining physical validation

There is no finite-element stress analysis, calibrated friction model, thermal-duty validation, fatigue/creep model or physical payload test. Printed PLA gear-tooth and hex-key strength, bearing wear, creep and motor thermal duty remain unknown. The scene demonstrates constrained kinematics, not the full physics of a printed assembly.

Measure the supplied motors, horns, nuts and screws. Confirm printed hole fits, free joint motion and nut access, then establish motor zeros and protective limits on the assembled prototype. Begin powered tests unloaded, checking deflection, friction and temperature before adding a load. These measurements are necessary to assign an operating payload or duty cycle.

AX position mode offers approximately 300° total motor travel; external reduction reduces the available output travel. AX wheel mode does not give the same absolute position control. The eventual controller must handle AX Protocol 1.0 and XM Protocol 2.0 and use a suitable separate motor supply.

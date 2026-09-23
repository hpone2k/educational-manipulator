# EDU-06 L01: lightweight PLA engineering study
23 September 2026. Supersedes the 140 / 120 mm link-length assumption in the earlier image study. The image and existing five-axis webpage have not been converted to dimensional CAD. This revision defines engineering inputs; it does not release printable arm parts.

## Baseline
User: normal filament, Bambu printer. Working assumption: standard PLA, 0.4 mm nozzle. Exact printer, nozzle and filament formulation remain unconfirmed. Retain six arm axes plus separate geared gripper: 5 x AX-12A and 2 x XM430-W350-T.

| Motor | Manufacturer W x H x D | Mass | Count |
|---|---|---:|---:|
| AX-12A | 32 x 50 x 40 mm | 54.6 g | 5 |
| XM430-W350-T | 28.5 x 46.5 x 34 mm | 82 g | 2 |

Total motors: 437 g. J4/J5/J6/gripper AX motors alone: 218.4 g. This makes a tiny, weightless wrist impossible. Bodies are positioning envelopes, not installation clearances: allow for horns, mating cables, screw heads, moving yokes and tool access. Preliminary pocket allowance is 0.25-0.40 mm per side, to be tuned on coupons; do not add it to hole-center coordinates.

## Mounting drawings actually inspected
AX: official ROBOTIS front/side image saved in motor-references/ax-12a-dimensions.png.
XM: ROBOTIS-authored XM series datasheet, hosted by Distrelec, saved in motor-references/robotis-xm-datasheet.pdf. This is a reference drawing, not confirmation of the revision of the user's horn.

- AX output horn: four M2 tapped holes at 90-degree intervals on a 16 mm pitch circle; drawing callout depth 4.0 mm. In front-view coordinates centred on the output axis, cardinal hole centres are (+8,0), (0,+8), (-8,0), (0,-8) mm. Frame hole clearance is separate from the motor's M2 thread.
- AX front body mounting rows: drawing shows 27 mm between the two outer mounting-hole columns and 8 mm vertical pitch between repeated rows. The top repeated row is 6.5 mm below output centre. Do not mistake the case assembly screws for all-purpose bracket mount holes. AX body frame mounting hardware and nut access must be matched to the official assembly scheme; no body-hole coordinates are released for fabrication here.
- XM chosen four-hole side interface: rectangular 12 x 24 mm hole spacing, M2.5 x 0.45 tapped holes, maximum depth 3.0 mm in the inspected sheet. Local pattern coordinates around that pattern's centre are (+/-6,+/-12) mm. The pattern centre is NOT the output-shaft centre; place it on the correct body face using the manufacturer drawing/STEP.
- XM horn in the inspected sheet: eight M2 x 0.4 holes on 16 mm PCD, maximum thread depth 2.0 mm. Hole indexing and horn revision must be checked against the supplied horn; another horn drawing may have a different depth. The AX and XM horn patterns are not interchangeable.
- The front case-retaining screws, shaft-centre screw, horn attachment screws and frame attachment screws serve different functions. Do not replace them all with M3.
- Screw projection = under-head length minus printed bracket, washer and spacer stack. Check both sufficient engagement and the maximum allowed projection, with tolerance, before choosing length. A blind-hole depth is a maximum, not an instruction to bottom out. Preserve prescribed ROBOTIS spacers/idler arrangements.

## Printed fastening features
These are trial CAD values, not universal Bambu tolerances:
- M2 through-clearance: 2.3 mm; M2.5: 2.8 mm; M3: 3.4 mm. Print a coupon; holes may need finishing.
- M3 shell nut pocket: 5.8 mm across flats, 2.7 mm deep for a nominal DIN 934 M3 nut (5.5 mm AF, 2.4 mm high). Check the purchased nut. Pocket oriented with flats resisting rotation, open assembly access, positive retention via the cover.
- M3 boss outer diameter: 11 mm provisional. A 5.8 mm AF pocket is about 6.70 mm across corners, leaving about 2.15 mm minimum radial material in this boss. Add ribs and root fillets; keep pocket corners away from cutouts.
- Aim for at least 2 mm material between pocket corners and free surfaces as a starting layout constraint, not a strength guarantee. Screw-head/washer seat and bearing retention require additional local thickness.
- Keep repeated motor hole centres exact while tuning only clearances. Do not place nut pockets behind XM threaded motor-body holes.
- Use metal fasteners and nuts. Structural printed screws are not part of this design.

## Lightweight architecture
Proposed J2-J3 spacing 120 mm; J3-J4 spacing 100 mm; provisional distal wrist/tool chain 150 mm. Shoulder-to-tool horizontal reach about 370 mm. The 150 mm distal packaging must be verified using all four actual AX motor envelopes; do not shrink motors to fit the render.

Use a hollow ribbed closed box for each main link, local double-shear clevises, and small covers only where needed. Keep material away from the neutral axis; do not replace a torsionally stiff box with two unbraced decorative plates. Ventilated motor saddles and sparse cable clips replace large cosmetic motor shrouds.

Provisional print geometry for a 0.4 mm nozzle:
- Main link wall: 2.0-2.4 mm; internal ribs: 2.0 mm.
- Cosmetic removable covers: 1.2-1.6 mm.
- Bearing cheeks and bolt-bearing pads: 4-6 mm locally, subject to bore size and stress checks.
- Fillet rib/boss roots; preserve continuous material around bearing bores.
- Bambu Studio starting profile: 0.20 mm layer, about 5-6 wall loops where geometry allows, 5 top/bottom layers, 15-20% gyroid only in remaining enclosed bulk. Use local solid regions at fasteners and gear hubs. Final mass comes from sliced extrusion volume, not the infill percentage alone.
- Orient main links lengthwise on the bed with load-bearing skins continuous. Orient gear teeth in the XY plane. Check bearing-yoke layer orientation for peel/splitting; supports and surface finish remain part-specific.
- No automatic material change to carbon-filled nylon. PLA is the user's assumed baseline.

PLA sensitivity matters near warm motors: Bambu's cited PLA Basic TDS gives heat-deflection values of 54 degrees C at 1.8 MPa and 57 degrees C at 0.45 MPa. These are test results, not permissible arm service temperatures. Leave ventilation, measure bracket temperature and creep under actual duty, and do not use the servo's maximum allowable internal temperature as a PLA limit. If tests fail, revise bracket geometry/material rather than assuming the motor temperature shutdown protects PLA.

## Honest mass budget
Targets below include purchased moving hardware and wires separately. They are design allocations, not masses measured from CAD. Moving assembly above J2 is budgeted at 590.4 g without payload. Proposed moving printed parts total 145 g; all nonmotor moving parts total 290 g. Additional J2 drive hardware near the pivot, pedestal, J1 drive, turntable, base and electronics still add mass to the full robot. Do not report 590 g as total robot mass.

| Lump | Mass g | Horizontal coordinate from J2 mm |
|---|---:|---:|
| upper link print | 45.0 | 60 |
| upper link hardware | 25.0 | 60 |
| J3 XM430 | 82.0 | 120 |
| J3 reduction and support | 40.0 | 120 |
| forearm print | 35.0 | 170 |
| forearm hardware | 20.0 | 170 |
| J4 AX12 | 54.6 | 220 |
| J5 AX12 | 54.6 | 255 |
| J6 AX12 | 54.6 | 290 |
| gripper AX12 | 54.6 | 325 |
| wrist print | 40.0 | 270 |
| wrist hardware | 25.0 | 290 |
| gripper print | 25.0 | 345 |
| gripper rails and screws | 15.0 | 340 |
| moving cables | 20.0 | 190 |

## Static screening
Gravity torque: sum(mass x 9.80665 x horizontal lever arm). Shoulder at 0 mm; elbow at 120 mm; wrist pitch at 255 mm; payload at 370 mm. Only masses distal to a joint are included. Wrist printed parts are conservatively lumped distal to J5. This is one horizontal straight-arm screening pose, not the maximum over all six-axis poses.

| Payload | J2 shoulder | J3 elbow | J5 wrist pitch |
|---|---:|---:|---:|
| 0 g | 1.209 N m | 0.555 N m | 0.105 N m |
| 50 g | 1.390 N m | 0.678 N m | 0.162 N m |
| 100 g | 1.572 N m | 0.801 N m | 0.218 N m |
| 200 g | 1.935 N m | 1.046 N m | 0.331 N m |

Planning motor torque: 0.82 N m XM and 0.30 N m AX. These are estimates based on 20% of published 12 V stall torque, not independently validated continuous thermal ratings for this assembly.
Assumed external reduction efficiency: 80%. J2 4:1 -> 2.624 N m estimated output; J3 2:1 -> 1.312 N m estimated output; J5 direct -> 0.300 N m.
At 50 g: static ratios approximately 1.89, 1.94, 1.86 respectively.
At 100 g: approximately 1.67, 1.64, 1.38 respectively. Wrist pitch fails a chosen preliminary 1.5x static-reserve screen.
At 200 g: wrist pitch exceeds the estimated planning torque even before dynamics.

Therefore start commissioning unloaded, then use 50 g for slow-motion testing; 100 g remains a development goal, not a rated payload. The 1.5x screen is an engineering assumption, not a safety standard or structural factor of safety. Acceleration, gearbox losses beyond the assumed value, actual thermal behavior, off-axis loads, backlash, cable forces and printed-part strength require separate checks.

Removing 10 g at a 300 mm horizontal lever saves 0.0294 N m at the shoulder. Moving distal mass closer is more useful to shoulder torque than lightening the stationary base.

## Bearings, gears and force
No motor has a universal 'kg it can hold' rating. Output torque, radial/axial shaft load, output overhang, motor thermal duty, base overturning load and print stiffness are separate constraints.

ROBOTIS lists XM radial force 40 N (manual reference location 10 mm from horn) and axial force 20 N. These are not multi-kilogram arm payload ratings. AX shaft-load limits were not verified; do not infer them from stall torque.

Use independent output shaft bearings for J2/J3 and a moment-rated base turntable. External pinion shafts should also be bearing supported where gear force would overload motor bearings. The motor transmits torque via a suitable coupling.
Example only: 1.390 N m at a driven pitch radius of 40 mm gives about 34.8 N tangential gear force; a 20-degree pressure angle gives about 12.7 N separating force. These go into shaft/bearing/bracket calculations. Torque multiplication does not make these forces disappear.

A 1.390 N m moment reacted as a pure force couple across 40 mm bearing spacing corresponds to about 34.8 N per couple force, before additional weight and gear loads. This example illustrates the need for bearing spacing; it is not a bearing selection.

J1 remains AX with proposed external 3:1 gear reduction: at most 100 degrees total output travel from 300-degree joint mode, before margins. The bearing reduces rotation resistance and carries weight/moment; the gear adds reduction and friction. Check yaw acceleration and gear tooth load separately.
Gripper pinion must engage two opposed racks, with rails taking jaw moments. Force at the pads depends on pinion radius, efficiency, current/torque limit and object friction; no grip-force rating is released.

## Release gates
1. Match actual horns, manufacturer mounting coordinates and screw protrusion with a small PLA fit coupon.
2. Resolve six-axis motor packaging and collisions in dimensional CAD, including cable bends and tools for assembly.
3. Weigh sliced/printed parts and hardware; replace every budget mass and centre of gravity.
4. Check full-pose gravity loads, acceleration, pinion/bearing forces and print-layer load directions.
5. Bench-test brackets and gears; log servo and PLA bracket temperatures, deflection, backlash and creep. Increase payload only from evidence.

## Sources
- AX official dimensions: https://emanual.robotis.com/assets/images/dxl/ax/ax-12a_dimension.png
- AX manual: https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/
- ROBOTIS XM datasheet: https://media.distrelec.com/Web/Downloads/_t/ds/Dynamixel_XM-Series_eng_tds.pdf
- XM manual: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/
- XM torque/load estimates: https://robotis.us/products/dynamixel-xm430-w350-t
- Bambu PLA Basic TDS: https://store.bblcdn.com/s7/default/b189de92249a4b9ebed28b8ea1f080f0/Bambu_PLA_Basic_Technical_Data_Sheet.pdf
- Example M3 DIN 934 nut: https://www.accu.co.uk/hexagon-nuts/766485-NUT930M3C


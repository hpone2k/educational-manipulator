# EDU06 R03 motor-interface research

Checked 23 September 2026. These are manufacturer reference dimensions, not measurements of the user's individual hardware. Existing L01 mass/load calculations do not validate a new geometry.

## Motor envelope and datum

| Item | Published W x H x D (mm) | Mass | 12 V stall torque | Position range |
|---|---:|---:|---:|---|
| AX-12A | 32 x 50 x 40 | 54.6 g | 1.5 N m | 0–300 degrees in position mode |
| XM430-W350-T | 28.5 x 46.5 x 34 | 82 g | 4.1 N m | 0–360 degrees; extended position mode also available |

Sources: [AX eManual](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/), [XM eManual](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/).

AX output axis is 11.5 mm below the top edge in the official front drawing. Its side drawing has a 32 mm main body depth within the overall 40 mm dimension; horn and rear projections must be represented separately. XM output axis is 11.25 mm below the top. Its drawing shows horn projections separately from the 34 mm case depth. Do not put either motor axis at the centre of its height, shrink a motor to improve a render, or treat a specification envelope as a complete installation clearance.

Sources: [official AX drawing](https://emanual.robotis.com/assets/images/dxl/ax/ax-12a_dimension.png), [ROBOTIS-authored XM datasheet, distributor mirror](https://media.distrelec.com/Web/Downloads/_t/ds/Dynamixel_XM-Series_eng_tds.pdf). Local copies: `design-concepts/motor-references/ax-12a-dimensions.png`, `xm-drawing-review.png`, and `robotis-xm-datasheet.pdf`.

## Horn interfaces

- AX: four M2 tapped holes on a 16 mm pitch circle, cardinal spacing, drawing depth 4.0 mm. Hole centres relative to output axis: (+8,0), (0,+8), (-8,0), (0,-8) mm.
- XM HN12-N101 in the inspected drawing: eight M2 x 0.4 holes, 16 mm PCD, 45-degree spacing, maximum threaded depth 2.0 mm. Check the supplied horn revision and indexing with a coupon.
- XM body-side pattern in the inspected sheet is 12 x 24 mm, M2.5 x 0.45, maximum depth 3 mm. The pattern centre is not the output axis. Use a mechanically keyed cradle if the global interface datum is unresolved.
- Preserve the manufacturer's installed horn, centre screw and thrust washer. They are supplied motor components. The printed adapter attaches to the horn holes; it does not replace the motor spline.

Screw penetration equals under-head length minus the actual bracket/spacer/washer stack. A 4 mm AX adapter and M2x6 screw gives 2 mm nominal penetration. A 4.5 mm XM adapter and M2x6 screw gives 1.5 mm nominal penetration. These are design examples; verify actual stack and tolerances before assembly, leaving clearance from the blind-hole bottom. Preserve access to the central horn-retaining screw.

## Torque and mass implications

The seven motors total 437 g. J4/J5/J6 plus the gripper motor alone total 218.4 g. Wrist compactness is constrained by four real 32 x 50 x 40 mm AX envelopes.

ROBOTIS America's [AX bulk product page](https://robotis.us/products/dynamixel-ax-12a-6pcs-bulk) and [XM product page](https://robotis.us/products/dynamixel-xm430-w350-t) identify 0.30 N m and 0.82 N m respectively as estimated continuous torque values calculated at 20% of stall. These are screening assumptions, not independently measured continuous torque for this PLA assembly. The single AX product page currently contains an inconsistent 0.2 N m stall entry; the eManual and bulk page agree on 1.5 N m, which is used here.

XM eManual gives radial load 40 N at 10 mm from the horn and axial load 20 N. These do not specify payload at the robot tool. No AX shaft-load limit was verified. Printed journals and supports must react arm moments instead of assuming unlimited motor-bearing capacity. Extra gear reduction multiplies available output torque but adds friction, backlash and gear forces. AX 3:1 external reduction permits only 100 degrees total output travel from its 300-degree position range, before end margins.

## U2D2 and wiring

[ROBOTIS U2D2 manual](https://emanual.robotis.com/docs/en/parts/interface/u2d2/): case 48 x 18 x 14.9 mm, 9 g. It is a small USB communication converter, not a motor or a motor power supply. Include a separate power entry and preserve cable access. USB changed from Micro-B to Type-C in August 2025, so an open-ended cradle/cable opening should allow either. A keyed tray and removable printed strap avoid relying on unverified mounting-hole coordinates.

AX uses TTL Protocol 1.0; XM-T is TTL and normally Protocol 2.0 (Protocol 1.0 configurable on supported firmware). Plan matched connector cables, unique IDs and a compatible control scheme; do not imply the Blender rig drives real hardware.

## Printing-specific implementation assumptions

Recommended starting CAD trial clearances, not manufacturer specifications: 0.3–0.4 mm per cradle side; M2 clearance 2.3 mm, M2.5 clearance 2.8 mm, M3 clearance 3.4 mm. Change clearance diameters after a fit coupon, never the manufacturer hole-centre spacing. All added shafts, journals, thrust pads, gears and structural components must be printed for this user's materials constraint. Printed sliding bearings need friction/wear/creep tests; a motion animation cannot validate them. Do not add purchased metal bearings or rods to the BOM.

# EDU06 R03 motor and fastener guide

This guide describes the current Blender generator's motor interfaces and fastening stacks. It is a prototype assembly guide, not evidence of physical fit, carrying capacity or successful powered operation. Dimensions are millimetres. Check the final `motor-interface-schedule.json` against the supplied hardware before printing the complete arm; that schedule records each generated motor transform and fastening stack.

## Materials and purchased components

Fabricated cradles, caps, shafts, bearings, gears, links, spacers and feet are printed filament. The additional fastening hardware is screws and nuts. Motors retain their supplied cases, horns, centre screws and internal components. Electronics and cables are purchased components. No added metal bearing, shaft, guide rod, bracket or washer is specified by these motor assemblies.

## Motor datum and verified interfaces

For every motor, local `(0,0,0)` is the **front face of its installed horn**. The output axis is local **+Z**; case height follows local **Y**. Parent transforms in the interface schedule place this datum into the arm. The motor output axis is not the centre of the rectangular case.

| Dimension or coordinate | AX-12A | XM430-W350-T |
|---|---:|---:|
| Published width × height × depth | 32 × 50 × 40 | 28.5 × 46.5 × 34 |
| Case top Y / bottom Y | +11.50 / −38.50 | +11.25 / −35.25 |
| Main case front Z / back Z | −4.00 / −36.00 | −2.20 / −36.20 |
| Rearmost modeled case Z | −40.00 | −36.20 |
| Installed reference depth, horn front to rearmost case | 40.00 | 36.20 |
| Front cradle bezel Z, back to front | −3.65 to −1.05 | −1.85 to −0.25 |
| Rear-cap front Z / rear Z | −40.35 / −44.95 | −36.55 / −41.15 |
| Four cradle-post X coordinates | ±21.00 | ±19.25 |
| Cradle-post Y coordinates | +15.50, −42.50 | +15.25, −39.25 |
| Cradle rectangular hole-centre spacing | 42.00 × 58.00 | 38.50 × 54.50 |

The AX main body, front horn and rear projections are modeled separately within its 40 mm installed depth. The XM published 34 mm case depth has a separately modeled 2.2 mm front horn projection. These envelope models do not reproduce every manufacturer surface feature. Connector details in Blender illustrate the access space; compare actual plugs and wires with the printed rear window.

The AX horn has four M2 holes on a 16 mm pitch circle: `(8,0)`, `(0,8)`, `(−8,0)`, `(0,−8)`. The XM reference horn has eight M2 holes on the same pitch circle, spaced 45 degrees apart. Manufacturer drawing thread-depth limits used here are 4 mm for AX and 2 mm for the inspected XM horn. Confirm the supplied horn revision before attaching a printed part. The cradles locate the motor case mechanically and do not rely on guessed motor-body mounting holes.

Manufacturer references: [AX-12A eManual](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/), [AX dimensional drawing](https://emanual.robotis.com/assets/images/dxl/ax/ax-12a_dimension.png), [XM430 eManual](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/), and the locally retained ROBOTIS XM dimensional drawing described in `research-motors.md`.

## Cradle fit and rear fastening

Each cradle provides 0.35 mm nominal clearance per case side and a 26 mm front horn window. Its rear cap is 4.6 mm thick. Two removable 0.30 mm axial shims reduce the modeled total front/rear clearance from 0.70 to 0.10 mm. These are initial print-fit allowances, not guaranteed printed results.

The **four M3 nuts are captive at the front of the cradle posts**. Their pockets are 5.8 mm across flats and 2.8 mm deep. Posts have a 4.6 mm radius, leaving approximately 1.25 mm of plastic outside the nut-pocket corners. The reference M3 nut is 5.5 mm across flats and 2.4 mm thick. All through holes in this stack are 3.4 mm diameter.

Screws enter from behind the supporting wall, through the rear printed spacer, supporting wall and any structural standoff, rear cap, and cradle post. Their shafts point along local +Z into the front captive nuts. Screw heads and length-adjusting spacers therefore remain behind the motor mounting structure, clear of the front gear plane. There are no additional rear-cap nuts or duplicate outer nuts.

The following table is derived from the current `make_motor` function and builder attachment depths. Each listed unit has four identical M3 screws, four front M3 nuts, and four rear spacers.

| Unit | Motor | Attachment depth behind cap | Screw, under-head length | Rear printed spacer thickness |
|---|---|---:|---:|---:|
| J1 base rotation | AX | 20.05 | M3 × 65 | 1.15 |
| J2 shoulder | XM | 15.35 | M3 × 60 | 3.85 |
| J3 elbow | XM | 15.35 | M3 × 60 | 3.85 |
| J4 forearm roll | AX | 6.00 | M3 × 50 | 0.20 |
| J5 wrist pitch | AX | 4.00 | M3 × 50 | 2.20 |
| J6 tool roll | AX | 4.00 | M3 × 50 | 2.20 |
| Separate gripper actuator | AX | 12.00 | M3 × 60 | 4.20 |

This motor-cradle subtotal is **4 M3×65, 12 M3×60, 12 M3×50 and 28 M3 nuts**. It excludes other arm, gear, journal and enclosure fasteners. Use the rear-spacer STL belonging to that particular motor; similar-looking spacers have different thicknesses.

The calculation uses `B = rear_cap_back`, `D = attachment_depth`, `F = front_bezel_front`, all in the motor frame:

```text
rear wall outer plane = B − D
front nut top        = F − 0.20
front nut bottom     = F − 2.60
target screw tip     = F − 0.10
screw length         = 5 × ceil((target tip − rear wall outer plane) / 5)
under-head Z         = target screw tip − screw length
rear spacer thickness = rear wall outer plane − under-head Z
```

The nominal tip projects 0.10 mm beyond the nut while remaining 0.10 mm behind the cradle front plane. Inspect the actual assembled stack: printed thickness errors and screw-length tolerances can change this small clearance. The old `attachment_nut_recess` argument is deprecated and does not affect this calculation.

The base has separately printed **8 mm feet** to provide underside screw-head clearance. Preserve those feet and the supporting floor/standoff arrangement. Reference socket heads are M2 Ø3.8 × 2 mm high, M3 Ø5.5 × 3 mm high, and M4 Ø7 × 4 mm high. Match the actual purchased head profiles and allow driver access, especially behind the wrist.

The five enclosure-lid nuts and four rotating-deck flange nuts are **loaded through side slots**, leaving plastic roofs above them to react the upward bolt pull. Insert these nuts before closing their access. Lid pockets occupy Z85.2–88.0 with 2 mm roofs; their M3×12 screws remain under-head Z95. The rotating flange pockets occupy Z106.8–109.6 with 2.4 mm roofs. Its four M3×12 screws use 0.8 mm printed spacers above the deck: heads seat at Z118.8 and tips end at Z106.8, above the collar that ends at Z106. These coordinates are in the fixed base frame for the lid and the yaw frame for the rotating flange.

## Horn screw stacks

Screw length below the head minus the complete printed stack gives nominal thread penetration. The values below assume no additional washer. Retain the manufacturer's central horn-retaining screw and leave access to it.

| Interface | Quantity per actuator | Screw | Printed stack under head | Nominal horn penetration | Drawing depth limit |
|---|---:|---|---:|---:|---:|
| AX J4/J5/J6 raised output adapter | 4 | M2 × 10 | 7.0 | 3.0 | 4.0 |
| AX J1 yaw pinion | 4 | M2 × 6 | 4.0 counterbore floor | 2.0 | 4.0 |
| AX driven gripper gear | 4 | M2 × 6 | 4.0 counterbore floor | 2.0 | 4.0 |
| XM J2/J3 pinion | 8 | M2 × 6 | 4.5 counterbore floor | 1.5 | 2.0 |

This horn-fastener subtotal is **12 M2×10 and 24 M2×6**. The supplied motor-centre screws are additional retained hardware. The modeled M2 clearance diameter is 2.3 mm. Check actual under-head length and printed floor thickness with calipers, particularly the XM stack with its 0.5 mm nominal depth margin. Do not tighten a screw that bottoms before the printed adapter seats.

## Fit trials and assembly sequence

1. Confirm the actual actuator labels, supplied horns, nut dimensions, screw lengths and head profiles. Keep the motors unpowered while fitting brackets. Print the general hole/nut coupon first on the Bambu A1 using the intended filament and print settings. Its ranges are Ø3.2/3.4/3.6, Ø8.3/8.5/8.7 and 5.6/5.8/6.0 mm across-flats pockets.
2. Print the separate `F02_AX_16PCD_horn_coupon` and `F02_XM_16PCD_horn_coupon` before their gears. They provide unobstructed four-hole and eight-hole patterns respectively, both on a 16 mm pitch circle. The AX coupon is 4 mm thick and the XM coupon is 4.5 mm thick; M2×6 gives the same nominal 2 mm / 1.5 mm engagement as their corresponding pinion floors. F01 is exclusively the general hole/nut-fit coupon.
3. Print one cradle, cap and matching shims as a physical sample. Remove supports and any burrs from seating faces, bores and nut pockets. Check that nuts seat without splitting the posts, the case slides in without force, the horn remains free, and both connector plugs can be inserted and removed. Adjust clearance or shim thickness from measurements; keep the manufacturer hole-centre coordinates fixed.
4. Insert the four front captive nuts before installing gears that would obstruct access. Place the front shim against the cradle retaining lip; insert the motor from the rear with its horn through the 26 mm window. Add the rear shim and cap. Check seating before tightening anything.
5. Align the cradle, structural standoffs and supporting wall with the four scheduled hole centres. Place the appropriate rear spacers behind that wall, then insert the scheduled M3 screws from the rear. Tighten evenly only enough to seat the stack. Confirm that the case is retained without distortion and that the front tips remain recessed. Nut retention and tightening torque require physical validation; no tightening torque is prescribed here.
6. Fit the horn adapter or pinion using its M2 stack from the table. Check central-screw access and screw-head counterbores before fitting an outboard support that covers them. Test each printed journal and mating bore as a small physical sample. Confirm free rotation, axial clearance and gear contact before loading the complete arm; do not force a stationary servo gearbox by pulling on a long link.
7. Inspect the assembled range slowly while supporting the arm. Check rear screw heads, gear sweeps, printed thrust faces and real cable service loops. STL mesh checks and Blender animation do not establish friction, wear, creep, temperature rise or payload. Those require staged physical testing before powered use under load.

Very thin rear spacers and the 0.30 mm motor shims need suitable layer settings and a measured result. Select print orientation and supports to preserve the motor lips, nut-pocket walls, journal surfaces and load-bearing layers. Do not interpret a closed STL or a successful slicer preview as proof that those features will fit or carry the required moment.

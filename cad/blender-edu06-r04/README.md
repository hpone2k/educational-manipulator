# EDU06 R04 — centred wrist and parallel gripper

Open **EDU06_R04.blend**. This revision replaces the sideways wrist adapters with an aligned roll–pitch–roll assembly and larger parallel fingers. The green/ivory render is produced from this editable assembly. R03 is preserved in its separate folder.

## Inspect and move

The saved engineering scene shows the assembled robot. Select the **CONTROL** object and expand **Object Properties → Custom Properties**. J1–J6 are output angles in degrees. **GRIP is the clear jaw opening in millimetres**, from 20 to 70 mm. Space plays the 360-frame demonstration; stop playback before editing. Keyframed values return as the timeline moves. NumPad 0 leaves/enters the camera view; middle-mouse orbits. In Solid shading, Alt+Z toggles X-ray.

The second scene, **Individual print parts**, separates the printable components on a display grid. It is an inspection layout, not a single slicer plate. Collection 01 contains printable parts; motors, screws, nuts, electronics, cables and presentation objects are excluded from STL export.

## Main dimensions

| Interface | Nominal CAD dimension |
|---|---:|
| AX-12A published envelope | 32 × 50 × 40 mm |
| XM430 published main case | 28.5 × 46.5 × 34 mm; projections modelled separately |
| Shoulder–elbow pivot spacing | 100 mm |
| J4 roll datum–J5 pitch datum | 78 mm |
| J5 pitch datum–J6 horn datum | 41 mm |
| J6 horn–gripper horn datum | 74.45 mm |
| Neutral J4 datum–gripper tip plane | 293.45 mm |
| Finger body, each | 75 × 24 × 12 mm, lightened with open rear pockets |
| Replaceable contact pad thickness | 3 mm, with 1.2 mm-deep central V |
| Clear parallel opening | 20–70 mm |
| Roll journal / fixed bore | Ø40 / Ø40.5 mm; 16 mm nominal sleeve length |
| Pitch trunnion / fixed bore | Ø20 / Ø20.5 mm |
| M2 / M3 printed clearance trials | Ø2.3 / Ø3.4 mm |
| M3 captive-nut trial | 5.8 mm across flats, 2.8–2.9 mm depth |

These are model dimensions, not a promise of as-printed accuracy. Flat lands contact rectangular objects; the shallow V helps locate round ones within the opening range. Grip force and slip depend on the printed surfaces and object. No universal tool capacity is assigned.

## Motors and reductions

| Axis | Motor | External drive | Declared output travel |
|---|---|---|---:|
| J1 base yaw | AX-12A | 20/60 teeth, module 1.5, 3:1 | −40°…+40° |
| J2 shoulder pitch | XM430-W350-T | 20/100, module 1.25, 5:1 | 60°…85° |
| J3 elbow pitch | XM430-W350-T | 20/80, module 1.25, 4:1 | 30°…75° |
| J4 forearm roll | AX-12A | Direct, external printed support | −40°…+40° |
| J5 wrist pitch | AX-12A | 20/60, module 1.5, 3:1 | −25°…+25° |
| J6 tool roll | AX-12A | Direct, external printed support | −60°…+60° |
| Gripper | AX-12A | 20T, module 1.5 pinion; opposing racks | 20–70 mm gap |

The six arm axes use six motors; the gripper uses a seventh. The elbow's fixed gearbox is clocked 90° away from the shoulder; its output zero is unchanged. Gear profiles use 20° involutes and explicit nominal backlash. The motor phase shown by a Blender driver is not a calibrated hardware goal-position command.

The shoulder's 60° lower operating limit follows the gravity calculation for the larger gripper. More extended poses exceeded the motor planning comparison. These operating limits constrain the prototype's workspace; they are not a physical payload certification.

Actual ROBOTIS exterior CAD supplies motor cases, connector geometry, body holes and stock horns. Details and the XM drawing/STEP revision discrepancy are in `motor-references/README-official-cad.md`. Printed cradles capture the cases; fabricated parts do not rely on guessed motor-body drilling positions. Supplied horns and their original retention hardware remain part of the purchased motors.

## Assembly order for the new wrist

1. Print fit coupons first. Check the actual screws, nuts, horn pattern and clearances against your motors.
2. Capture J4 in its keyed cradle on the forearm. Fit its printed annular output and M2 × 6 horn screws. Fit four flange nuts before installing the centred fork with M3 × 10 screws. The central opening preserves horn-screw access before downstream components are added.
3. Install the J5 motor in the fork. Install its pinion and M2 × 6 horn screws before the removable outboard journal bridge. Fit the matching printed foot/head spacers and M3 × 70 bridge fasteners.
4. Place the moving J6 carrier inside the fork. Insert the two separate printed trunnions from the sides, then fasten each with four M3 × 20 screws into its captured nuts. The journals have running clearance; tightening their screws must not clamp the fixed cheeks. Add the 60T gear using its recessed M3 × 12 seats.
5. Capture J6, then assemble its annular output and gripper rear palm while the gripper motor is absent. Fit the output horn screws through the central access opening. Four PCD 48 palm screws use **1 mm printed spacers and M3 × 12 screws** so their tips clear the fixed roll sleeve.
6. Insert the gripper's rear cradle nuts before mating its palm. Install the gripper motor from the front and use the recessed **M3 × 45 front-inserted cradle screws**. These replace inaccessible rear screw heads.
7. Fit the gripper's rear-to-front standoffs, lower rails and pinion. Lower the opposed carriages into the rails from above, then install the retaining lips and journal bridge. End stops prevent insertion from the rail ends. Attach the thick fingers, slide in their keyed pads, and install the removable tip stops.

The exact added screw/nut quantities are in `hardware-bom.json`. Printed spacers are separate parts. No added metal bearing, rod, bracket, insert, spring or rubber pad is assumed. Connector service loops remain visual routing references; actual cables require clearance checks throughout motion.

## Printing and commissioning

All exported parts use millimetres and are checked against the A1's 256 mm nominal build cube. Print one part or a deliberate slicer arrangement, not the assembled robot. Leave room for brim and printer exclusions. PLA is a provisional interpretation of “normal filament”; measure printed mass and fit before accepting the model's assumptions.

Begin with the hole/nut and horn coupons, then one motor cradle and one bearing fit. Gears normally print flat with their axes vertical. Finger pockets and T slots should face upward in the supplied print orientation. Large yokes and the open case require slicer support/orientation review. Load-bearing perimeters, layer direction, creep, motor heat and tooth strength have not been qualified by a material test.

Start any physical assembly unpowered and turn every joint through its allowed range by hand. Investigate binding before powering motors. Blender playback checks geometry and kinematics; it does not measure dry polymer friction, real backlash, print strength or motor temperature. The separate U2D2 is a communication interface and does not power the motors.

Read **engineering-review.md** for the actual geometry checks, torque assumptions and release limitations. This is an editable, dimensioned engineering prototype; a physical payload rating remains unassigned.

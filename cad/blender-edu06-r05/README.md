# EDU06 R05 — six motors, curved upper structure

Open **EDU06_R05.blend**. This revision uses exactly **four AX-12A and two XM430-W350-T motors**. Five motors position the arm; the sixth opens and closes the gripper. It has **five arm DOF plus one gripper coordinate**. The earlier separate forearm-roll motor is removed. R04 is preserved in its own folder.

The base enclosure, turntable and yaw drive retain the R04 design. Above the base, rounded outlines, open motor saddles, curved bearing supports and oval reliefs replace the box-like shapes. The shorter wrist has a fixed forearm flange, geared pitch and supported tool roll. These shapes are printable structure, not decorative covers.

## Motors and motion

| Control | Motor | Drive | Configured travel |
|---|---|---|---|
| J1 — base yaw | AX-12A | 20/60 teeth, module 1.5, 3:1 | −40°…40° |
| J2 — shoulder pitch | XM430-W350-T | 20/100, module 1.25, 5:1 | 45°…90° |
| J3 — elbow pitch | XM430-W350-T | 20/80, module 1.25, 4:1 | 30°…75° |
| J4 — wrist pitch | AX-12A | 20/60, module 1.5, 3:1 | −25°…25° |
| J5 — tool roll | AX-12A | Direct, external printed support | −60°…60° |
| GRIP — jaw opening | AX-12A | 20T pinion and opposed racks | 20–70 mm clear gap |

Gear reduction increases output torque while reducing speed and angular travel. It does not eliminate printed-bearing friction. Blender motor phases are kinematic relationships, not calibrated hardware position commands.

Select **CONTROL** and expand **Object Properties → Custom Properties**. J1–J5 are output angles in degrees; GRIP is the clear opening in millimetres. Space plays the 360-frame demonstration. Stop playback before editing; moving the timeline reapplies its keyframes. NumPad 0 enters/leaves camera view. Middle-mouse orbits; in Solid shading, Alt+Z toggles X-ray.

The **Individual print parts** scene displays the separate printable components. It is an inspection grid, not a slicer plate. Collection 01 contains printable geometry; motors, screws, nuts, cables, electronics and studio objects are excluded from STL export.

## Dimensions and interfaces

All CAD and STL dimensions are millimetres. Actual ROBOTIS exterior STEP geometry supplies motor bodies, connector shapes, body holes and stock horns. See **motor-references/README-official-cad.md** for source drawings, datums and the XM STEP/drawing discrepancy. The cradles capture the cases rather than relying on guessed body-hole positions.

AX-12A published envelope: 32 × 50 × 40 mm. XM430 main case: 28.5 × 46.5 × 34 mm, with horn/idler projections modelled separately. Shoulder–elbow pivot spacing: 100 mm.

The fixed forearm flange has a 60 mm outside diameter, 26 mm central access opening, 10 mm axial thickness and four M3 holes on a 48 mm pitch circle. Captive nuts enter radially. The mating 5 mm wrist heel uses front-inserted M3 × 12 screws.

The gripper retains 75 × 24 × 12 mm finger bodies, lightened behind the contact surfaces, with separate 3 mm keyed pads. Flat lands contact rectangular objects; a shallow V helps locate round objects within the 20–70 mm opening. Shape does not establish grip force or slip resistance.

Provisional running fits: roll journal/bore Ø40/Ø40.5 mm; pitch trunnion/bore Ø20/Ø20.5 mm. M2/M3 clearance trials: Ø2.3/Ø3.4 mm. M3 captive pockets: 5.8 mm across flats. Print coupons and compare them with actual filament, nuts, screws and motor revision.

**wrist-dimensions.json** gives final wrist datums. **print-parts.csv** lists exported parts, bounds and solid-PLA mass estimates. **hardware-bom.csv** lists added screws/nuts; factory hardware supplied with motors is separate. Detailed mounting stacks are in **motor-interface-schedule.json** and **hardware-bom.json**.

## Assembly sequence

1. Print the hole/nut and motor-horn coupons. Check a cradle and a printed journal fit before committing to all parts.
2. Assemble the unchanged base, printed yaw bearings, geared shoulder and elbow. Their external output bearings carry bending loads independently of the motor horns.
3. Insert four M3 nuts radially into the fixed forearm flange. Attach the wrist heel with front-inserted M3 × 12 screws. Keep the central opening accessible.
4. Assemble the J5 tool-roll motor, rear capture plate and supported sleeve as a separate moving unit. Tighten its rear screws before sliding the unit into the fixed fork. Insert the two trunnions from the sides and fasten them; they must clamp the moving unit without locking the stationary cheeks.
5. Install the 60T pitch wheel and fixed J4 motor/pinion. Tighten the motor's rear screws from the open back, then install its removable pinion journal bridge. Attach the gripper rear palm while its own motor is absent, preserving straight driver access to roll horn and palm screws.
6. Insert the gripper captive nuts and motor. Its cradle screws enter from the front. Assemble rails, pinion and opposed carriages; install removable guide lips after inserting the slides.
7. Attach the fingers, slide in the keyed pads and install tip stops. Check travel, end stops and free movement by hand before powering.

Printed structures, gears, shafts, sleeves, spacers and pads require no additional metal brackets, bearings, rods, inserts or springs. Motors retain their supplied components. Cable routes are visual references; actual wires need service loops and motion clearance checks. U2D2 provides communication, not motor power.

## Printing and validation

Exported part bounds are checked individually against the A1's nominal 256 mm build cube. Leave room for brims and printer exclusions. PLA is a provisional interpretation of “normal filament”; measured mass, layer adhesion, creep and heat resistance can differ from assumptions.

Gears normally print flat with their axes vertical. Review support and layer direction for yokes, slides and the base. Print fit coupons first.

Read **engineering-review.md** and the JSON reports for this revision's actual results. Discrete collision samples and gear checks do not establish continuous cable clearance, strength, dry-bearing friction, thermal duty cycle or a physical payload rating. This is a dimensioned engineering prototype. Begin commissioning unpowered, then unloaded, and measure friction, deflection and temperature before assigning carrying capacity.

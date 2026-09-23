# EDU06 R06 — centred, bilateral printed arm

Open **EDU06_R06.blend**. This prototype uses exactly **four AX-12A and two XM430-W350-T motors**: five arm axes plus a powered gripper. It has **five arm DOF and one jaw-opening coordinate**, not six independently controlled arm axes.

R06 supports the upper arm and forearm from both sides. Each geared joint has an independent printed output shaft, front bolted flange and positively keyed rear flange. Matched curved side plates connect these outputs, replacing the previous offset link arrangement. Shoulder–elbow pivot spacing is **100 mm** with no lateral centre offset; the wrist mounts to a removable crossmember centred between the forearm plates. These printed journals carry bending around the motor output; their friction and load capacity still require physical testing.

## Inspect and move the model

Select **CONTROL**, then **Object Properties → Custom Properties**. J1–J5 are output angles in degrees; GRIP is the clear jaw gap in millimetres. Space plays the 360-frame demonstration. Stop playback before editing a control: changing frames reapplies its keyframes. Middle-mouse orbits, NumPad 0 toggles camera view, and Alt+Z toggles X-ray in Solid shading.

The **Individual print parts** scene is an inspection grid, not a slicer plate. Collection 01 contains printable parts. Purchased motor references, screws, nuts, electronics, cables, reservation boxes and studio objects are not printed.

| Control | Motor | Drive | Configured travel |
|---|---|---|---|
| J1 — base yaw | AX-12A | 20/60 teeth, module 1.5; 3:1 | −40°…40° |
| J2 — shoulder pitch | XM430-W350-T | 20/100, module 1.25; 5:1 | 45°…90° |
| J3 — elbow pitch | XM430-W350-T | 20/80, module 1.25; 4:1 | 30°…75° |
| J4 — wrist pitch | AX-12A | 20/60, module 1.5; 3:1 | −25°…25° |
| J5 — tool roll | AX-12A | Direct, with external printed support | −60°…60° |
| GRIP — jaw opening | AX-12A | 20T pinion and opposed racks | 20–70 mm |

Reduction trades speed and travel for output torque. Blender's gear phases are kinematic relationships; they are not calibrated hardware position commands.

## Dimensions and service space

All model and STL dimensions are **millimetres**. Official ROBOTIS exterior STEP geometry supplies motor bodies, stock horns and connector shapes. The cases are mechanically captured by printed cradles; no guessed motor-body hole pattern is used. AX-12A's published envelope is **32 × 50 × 40 mm**; the XM430 main case is **28.5 × 46.5 × 34 mm**, with projections modelled separately. See [motor CAD sources and datums](motor-references/README-official-cad.md).

- **Base:** measured maximum enclosure **241 × 240 × 95 mm**, plus 8 mm printed feet. The nominal shell/lid footprint is 240 × 240 mm; front-panel support arms add 0.5 mm on each side. The open front has a removable panel, and the structural lid removes for drive access. The original yaw centre at X = −28 mm, gear elevations and pedestal mounting interface are retained.
- **Controller bay:** 100 × 65 × 30 mm of reserved clear space above a removable slotted tray. It accommodates a controller-sized envelope without assuming an Arduino mounting-hole pattern. Choose standoffs and screw lengths from the actual board.
- **U2D2:** a separate **48 × 18 × 14.9 mm** reference, retained by its own tray and removable printed strap. USB plug withdrawal space, rear cable outlets and screw-fastened split cable saddles are provided. The larger controller bay is additional space; the U2D2 itself is small.
- **Power hardware:** a separate 45 × 35 × 22 mm reserved envelope and slotted plate. Its actual board, fuse, terminals, supply and current rating remain unselected.
- **Wrist interface:** the flange front datum is **X = 78.8 mm from the elbow pivot**, centred at Y = Z = 0 in the forearm frame. Its Ø60 mm neck joins the crossmember behind the wrist gear sweep; the front has Ø26 mm central access and four M3 holes on a Ø48 mm pitch circle. A 5 mm wrist heel bolts to it from the front.
- **Gripper:** 75 × 24 × 12 mm finger bodies with lightening pockets, separate 3 mm keyed pads, flat contact lands and a shallow V. Shape and opening range do not establish grip force or slip resistance.

[base-layout.json](base-layout.json) records the clear bays and installed panel transform; [wrist-dimensions.json](wrist-dimensions.json) and [gripper-design-notes.json](gripper-design-notes.json) record local datums and assembly details. Use [motor-interface-schedule.json](motor-interface-schedule.json), [hardware-bom.json](hardware-bom.json) and the generated CSVs to identify the actual fastener stacks.

## Assembly order

1. Print the hole/nut and AX/XM horn coupons. Measure the supplied motors and hardware; trial-fit a cradle, gear mesh, journal and slide before printing the complete set.
2. Install the base feet, lower yaw support, printed shaft/bushings and motor drive. Fit the trays and actual electronics with the front panel removed. Leave the lid open while checking connectors and cable access.
3. Preload captive nuts before closing their access. Assemble the shoulder's fixed cheeks, sleeves, independent output shaft and keyed rear flange. Fit both upper-arm plates with their front spacers and rear bolts. The central retainer must clamp the rotating shaft/flange stack while preserving clearance to stationary cheeks.
4. Build the elbow reducer on its own fixed cheek ties. Attach its outer mounting ears to both upper-arm plates through the separate support posts. Fit both forearm plates to the elbow's front and keyed rear outputs, then bolt the centred wrist crossmember between their ends.
5. Load the wrist-flange nuts and attach the empty wrist heel using four front-inserted M3 × 12 screws. Preassemble and tighten the J5 motor/carrier before inserting it into the pitch fork. Install its removable side trunnions, pitch gear and J4 drive; fit the pinion journal bridge last.
6. Attach the gripper palm through its four printed service-gap posts, keeping its motor absent so the roll horn and palm screws remain accessible. Route the AX leads through the rear connector passage and open gap before installing the front-loaded motor. Then fit the pinion, carriages and removable guide lips; attach fingers, slide in pads and secure the tip stops.
7. Route and secure the actual harness, then move every joint and the gripper by hand with power off. Check bearing freedom, nut retention, cable slack and tooth clearance before fitting the lid and service panel.

All custom brackets, gears, shafts, sleeves, spacers and pads are printed. Purchased motors retain their factory components; additional mechanical metal is screws and nuts. U2D2 provides communication, **not motor power**. Read [wiring-notes.md](wiring-notes.md) for the separate supply, AX/XM connector conversion, mixed protocols and provisional harness assumptions.

The gripper harness also has supplementary bend and strand-spacing checks across 275 wrist combinations; see [wiring-evidence.md](wiring-evidence.md). Its guide points remain routing references pending physical cable fitting and retention.

## Print and commission

Import individual **prototype_stl/** files into Bambu Studio in millimetres. The largest case STL is 241 × 240 mm and the lid is 240 × 240 mm; leave room within the A1's nominal 256 mm plate for the selected brim and printer exclusions. Preview every plate, support interface and hole rather than treating the Blender inspection layout as a print job. Gears normally print flat with their axes vertical; inspect layer direction and supports for the forks, base, fingers and slides.

PLA is a provisional interpretation of “normal filament.” Trial dimensions include Ø2.3/Ø3.4 mm M2/M3 clearances, 5.8 mm across-flats M3 nut pockets and 0.25 mm radial journal clearance. Actual filament, layer orientation, shrinkage and hardware variation govern final fits. Exported solid-PLA mass estimates are not slicer or weighed masses.

Consult [engineering-review.md](engineering-review.md) and this revision's dated mesh, gear, motion, wiring and mass/load reports for the recorded results and their scope; earlier revision checks do not validate new parts. Discrete collision checks and a moving Blender model do not establish continuous cable clearance, strength, friction, heat limits or a physical payload rating. Commission unloaded first and measure deflection, joint friction and motor temperature before assigning an operating load or duty cycle.

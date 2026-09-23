# Polymer Arm Studio — P03

An interactive, dimensioned five-axis plastic-arm concept based on the supplied modular servo-arm image. Open `http://127.0.0.1:4173/polymer-studio/index.html` after running `npm start` in the parent project folder. Three.js is served locally; the page needs no external account or service.

P03 restores the original dark-green ORBIT theme and adds rounded cover lips, raised shell detailing, concentric joint caps, recessed socket screws, a base nameplate, braided wiring with printed clips and strain reliefs, and more detailed generic actuators. Lighting uses a local studio reflection environment, filtered shadows, multisample antialiasing and ambient occlusion. X-ray bypasses ambient occlusion so transparent covers do not obscure the interior.

## Explore

- **Exterior:** complete plastic housings and joint covers.
- **X-ray:** transparent structural shells reveal actual modeled ribs, fastening bosses, bearings, shafts, wiring and generic motor bodies. This is a display mode, not an X-ray scan or a physical simulation.
- **Open covers:** remove the five main shell covers.
- **Separate covers:** move the covers away from their mating faces for inspection.
- **Motion:** pose all five joints and the gripper, choose a preset or play a 12-second study. Escape or manual input stops the animation.
- **Parts:** inspect nominal dimensions, focus a component, examine the M3 boss and hexagonal nut pocket, and download specification JSON or dimension CSV. In the fastening close-up, the nut is displaced along the bolt axis to expose its pocket; Fit returns to the arm.
- **Loads:** estimate static gravity moments with an adjustable payload and component mass assumptions.
- **Inspect motors:** examine a generic servo and 42 mm pancake stepper in a separate close-up. These use the same geometry as the assembled arm, including mounting ears, case seams, output horns, connectors, lead wires, laminations and end plates. Fit returns to the arm.

## Nominal dimensions

| Feature | Dimension |
|---|---|
| Base envelope | 180 × 160 × 32 mm |
| Base wall | 4 mm |
| Anchor pattern | 150 × 130 mm, four Ø6.6 mm holes |
| Shoulder axis above ground | 120 mm |
| Upper link pivot spacing | 180 mm |
| Upper link cover envelope | 232 × 52 mm; section depth 62 mm |
| Forearm pivot spacing | 150 mm |
| Forearm cover envelope | 194 × 44 mm; section depth 46 mm |
| Link walls / covers / cross ribs | 3 mm nominal |
| Wrist pitch to roll axis | 52 mm |
| Roll axis to tool centre | 78 mm |
| Gripper clear opening | 0–50 mm, measured between the inner pad faces |
| Guide rods / provisional slider bores | Ø4 mm rods, 84 mm span; Ø4.3 mm trial bores |
| Structural shaft | Ø8 mm |
| Reference 608 bearing | 8 mm ID × 22 mm OD × 7 mm width |
| Trial printed bearing seat | Ø22.2 mm × 7.2 mm depth |
| M3 bolt clearance | Ø3.4 mm |
| Printed captive-nut boss | Ø12 mm × 9 mm long |
| Hexagonal nut pocket | 5.8 mm across flats × 2.8 mm deep |
| Reference M3 nut | 5.5 mm across flats × 2.4 mm thick |

Dimensions are explicit nominal design values, not measurements of the user's hardware. Section dimensions describe the principal shell envelope and exclude exterior screw heads, joint end caps, raised face detailing, clips and cable loops. Nominal wall thickness excludes local relief and chamfers. Bearing, guide and nut allowances require print coupons and appropriate retention details. The four base feet preserve the Ø6.6 mm anchor passages.

The manufactured base, links, covers, joint supports, nut pockets and motor cradles are plastic. Motors, rolling bearings, shafts, bolts, nuts and guide rods remain separate purchased hardware. Polymer support features do not imply printed structural bolts or bearing balls.

## Mechanical scope

The model uses five serial revolute joints: base yaw, shoulder pitch, elbow pitch, wrist pitch and tool-axis roll. Gripper opening is separate. Three.js uses Y up; displayed robotics coordinates are X = scene X, Y = −scene Z, Z = scene Y.

The torque panel computes signed gravitational moments, then displays magnitudes, using τ = Σ(m g r_horizontal). Link mass is placed at each link's midpoint. Motor masses are placed at the elbow and wrist-pitch pivots. Tool mass is at the midpoint between the roll axis and tool centre; payload is at the tool centre. Values are at joint outputs and use g = 9.80665 m/s². Input masses are assumptions; they are not mesh-derived, measured or material-calibrated.

The calculation excludes acceleration, friction, transmission efficiency, cable forces, off-axis loading and compliance. It does not specify motor torque ratings or payload capacity. The scene does not solve collisions, finite-element stress, fatigue, layer adhesion, creep, bearing retention, drive couplings or printer-specific tolerances. These need actual motor data, filament and process data, load cases and physical testing.

The reference image supplies styling, not verified kinematics or dimensions. Generic motor body dimensions are 42 × 23 × 42 mm for the base stepper and 40 × 32 × 28, 32 × 26 × 24 and 24 × 20 × 20 mm for the servo representations, in scene X/Y/Z order. They exclude protruding ears, horns, connectors and shafts and do not identify compatible commercial motors. Servo internals and complete joint transmissions are not modeled. Motor mounts and output couplings require actual hardware data.

Five braided service loops update with joint poses. Their endpoints stay attached to their respective assemblies. Curves are visual routes, not a simulation of fixed cable length, minimum bend radius, slack, fatigue, stiffness or collisions. These must be engineered before fabrication.

This page does not replace the earlier Blender file or STL set, and does not claim those files match this P03 model. Visual detail does not imply NASA certification, production qualification, printable watertight CAD solids, or demonstrated load capacity.

## Sources

- [SKF 608 manufacturer datasheet](https://docs.rs-online.com/9931/A700000008717780.pdf): bearing envelope.
- [Accu M3 DIN 934 nut](https://www.accu.co.uk/hexagon-nuts/766485-NUT930M3C): across-flats size and thickness.
- All shell dimensions, clearances and mass assumptions are provisional design choices in `spec.js`.

## Files and validation

`spec.js` contains the nominal dimensions, joint ranges, forward kinematics and static torque calculation. `model.js` builds the meshes and inspection states. `studio.js` provides interaction, labels, camera controls and exports. `studio.css` and `index.html` implement the responsive page.

`check.cjs` runs browser checks using this machine's bundled Playwright and installed Edge. It checks the renderer, interior geometry, inspection controls, joint coordinates, roll and gripper independence, cable attachment errors, clamping, payload moment changes, dimension tables, motor and fastening close-ups, exports, camera views and responsive widths from 320 to 1440 px. Screenshots are in `qa/`. `mechanics-check.mjs` independently checks the gravity calculation.

The rendering add-ons are pinned to the same Three.js r180 version as the existing local core. `vendor-rendering.cjs` fetches them from the official Three.js repository; `../vendor/THREE-LICENSE.txt` contains their MIT license. Runtime rendering does not contact a CDN.


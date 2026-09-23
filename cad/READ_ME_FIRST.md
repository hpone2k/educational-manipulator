# EDU-05 — Blender arm concept

This is an editable concept with separate structural meshes. The motor types and dimensions, payload, reach, printer, bearings, fasteners and transmissions have not been specified. The supplied STLs are **prototype geometry for inspection and fit trials**, not a validated functional robot kit.

## Open the model

Open `EDU05_robot_arm_concept.blend` in Blender. The scene selector offers:

- **EDU-05 | Assembled** — the posed arm, reference motors and labeled joints.
- **EDU-05 | Parts layout** — all 13 unique prototype parts, with names, quantities and bounding dimensions.

In the Outliner, expand **03 | Joint controls — rotate these empties**. Select a JOINT object and rotate around the local axis in its name. J1 uses local Z, J2/J3/J4 use local Y, and J5 uses local X. The downstream parts follow the joint. The initial pitch angles use the negative local Y direction. The joint labels are presentation annotations for the saved pose; their leader lines do not track subsequent edits.

The embedded text blocks include the generator, parameters and a short introduction. The scene uses millimetres: one Blender coordinate unit equals one millimetre. The native file preserves the separate parts and the parent hierarchy.

## What is included

| ID | Structural part | Assembly quantity |
|---|---|---:|
| P01 | Base plate | 1 |
| P02 | Motor housing | 1 |
| P03 | Rotating deck | 1 |
| P04 | Shoulder bracket | 2 |
| P05 | Upper link side plate | 2 |
| P06 | Forearm side plate | 2 |
| P07 | Upper link spacer | 2 |
| P08 | Forearm spacer | 2 |
| P09 | Wrist side plate | 2 |
| P10 | Roll carrier | 1 |
| P11 | Gripper palm | 1 |
| P12 | Gripper finger | 2 |
| P13 | Clearance coupon | 1 optional test piece |

Motors, shafts, bearings and guide rods are in the **reference hardware** collection. They are excluded from STL export and are not a purchasing specification. The base coupling, joint drive interfaces, gripper actuation and hardware retention still need detailed design. The model is not collision-checked or load-tested.

## Prototype STL files

Each file in `prototype_stl/` contains one part, centered in X/Y and resting at Z = 0. STL has no unit metadata; import these at **millimetres, 100% scale**. The base diameter should measure 180 mm. The upper link has 180 mm between pivots and is 226 mm overall, so it will not fit flat on a 220 mm bed without reorientation or a design change.

The automated mesh checks require one connected shell, no non-manifold edges and positive enclosed volume for each exported part. These checks establish closed geometry, not hardware compatibility, mechanical strength, dimensional accuracy of the printer, or support-free printability.

Start with **P13_clearance_coupon.stl** after checking its dimensions in your slicer. The holes from left to right in the parts layout are 3.4, 4.4, 8.4 and 6.6 mm. Decide filament, wall counts, infill, print orientation and supports after the expected joint loads and printer are known; no final structural print settings have been assumed.

## Edit and regenerate

Edit `parameters.json` and regenerate using a separate Blender process:

```text
blender --background --python build_robot.py
```

Run this from this directory or use absolute paths. The script writes its output next to itself. It creates new scenes without deleting existing scenes, but overwrites this concept's output files when rerun. Retain a copy before keeping manual edits to the generated model. Some mounting geometry remains explicit in `build_robot.py` and is intentionally provisional.

## Next measurements

To turn this into an assembly-ready design, provide the model and dimensions of every motor, mounting hole spacing, output shaft or servo horn geometry, intended bearings, reach, payload, and printer build volume. Then revise the transmission, joint stack dimensions, fastener lengths, mechanical stops and clearances, and test a single joint before printing the complete arm.

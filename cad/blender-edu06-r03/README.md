# EDU06 R03 — printed six-axis manipulator

Open **`EDU06_R03.blend`** in Blender. It contains the assembled arm, seven dimensioned actuator references, individually named printed parts, an open service base and a geared gripper. J1 and the wrist use AX-12A motors; J2/J3 use XM430-W350-T motors. The gripper has its own AX-12A actuator.

This is an editable engineering prototype. Geometric checks, movement demonstrations and calculated loads are documented separately; the arm has no certified payload or completed physical load test.

## Move and inspect the model

1. Select **`CONTROL • angles in degrees — edit custom properties`** in the Outliner.
2. Open **Object Properties → Custom Properties**. Change `J1` through `J6` for the six joint output angles; `GRIP` controls the geared jaw opening angle. Values are degrees.
3. Press **Space** over the Timeline to play the **360-frame / 12-second** demonstration. Stop playback before editing a pose. Existing animation keys restore their recorded values when you change frames; insert your own property keyframes if you want to keep an edited animation.

Gear drivers impose actual modeled reductions of **3:1 at J1, 4:1 at J2 and 3:1 at J3**. The gripper's two gears rotate oppositely. This is a kinematic rig: animation does not simulate motor heating, printed-bearing friction or structural failure. Use the documented angle ranges, then review the motion-check results before extending them.

Orbit with the middle mouse button, pan with Shift + middle mouse, and zoom with the wheel. Press **Numpad 0** to leave the saved camera view. Select a part and use **Numpad .** to frame it. Switch to **Solid** viewport shading, then **Alt + Z** toggles X-ray for internal inspection; the Outliner eye icons let you hide the lid, frame or other components without deleting them.

## Identify the parts

| Collection | Contents |
|---|---|
| `01 PRINTED PARTS` | Individual manufacturing meshes: structure, gears, plain bearings, shafts, cradles, caps and spacers |
| `02 PURCHASED` | Motor envelopes/horns, nuts, screws and electronics; exclude these from printing |
| `03 JOINT CONTROLS` | Joint datums, drivers and the main control object |
| `04 CABLE ROUTING` | Visual cable paths; real cable access and service loops need fitting |
| `05 STUDIO` | Presentation elements; exclude from printing |

Green and ivory materials distinguish the printed components. Black motor bodies and electronic modules are reference hardware. The fabricated design adds no metal bearing, shaft, guide rod or structural bracket; the motors retain their supplied internal hardware and horns.

## Print the fit samples first

The scene uses **millimetres**. STL files in `prototype_stl/` also use millimetres; import them into Bambu Studio at **100% scale**. Do not print a single export of the assembled arm.

Start with `F01_hole_and_nut_coupon.stl`, `F02_AX_16PCD_horn_coupon.stl` and `F02_XM_16PCD_horn_coupon.stl`. Then try one motor cradle/cap/shim set and one printed journal/bushing pair. Check actual motors, screws and nuts with calipers before committing to the full set. Thin spacers and 0.30 mm shims need suitable layer settings and a measured result.

The STL audit compares part bounds against the Bambu A1's **256 × 256 × 256 mm** build volume. Check the final sliced orientation, supports, brim and plate exclusions in Bambu Studio. Closed meshes and build-volume fit do not establish layer strength or support-free printability.

## Read the verification and assembly records

- **`engineering-review.md`** — completed checks, design decisions and remaining physical validation.
- **`motor-and-fastener-guide.md`** — exact motor datums, horn screws, rear-inserted cradle bolts, spacers and assembly sequence.
- **`structural-fasteners.md`** — remaining structural screw/nut sets and matching holes, including the elbow bearing ties.
- **`motor-interface-schedule.json`** — the generated interface and fastener stack for each actuator.
- **`stl-audit.json`** — independent checks of the exported STL files.
- **`mass-load-audit.json`** — mass and joint-moment calculations with their assumptions.
- **`demo-trajectory-audit.json`** — sampled clearances along the saved animation, when supplied.

The scene selector also contains **Individual print parts**, a layout of the separate exported meshes. It is an inspection layout, not a prepared multi-plate slicing job. The PNG previews and motion GIF are rendered from the editable Blender geometry.

Keep the open-base service access and printed 8 mm feet when assembling the base. Establish secure mounting, free movement and cable clearance before staged powered testing. Review the calculated loads and the remaining checks before assigning a payload.

## Edit and regenerate

Save a separate copy before manual editing. The source generator is `build_edu06.py`, with reusable geometry in `blender_lib.py`, motor interfaces in `motor_models.py` and gear mathematics in `gear_math.py`. Run the generator in a separate background Blender process to avoid disturbing an unsaved scene:

```text
blender --background --python build_edu06.py
```

Regeneration overwrites the generated R03 model and outputs. Re-run the mesh, motion and load checks after dimensional or kinematic changes; previous results do not validate a modified design.

# Educational Manipulator — Blender & Web Studio

The latest mechanical prototype is **EDU06 R06**, with four AX-12A motors, two XM430-W350-T motors, five arm axes and a powered gripper. It includes paired joint supports, centred links, an enlarged electronics base and a modelled daisy-chain harness.

- [Blender assembly](cad/blender-edu06-r06/EDU06_R06.blend)
- [Complete R06 package: model, 186 STL files, previews and reports](cad/blender-edu06-r06/EDU06_R06_Blender_and_Print_Prototype.zip)
- [Assembly, dimensions and printing guide](cad/blender-edu06-r06/README.md)
- [Mechanical verification and limitations](cad/blender-edu06-r06/engineering-review.md)
- [Wiring and connector notes](cad/blender-edu06-r06/wiring-notes.md)

R06 has sampled digital geometry, motion and cable checks. Physical print fits, cable retention and load capacity still require validation. Earlier CAD revisions are retained in `cad/`; temporary generation files and local runtime caches are excluded from Git.

## Orbit web concept

The web application below is an earlier interactive concept. Its illustrative dimensions are separate from the R06 manufacturing prototype.

A local web application for exploring a five-joint educational robot arm. The interface includes a detailed 3D model, selectable joint labels, joint angle controls, a parallel gripper, preset poses, a 12-second motion demonstration, camera views and live tool coordinates.

## Run

With Node.js installed, open a terminal in this folder and run:

```sh
npm start
```

Open http://127.0.0.1:4173 in a browser with WebGL 2 support. Keep the terminal running. No package installation or external service is needed; Three.js 0.180.0 and OrbitControls are included in `vendor/`, with their MIT license. Use the local server rather than opening `index.html` directly because the page uses JavaScript modules.

## Controls

- Drag to orbit; scroll or pinch to zoom; right-drag to pan.
- Select a label, a joint on the model, or its name in the control panel.
- Move sliders or enter angles. Keyboard arrows work on the inputs.
- Use Front, Side, Top, 3D and Fit for camera positioning.
- Toggle joint labels or rotation axes.
- Try Home, Reach and Fold, or play the demonstration. Stop or Escape pauses motion at its current position; a manual adjustment also stops it.

## Model conventions

Five arm DOFs: base yaw, shoulder pitch, elbow pitch, wrist pitch and wrist roll. Gripper opening is a separate actuator. All dimensions are illustrative millimetres.

| Dimension | Value |
|---|---:|
| Shoulder height above world origin | 90 mm |
| Upper arm | 180 mm |
| Forearm | 150 mm |
| Wrist pitch to roll axis | 52 mm |
| Roll axis to tool centre | 73 mm |
| Gripper clear opening | 0–60 mm |

The displayed world frame is right-handed with Z upward. In Three.js coordinates, world X = scene X, world Y = −scene Z, world Z = scene Y. Shoulder zero is horizontal along the base's +X direction. Elbow and wrist angles are relative to their parent links. Tool position is the centre between the fingertips and is independent of wrist roll and gripper opening.

This is a kinematic concept model. It does not simulate mass, torque, collisions, gravity, motor limits or real hardware. Some manually selected poses may intersect the arm or floor. Real dimensions, joint limits and motor calibration can be added once the hardware is defined.

## Files

- `index.html`: accessible page structure.
- `styles.css`: responsive interface.
- `app.js`: Three.js geometry, joint hierarchy, labels, interaction and animation.
- `server.cjs`: local HTTP server, bound to 127.0.0.1.
- `vendor/`: pinned renderer dependencies and license.
- `check-browser.cjs`: browser checks; uses this workspace's bundled Playwright runtime and installed Microsoft Edge.
- `qa/`: screenshots used for visual inspection.

The browser checks verify forward kinematics against an independent calculation, joint and gripper controls, input clamping, camera views, demonstrations, and layouts from 320 to 1440 pixels. Reference: [Three.js documentation](https://threejs.org/docs/).

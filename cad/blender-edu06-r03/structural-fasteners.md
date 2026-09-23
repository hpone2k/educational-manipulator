# R03 structural fasteners — source review

Reviewed against `build_edu06.py` after the side-loaded lid/deck nuts, elbow cheek ties and U2D2 tray translation to **(−61,−64)** were added. This schedule excludes motor-cradle bolts and M2 horn screws; those are in `motor-and-fastener-guide.md`. It records the modeled mounting geometry, not a tightening-torque or strength qualification.

Unless stated otherwise, M3 clearance holes are **Ø3.4 mm**, M4 clearance holes **Ø4.5 mm**, M3 nuts **5.5 AF × 2.4 mm**, and M4 nuts **7 AF × 3.2 mm**. Circular patterns below state their **diameter**, although the generator's `pcd()` argument is a radius. Coordinates are in the named assembly's local frame.

## Modeled fastening sets

| Mount | Screw and nut quantity | Pattern and actual stack |
|---|---|---|
| B02 lid → B01 posts | 5 × M3×12; 5 M3 nuts | XY (±110,±85), plus (0,85). Head Z95; tip83. Side-loaded pockets Z85.2–88.0 have 2 mm roofs; nuts Z85.4–87.8. |
| B03 service panel → four B01 tabs | 4 × M3×16; 4 M3 nuts | Installed panel at Y−93.5, Z+5; X±103, assembled Z10/73. Head Y−95, shaft +Y, tip−79. Nuts occupy Y−84.6 to−82.2 inside rear-open tab pockets. Panel is displayed removed, with its screws following it. |
| B05 lower journal stand → floor | 4 × M3×55; 4 M3 nuts | Stand-centred 52×48 rectangular pattern, global centre (−28,0). Head Z51; tip−4. Nuts Z−2.4–0 beneath the floor; 8 mm feet provide clearance. |
| B07 upper sleeve/thrust ring → lid | 4 × M3×12; 4 M3 nuts | Ø72 pattern at 45°, centre (−28,0). Head Z98; tip86. Nuts Z87.6–90 under the lid. |
| B17 split yaw retaining collar | 1 × M3×10; 1 M3 nut | Transverse Y bolt at X23/Z37.7. Head Y−4.5, tip+5.5; nut Y1.7–4.1. The clamp retains the shaft without clamping the stationary sleeve axially. |
| B09 yaw gear → B08 shaft coupling | 4 × M3×20; 4 M3 nuts | Ø50 at 45°. Includes four 0.5 mm B18 spacers. Head Z82; tip62; nuts Z62.6–65 below the gear. |
| B10 rotating deck → B08 flange | 4 × M3×12; 4 M3 nuts | Ø58 at 45°. Four 0.8 mm B19 spacers place heads at Z118.8; tips Z106.8. Radial nut slots Z106.8–109.6 leave 2.4 mm roofs; nuts Z107.0–109.4. Tips remain above the collar ending at Z106. |
| Shoulder pedestal → rotating deck | 4 × M3×25; 4 M3 nuts | X−76/+44, Y±20: **120×40** pattern. Head Z132; tip107. Nuts Z109.6–112 beneath the rotating deck. |
| B15 printed feet → floor | 4 × M4×16; 4 M4 nuts | X±108/Y±73, Ø4.5 holes. Four 3.1 mm B16 spacers place heads at Z8.1; tips−7.9. Nuts Z−7.8 to−4.6 in bottom-open 7.3 AF pockets. These screws attach the feet, not the bench. |
| B14 U2D2 tray → floor | 4 × M3×12; 4 M3 nuts | Tray centre (−61,−64); offsets (±27,±11), giving global X−88/−34 and Y−75/−53. Head Z8; tip−4. Nuts Z−2.4–0. Ø6.2 counterbores clear heads above the 3 mm tray floor. Matching floor holes are present. |
| Shoulder and elbow rotating shaft retainers | 2 × M4×60; 2 M4 nuts | One axial bolt per reducer, inserted +Z from under-head Z−29.4 through a 1.1 mm printed spacer. Tip Z30.6; front M4 nuts Z27.3–30.5. Ø4.5 cap/flange bores; the central shaft bore is Ø8. |
| Shoulder pinion support bridge → rear cheek | 2 × M3×80; 2 M3 nuts | Reducer-frame X−92.5, Y−25/+15. Head Z55.1; bridge top51.5 and 3.6 mm printed head spacers. Tip−24.9; rear nut pockets −25 to−22.2; nuts −24.8 to−22.4. |
| Elbow pinion support bridge → rear cheek | 2 × M3×75; 2 M3 nuts | Reducer-frame X−50, Y±30. Head Z50.1; bridge top49.5 and 0.6 mm printed spacers. Tip−24.9; same rear nut-pocket and nut-Z stack as shoulder. |
| Shoulder stationary cheeks → pedestal | 2 × M3×65; 2 M3 nuts | X±25/Y−58.5; head Z31, tip−34. Nuts Z−33.4 to−31. The bolt crosses both cheek seating slots and the pedestal. |
| Upper and forearm link roots → reducer wheels/output flanges | 8 × M3×25; 8 M3 nuts | Four per link, Ø36 at 45°. Both use head Z50.6, tip25.6 and output-flange nuts Z25.7–28.1. Head spacers are 1.1 mm at shoulder and 3.1 mm at elbow. |
| Elbow assembly and front cheek → upper link | 4 × M3×70; 4 M3 nuts | Ø44 at 45°, centred at the upper-link distal pivot. Each includes an 8.1 mm head spacer, 6 mm mount standoff and **38 mm stationary between-cheek tie**. In the elbow frame, head Z−45.1, tip24.9; recessed front nuts Z22.4–24.8. This set ties both stationary cheeks; it does not clamp the rotating shaft. |
| W03/W05/W07 carriers → AX output adapters | 12 × M3×12; 12 M3 nuts | Four per carrier, Ø34 at 45°. Includes 1.5 mm printed head spacers. Head Z12.5; tip0.5; nuts Z0.6–3.0 under the raised adapter flange. Separate from M2 horn screws. |
| G04 gripper bridge → G01 palm | 2 × M3×70; 2 M3 nuts | Palm-frame X−18/Y±30. Each stack includes a 57.95 mm column and 2.15 mm head spacer. Head Z19.15; tip−50.85; nuts Z−50.75 to−48.35 in rear-open palm pockets. |
| Gripper idler retaining cap/compression sleeve → palm | 1 × M3×75; 1 M3 nut | At X0/Y15. Head Z23.95; tip−51.05; nut Z−50.75 to−48.35. Stack includes 3.95 mm head spacer, 2 mm cap and 62.95 mm stationary sleeve; the sleeve carries bolt preload so the jaw can rotate. |
| B12 yaw pinion journal support → lid | 2 × M3×20; 2 M3 nuts | X32/Y±15. The 16 mm combined support/lid stack plus 1.5 mm printed head spacers gives head Z96.5 and tip76.5. Nuts Z76.6–79 seat below the support ears. |

The J4 bulkhead is now fused into the forearm mesh, so it needs no separate attachment set. J5/J6 cradle-to-yoke and gripper-palm-to-tool-carrier connections are included in the motor-cradle through-bolts; do not count them again.

W03's raised upright is 85 mm high. In the J4 frame its mounting wall spans X−54 to−50, Y−48 to22 and Z8 to93. With the J5 datum at `(−5.05,0,65)` and a +90° rotation about Y, the AX rear-cap face maps exactly onto X−50, and its four post axes map to Y−42.5/+15.5 and Z44/86. The Ø3.4 wall holes share those axes. The ventilation cut's bounding box spans Y−36 to10 and Z20.5 to79.5; it leaves at least 3.8 mm of planar material between the bore edge and the window. This is a dimensional-alignment check, not a flexural-strength result.

## Structural-only purchase subtotal

| Screw | Quantity |
|---|---:|
| M3×10 | 1 |
| M3×12 | 29 |
| M3×16 | 4 |
| M3×20 | 6 |
| M3×25 | 12 |
| M3×55 | 4 |
| M3×65 | 2 |
| M3×70 | 6 |
| M3×75 | 3 |
| M3×80 | 2 |
| M4×16 | 4 |
| M4×60 | 2 |
| M3 nuts | 69 |
| M4 nuts | 6 |

All listed washers/spacers are printed. These are nominal generator lengths: confirm purchased under-head lengths, head profiles and assembled printed stacks. `fasteners.json` contains only calls recorded through `screw_pattern`; direct `bolt()` and `nut()` calls are also included in this source-derived table, so that JSON alone is not the complete purchasing list.

## Review disposition

- **Corrected:** top-open lid/deck nut traps now have load-bearing roofs and side entries; the elbow front cheek now has four stationary ties and continuous mounting bolts; lower stand, yaw pinion support, service panel and electronics tray have explicit bolts/nuts and mating holes.
- **Corrected:** moving the tray centre to (−61,−64) separates its closest nut (−88,−75) from the foot centre (−108,−73) by 20.10 mm, exceeding the 12 mm foot radius plus the approximately 3.18 mm M3 nut corner radius.
- **Still to provide for physical use:** the feet do not anchor the robot to a bench. Choose and verify the external bench attachment before load testing; the four M4×16 foot bolts are not an anchoring specification. The U2D2 tray provides a lateral locating pocket but has no modeled top strap or positive vertical retainer.
- **Documentation consistency:** README ratios are J1=3:1, J2=4:1, J3=3:1. The motor guide's rear-inserted screw stacks match current attachment depths: base20.05, shoulder/elbow15.35, J4=6, J5/J6=4 and gripper12 mm. Neither document claims a certified payload or physical proof of operation.

This review establishes source-level mating intent and explicit fasteners. Confirm the rebuilt meshes, interference checks, nut insertion access and actual printed fits before relying on the connections.

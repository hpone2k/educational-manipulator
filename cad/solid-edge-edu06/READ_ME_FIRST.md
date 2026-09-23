# EDU06 R01 — native Solid Edge development model

Created 23 September 2026 for a Bambu A1, assuming standard PLA and a 0.4 mm nozzle.

**This is real solid CAD, but the full arm is not ready for fabrication or powered assembly.** The fit coupons are the intended first prints. The assembly is a static packaging layout; it has no solved joint mates, motion limits or completed interference clearance. Do not interpret an STL export as design approval.

## Open these files

- `EDU06_R01_LAYOUT_PROTOTYPE.asm`: native assembly. Keep the `parts` folder beside it.
- `parts/*.par`: editable ordered Solid Edge parts, made from exact numeric sketch coordinates and extrusion depths.
- `step/*.stp`: neutral solid exports.
- `PRINT_FIRST_fit_coupons_mm.zip`: the four initial fit-test STLs.
- `design.json` and `define_design.py`: millimetre source dimensions and placement definitions.
- `PARTS.csv`: individual part status and unresolved details.
- `cad-verification.json`: solid bounding boxes and volumes reported by Solid Edge.
- `mesh-verification.json`: STL bounds, closed-edge checks, orientation and volume comparisons.

## Print first

1. C01 clearance and M3 nut coupon: **82 × 36 × 4.2 mm**. Flat face on bed, no scaling. Small-hole row, left to right: Ø2.2, 2.3, 2.4, 2.7, 2.8, 2.9, 3.3, 3.4 mm. Nut-pocket row: 5.6, 5.7, 5.8, 5.9 mm across flats; 2.7 mm deep. There is deliberately no embossed text that could distort the test surfaces; keep this map beside the print.
2. P01 AX horn adapter: Ø34 × 4 mm; four Ø2.3 holes on **16 mm PCD**, Ø8 centre access, four Ø3.4 interface holes on 26 mm PCD at 45° indexing.
3. P02 XM horn adapter: Ø34 × 4 mm; eight Ø2.3 holes on **16 mm PCD**, same centre and outer interface.
4. P03 XM side coupon: **24 × 38 × 4 mm**; four Ø2.8 holes on a **12 × 24 mm** rectangle. This checks the local pattern only; its centre is not the motor output axis.

Start with your normal PLA profile, 0.20 mm layers, five walls and solid coupons. Use the hole/nut fit results to change diameters and pocket sizes, never the manufacturer's hole-centre spacing. Select screws by the measured bracket/washer stack. The inspected AX horn drawing gives 4 mm maximum threaded depth; XM horn gives 2 mm and XM side mounting 3 mm. Verify your actual horn revision and leave bottoming clearance. Do not drive long screws into the motor.

## Defined development dimensions

| Feature | CAD input |
|---|---|
| Upper pivot spacing | 120 mm |
| Forearm pivot spacing | 100 mm |
| Link cheeks | 4 mm; 38 mm overall width |
| Base plate | 200 × 180 × 5 mm |
| Base anchors | four Ø6.5 holes, 170 × 150 mm centres |
| Modular turntable plate | Ø160 / Ø60 × 6 mm; bearing interface unselected |
| AX body envelope | 32 × 50 × 40 mm |
| XM body envelope | 28.5 × 46.5 × 34 mm |
| Base reduction | module 2, 20/60 teeth, 80 mm shaft centres |
| Shoulder reduction | module 1.5, 20/80 teeth, 75 mm shaft centres |
| Elbow reduction | module 1.5, 20/40 teeth, 45 mm shaft centres |
| Gripper | module 1.5, 20-tooth pinion, two opposed racks |

Gear pressure angle is 20°. The involute flanks are sampled into line segments; the root transition is not a manufactured hob fillet. Tooth-thickness reduction is 0.16 mm per component at the pitch line, so a pair has approximately 0.32 mm nominal circular backlash before print errors. Gear faces are 8 mm for arm reductions and 6 mm for the gripper. Tooth strength, wear and root fatigue have not been calculated or tested.

Metal motors, bearings, shafts, bolts and nuts are reference/purchased components. `R01`, `R02`, `R03` must not be printed as replacements. Printed parts use clearance holes; an Ø8.2 hole alone is **not** a torque-transmitting shaft coupling.

## What still prevents full-arm printing

- Choose the actual turntable bearing: outer/inner sizes, axial height, bolt circle, screw pattern and moment rating. The 140 mm PCD in this model is our modular plate pattern, not a claim about a purchased bearing.
- Select and detail shaft bearings, axial retention, shaft-to-gear hubs and supported pinion couplings. The 608 envelope is a trial reference, not a verified bearing design.
- Complete the link flange fasteners, closure-panel attachments, motor supports and double-shear load paths. Some development panels are supplied separately rather than installed in the assembly.
- Complete J4/J5/J6 wrist brackets, cable routing and joint collision checks. The current full-size motor packaging is longer than the earlier 150 mm wrist assumption; **the previous payload estimate no longer applies**.
- Complete gripper rack-to-finger fasteners and captive guide covers. The supplied finger is a dimensional blank awaiting those matching details; it is not yet installed in the layout.
- Add root fillets and revise sharp load-bearing transitions after the load path is frozen. Check print orientation and stress perpendicular to layers.
- Replace earlier mass allocations with sliced masses and measured hardware; then recalculate gravity, acceleration, gearbox losses, bearing forces and PLA creep/temperature limits.

There is no rated payload for R01. Do not power this layout or use the earlier 50 g commissioning suggestion until these mechanical release items are resolved. This limit is tied to identified unfinished interfaces, not to STL mesh quality.

## Export and validation

Solid Edge's installed STL translator defaulted to inches with coarse tessellation. The deliverable meshes are instead generated from its solid-body facet API at **0.02 mm chord tolerance**, with coordinates converted from CAD metres to **millimetres**. Existing global translator settings were not changed. Verify C01 reads 82 × 36 × 4.2 mm in Bambu Studio.

Native solids and mesh manifold checks can verify geometry and scale; they cannot establish mechanical strength, correct motor clearance or assembly fit. STEP and STL exports are not a replacement for the native assembly and its outstanding design notes.

Manufacturer references: [AX drawing](https://emanual.robotis.com/assets/images/dxl/ax/ax-12a_dimension.png), [XM ROBOTIS datasheet](https://media.distrelec.com/Web/Downloads/_t/ds/Dynamixel_XM-Series_eng_tds.pdf). CAD method: [Siemens body faceting API](https://support.industrysoftware.automation.siemens.com/trainings/se/107/api/SolidEdgeGeometry~Body~GetFacetData.html).

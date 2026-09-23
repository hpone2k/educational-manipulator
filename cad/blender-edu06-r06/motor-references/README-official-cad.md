# ROBOTIS manufacturer CAD used by EDU06 R04

Retrieved 23 September 2026 from the official [ROBOTIS download index](https://en.robotis.com/service/downloadpage.php?ca_id=70). The ROBOTIS download landing pages themselves link to the downloaded Dropbox files; they are not community reconstructions. Original bytes and SHA256 hashes are recorded in `official-downloads.json`.

| Motor | Official STEP | Official dimension drawing |
|---|---|---|
| AX-12A / shared AX enclosure | [download 99](https://en.robotis.com/service/download.php?no=99) | [download 98](https://en.robotis.com/service/download.php?no=98) |
| XM430/XH430 with N101/I101 | [download 158](https://en.robotis.com/service/download.php?no=158) | [download 157](https://en.robotis.com/service/download.php?no=157) |

The original files are `AX-12A.stp` and `XM_H-430_idler.stp`; the matching PDFs and rendered drawings are included. STEP headers date the AX assembly to 2015-09-16 and XM assembly to 2026-07-10. The PDF drawings are dated 2011-01-24 and 2019-03-19 respectively. Both drawings say **FOR REFERENCE ONLY**. These are detailed exterior/interface assembly models, not complete internal geartrain and electronics models.

## Conversion and integration

`convert_official_cad.py` uses [cascadio / OpenCASCADE](https://github.com/trimesh/cascadio), installed only in this folder, to tessellate at **0.01 mm absolute chord deflection** and **0.15 rad angular deflection**. It preserves the STEP component placement and writes Blender-importable `*-official.glb`. The GLB includes analytical BREP primitive metadata in `*-gltf-metadata.json`.

`normalize_motor_meshes.py` applies the assembly transforms, converts metres to millimetres, and places the horn mounting face at Z=0. It produces `AX-official-mm.json.gz` and `XM-official-mm.json.gz`, usable by Blender with standard-library gzip/json. Coordinates are **X across case width, +Y toward the case top, +Z outward along the output shaft**. No exterior remeshing, scaling to an estimated envelope, or invented mounting holes is applied.

`motor_models.py` imports this geometry. AX horn and purchased rotor hardware animate with the output. The AX centre retaining screw and dummy output shaft overlap the manufacturer's simplified internal case volume because an internal gearbox cavity is not provided; those two visible, rotating purchased references are excluded from internal motor collision inference. The main case and actual stock horn remain collision meshes.

The XM STEP fuses the exterior horn into its case dummy. R04 partitions it at the actual front-case plane Z=-2 and adds matching internal planar caps. This internal partition is added for animation/closed-mesh containment tests; it does not move the outer surfaces or mounting holes. Source component boundaries are welded individually at 0.000001 mm; distinct touching hardware components are never welded together.

## Dimensions in the normalized frame

| Datum | AX-12A | XM430/XH430 vendor model |
|---|---:|---:|
| Published case width × height | 32 × 50 mm | 28.5 × 46.5 mm |
| Top Y / bottom Y | +11.5 / -38.5 mm | +11.25 / -35.25 mm |
| Broad front/rear case planes Z | -5 / -37 mm | -2 / -36 mm |
| Rearmost localized projection Z | -40 mm | -38 mm (rear idler) |
| Horn outside diameter | 22 mm | 19.5 mm |
| Horn mounting holes | 4 × M2, Ø16 PCD | 8 × M2×0.4, Ø16 PCD |
| Drawing maximum horn thread depth | 4 mm | 2 mm |
| Frontmost retaining feature | +0.04545 mm | +4.7 mm |

**Revision discrepancy:** the 2019 XM drawing labels 2.2 mm front horn protrusion while the current supplied STEP has a 2.0 mm horn mounting face offset. R04 uses the current STEP and records this difference. Confirm the user's actual supplied horn revision physically before committing to full printing. The 34 mm published XM case depth excludes horn/idler/central retention features; the downloaded complete reference spans approximately 42.7 mm in Z.

The AX pinion/adapter needs a **Ø6 mm × 0.30 mm minimum shallow centre relief** for its existing retaining screw. XM needs clearance for a **Ø8 mm boss to Z=+2.2**, then the **Ø4.5 centre feature to Z=+4.7**; design reliefs are Ø8.5 through depth2.5 and Ø5.0 through depth5.0. These allowances are separate from the M2 attachment holes.

## Actual mounting coordinates

Dimensions below come from the official drawing and analytical cylindrical faces in the official STEP. They are reference datums, not a recommendation to print the motor itself.

- **AX body front/back flange holes:** X=±13.5; Y=-6.5,-14.5,-22.5,-30.5 mm; additional bottom holes X=±8,Y=-36 mm. Front/back broad flange surfaces Z=-5/-37. The STEP shows Ø2.2 clearance bores. These use the manufacturer's M2 nut/screw arrangement; do not substitute a threaded M3 assumption.
- **AX horn:** (X,Y)=(8,0),(0,8),(-8,0),(0,-8), face Z=0. Central retaining screw remains installed.
- **XM side mountings:** X=±14.25 (side faces); Y=-4,-28; Z=-13,-25 mm (four holes on each side). These are M2.5×0.45, **3 mm maximum thread depth**.
- **XM top mountings:** Y=11.25; X=±8; Z=-13 mm. M2.5, maximum3 mm engagement.
- **XM bottom mountings:** Y=-35.25; X=±8; Z=-13,-25 mm. M2.5, maximum3 mm engagement.
- **XM front auxiliary mountings:** X=±11,Y=-8,Z=-2 mm. M2.5, maximum3 mm engagement.
- **XM front/rear 22×40 mm corner pattern:** X=±11,Y=8,-32 contains the manufacturer's case-retaining screws. Do not remove or repurpose these as ordinary body-mount holes.
- **XM horn/idler holes:** radius8 mm at 45° increments. Horn face Z=0; idler face Z=-38. The visible tapped minor diameter in the STEP is not a print clearance-hole diameter.

## Printed cradle changes

R04 retains R03 mounting-post XY and rear attachment planes: **AX cap back Z=-44.95; XM cap back Z=-41.15**. AX has a 0.30 mm front seating shim and 3.30 mm rear seating spacer, because its broad rear seating surface is at -37 while its local rear projections reach -40. XM has 0.30/0.50 mm seating spacers; a Ø21 rear aperture preserves the stock idler. The nominal residual axial gap is 0.10 mm, subject to actual filament/shrinkage/case revision fit measurement.

AX's front access opening is Ø34, clearing its actual raised/curved front casing and case-screw heads. XM retains a Ø26 opening. Motor body holes are faithfully visible but the robot uses separately printed captured cradles rather than unverified alternative mounting screws.

The AX 0.30 mm front spacer is a **single U-shaped piece**, contacting the side/lower case flange. Two disconnected nonfunctional upper corner remnants from the wide opening are removed; retained vertices and motor clearance are unchanged. Its volume is64.3801 mm³ (about0.07983 g of solidPLA). This removes4.9263 mm³ /0.006109 g per AX compared with the three-shell intermediate mesh. `ax-shim-connectivity-test.json` records connectivity, topology, unchanged coordinates and fit checks.

The GRIP-only `front_fasteners=True` option is dimensioned for an AX with a6 mm rear palm: four M3×45 screws enter from the front, under-head Z=-5.65, head top=-2.65, tip=-50.65; front bezel ends at -2.05. The gripper module supplies rear-palm captive nuts. It has no front captive nuts or rear stack spacers.

## Verification

`test_vendor_motor_import.py` builds AX, XM and front-fastener AX examples in a separate Blender process. `motor-import-test.json` records all26 resulting printed/collision meshes as closed manifold, nondegenerate and positive-volume. Independent sampled containment checks found no motor/cradle/shim or case/horn penetration in those examples. The full arm has separate pose/animation/torque audits. CAD fit checks do not establish printed strength, wear life, thermal duty or actual payload capacity.

Published weights and performance remain in the [AX-12A manual](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/) and [XM430-W350 manual](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/): AX54.6 g; XM82 g. Stall torque is not continuous-duty torque. R04 counts bought-motor mass once per actuator, rather than deriving its mass from the vendor envelope dummy volume.

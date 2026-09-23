# R03 independent mechanical feasibility review

Date: 2026-09-23. This is an engineering planning study, not a load rating or a manufacturing release. The numerical mass and centre-of-mass assumptions below must be replaced with the generated model's measured volumes and actual printed-part weights.

**Revision note:** the first independent Blender audit found considerably more mass than the budgets in this document and excessive elbow demand. The builder is being revised to a **3:1 elbow reduction (20/60 teeth, module 1.25, 50 mm centres)** and lighter wrist parts. The 2:1 elbow figures below are retained as the original planning study, not as the final model specification. Use `gear-pairs.json` and the independently generated `mass-load-audit.json` for the actual delivered geometry and motor-demand screening. No provisional payload in this planning document overrides a failed as-modelled load audit.

## Architecture that preserves the reference image

The reference has a green open-front box, cream gears and joint discs, ribbed green links, black motors, visible cable loops, and two gear-driven pivoting fingers. These features can be retained. Its apparently coaxial shoulder/elbow motor layout cannot simultaneously provide an external reduction: a real reduction needs an offset motor shaft, a separate output shaft, and gears that actually mesh. The three wrist axes plus gripper require four physical AX-12A motors, not two decorative motors or scaled-down cases.

Use six revolute arm axes (J1 yaw, J2 shoulder pitch, J3 elbow pitch, J4 forearm roll, J5 wrist pitch, J6 tool roll) and a seventh motor for the fingers. Only printed components, motor assemblies, electronics, cables, screws and nuts are assumed available. No purchased bearings, steel axles, metal brackets, threaded inserts, springs, belts, or rubber pads are assumed.

Recommended starting lengths are 100 mm shoulder-to-elbow and 85 mm elbow-to-wrist-roll. The wrist/gripper remains about 170 mm long because real AX cases occupy space. The provisional horizontal shoulder-to-contact distance is 355 mm. Shortening the links alone will not eliminate the distal four-motor mass.

| Drive | Teeth | Module | Pitch centres | Face width | Large gear outside diameter |
|---|---:|---:|---:|---:|---:|
| J1 yaw, 3:1 | 20 / 60 | 1.5 mm | 60 mm | 10 mm | 93 mm |
| J2 shoulder, 4:1 | 20 / 80 | 1.25 mm | 62.5 mm | 12 mm | 102.5 mm |
| J3 elbow, 2:1 | 20 / 40 | 1.5 mm | 45 mm | 10 mm | 63 mm |
| Opposed gripper jaws, 1:1 | 20 / 20 | 1.5 mm | 30 mm | 7 mm | 33 mm |

These are external 20-degree involute gears. Nominal centres are m(z1+z2)/2; outside diameter is m(z+2). Tooth thickness needs an explicit tangential backlash allowance, initially 0.20-0.30 mm total at the mesh, then adjustment from printed coupons. Gear roots, face widths, and spoke openings need strength assessment; a mesh that animates is not proof against tooth failure. Print each gear flat with its rotation axis normal to the bed. Do not substitute sawtooth circles or simple sinusoidal teeth.

J1's AX is fixed inside an approximately 220 x 180 x 90 mm open-front box. Its pinion shaft and the output turntable shaft each need printed support journals independent of the servo horn. Allow straight screwdriver access, space to connect cables, and a removable top deck. Put U2D2 in a small fixed tray, away from the gears and swept wire loops. A U2D2 is an interface, not the motor power supply.

J2's XM stays on the yaw platform and drives an offset shoulder pivot. J3's XM is carried by the upper link and drives an offset elbow pivot. Their larger output gears and gear covers can be styled as the cream discs in the reference. Cover the gear teeth while providing removable access.

## Printed support strategy

- Base: printed hollow yaw spindle, nominal journal diameter 32 mm, two replaceable printed sleeves each 14 mm long, centres separated approximately 45 mm. A 16 mm cable bore is a starting envelope, subject to actual connector passage. Use a broad replaceable printed thrust ring, approximately 60 mm ID and 100 mm OD. Keep a separate retaining collar above the thrust surface.
- Shoulder: printed output journal diameter 24 mm, supported in both clevis cheeks by approximately 12 mm-long sleeves separated at least 40 mm. Elbow: 20 mm journal with two sleeves. Avoid cantilevering the complete arm from an AX/XM horn or one thin printed side plate.
- Motor pinions need a supported printed journal/coupler, with an axial clearance to the motor case. Motor horns transmit torque; they should not be the only path for the external arm's bending moment.
- Bushings are plain sliding interfaces. Printed plastic is not automatically low-friction. Baseline dry friction, wear and backlash are unknown; use slow intermittent demonstrations until measured. Use replaceable sleeves and thrust rings so worn parts can be reprinted.
- Start with 0.25 mm radial clearance (0.50 mm diametral) for printed sleeves and 0.3-0.5 mm axial clearance. These are coupon-test values, not universal printer tolerances. An interference-fit sleeve can distort its bore.
- Retaining screws/nuts must bottom against a shoulder or printed spacer, leaving the running clearance. Tightening a nut directly against two moving cheeks will lock the joint. Printed spacer creep can gradually loosen retention; access for inspection is necessary.
- Use closed or ribbed box links and generous fillets at the motor/yoke transitions. A useful first shell thickness is 2.4-3.2 mm; highly loaded cheeks and bolt bosses start around 5-6 mm, with ribs. These are geometry starting points, not validated strength dimensions. Excessive solid fill at the wrist worsens every upstream moment.

For scale, the 50 g case below gives a 1.233 Nm shoulder gravity moment. If a base pair of journal sleeves is separated by 45 mm, its moment reaction is approximately M/L = 27.4 N at each support, before dynamics. On a 32 x 14 mm projected journal area this is about 0.061 MPa mean bearing pressure. This low average does not establish PLA creep life, local contact pressure, layer strength, or friction.

## Fasteners and motor envelopes

Published motor envelopes are AX-12A 32 x 50 x 40 mm and XM430-W350 28.5 x 46.5 x 34 mm. Keep motors at these dimensions and put fit clearance in their mounts. Allow cable connectors, bend radii, horn thickness, central screw access, and the full swept volume of case corners. Do not infer mounting-hole positions from a photorealistic concept image.

Starting printed through-hole diameters: M2 2.3 mm, M2.5 2.8 mm, M3 3.4 mm. M3 nut pockets can start at 5.8 mm across flats and 2.7 mm depth for a nominal 5.5 mm x 2.4 mm nut. Print a fit coupon first. Captive pockets need an insertion opening and an anti-rotation wall. Keep adequate material around each pocket rather than letting a hex corner break through a rib.

The manufacturer horn patterns and maximum screw engagement must be checked against the exact motor/horn revision. M2 horn screws are not interchangeable with M2.5 case screws, and printed-clearance assumptions are not evidence of motor-thread depth. No long bolt may bottom in a motor hole. Through-bolted printed case cradles are possible, but must not clamp covers or block cooling/connector access. The precise purchased screw inventory is still unknown.

## Gravity moment calculation

Use g = 9.81 m/s^2. The table assumes the links and wrist are extended horizontally. x is the centre of mass measured from J2, J3 is at x=100 mm, and J5 is at x=230 mm. This is deliberately transparent: the masses below are budgets, not extracted from the proposed Blender model.

| Moving item | Mass budget | x from J2 | J2 moment | J3 moment |
|---|---:|---:|---:|---:|
| Upper-link printed shell | 40 g | 50 mm | 0.0196 Nm | 0 |
| J3 motor + elbow mount/reduction | 122 g | 100 mm | 0.1197 Nm | 0 |
| Forearm shell | 30 g | 142.5 mm | 0.0419 Nm | 0.0125 Nm |
| J4 AX + frame | 79.6 g | 190 mm | 0.1484 Nm | 0.0703 Nm |
| J5 AX + frame | 79.6 g | 230 mm | 0.1796 Nm | 0.1015 Nm |
| J6 AX + frame | 74.6 g | 270 mm | 0.1976 Nm | 0.1244 Nm |
| Gripper AX + jaws/gears/frame | 99.6 g | 315 mm | 0.3078 Nm | 0.2101 Nm |
| Moving cables + fasteners | 25 g | 180 mm | 0.0441 Nm | 0.0196 Nm |

For every distal item, tau_j = g * sum(m_i * horizontal_distance_i). Fixed shoulder-motor and base mass do not contribute to J2 torque but do affect base loading. The table approximates J3's mass at its pivot; actual motor-offset COM must be included in the final calculation.

| Assumed payload at x=355 mm | Total moving mass | J2 gravity | J3 gravity | J5 gravity |
|---|---:|---:|---:|---:|
| 25 g | 575.4 g | 1.146 Nm | 0.601 Nm | 0.143 Nm |
| 50 g | 600.4 g | 1.233 Nm | 0.663 Nm | 0.174 Nm |

The four distal AX motors alone weigh 218.4 g. Three wrist motors plus the gripper must not be omitted from the load calculation. A visually slim wrist cannot be obtained by shrinking those case meshes.

For preliminary sensitivity only, assume combined gear/journal efficiency eta=0.65 and an allowance factor of 1.5 on the gravity torque. Motor estimate is tau_motor = 1.5*tau_joint/(ratio*eta). The factor is not a measured dynamic simulation or an established safety factor for printed material.

| Payload | J2 motor, 4:1 | J3 motor, 2:1 | J5 direct, factor 1.5 |
|---|---:|---:|---:|
| 25 g | 0.661 Nm | 0.693 Nm | 0.214 Nm |
| 50 g | 0.711 Nm | 0.766 Nm | 0.260 Nm |

At 12 V, published stall torques are 1.5 Nm for AX and 4.1 Nm for XM430-W350. AX documentation recommends loads at or below one fifth stall for stable motion. ROBOTIS lists 0.82 Nm as an estimated continuous torque for XM, explicitly derived as 20% of stall. Thus 0.30/0.82 Nm are planning comparisons, not guarantees for this printed assembly. Direct J2 drive exceeds the XM planning comparison even before the allowance; do not claim it can hold the horizontal model continuously. At eta=0.50, the same 50 g case and factor give 0.925 Nm at J2 and 0.995 Nm at J3: both exceed 0.82 Nm. This illustrates why actual friction and temperature measurements are essential.

J4/J6 roll torques depend on transverse COM, not the total forward reach. Keep all downstream components centred on the roll axis. For example, a 303.4 g distal group displaced 35 mm transversely would produce approximately 0.104 Nm at J4 before friction and acceleration. Derive this from the final model, not from a presumed perfect balance.

The gear-jaw gripper has mirrored pivots, not a parallel-jaw trajectory. If both 65 mm moment arms share motor torque equally, lifting 50 g by friction alone with a hypothetical friction coefficient 0.25 requires about 0.128 Nm before transmission losses. Actual hard PLA contact friction is unknown. Use small cupped fingers for geometric retention and test light objects; do not label an arbitrary object a validated payload. AX torque-limit register values are not calibrated jaw-force measurements.

## Movement, stability and print checks required before release

1. Export each printable part as a separate closed, consistently oriented mesh in millimetres; check manifold edges, thickness and connected components. Motor/electronic reference meshes must never enter the print set.
2. A1 nominal build volume is 256 mm per side. Verify every oriented part's bounds, including a margin for brim and printer exclusions, rather than assuming the complete assembly is printable in one piece.
3. Use actual mating holes and nut pockets. Check nominal coaxiality, slot insertion, tool access and screw stack length numerically. Check clearances after printing coupons.
4. Parent each body to its actual joint frame. Gear relationships are theta_out = -theta_motor/N, with correct initial tooth phase. Paired gripper gears rotate equally and oppositely. A kinematic driver is not a force or friction solver.
5. Sweep joint ranges and sample combined poses. Check gear and bushing contacts separately from forbidden body collisions; contact intended for meshing must not be misreported as an assembly clash. Check cables manually in extreme poses.
6. With J1 3:1 and an AX positional span of 300 degrees, theoretical yaw travel is only 100 degrees. An initial software range of +/-45 degrees leaves some margin. More reduction also reduces output speed and usable positional range. J2 4:1 should use a deliberately limited output arc with the corresponding motor range/mode accounted for.
7. Prevent tipping. A free-standing 220 mm box is not automatically stable against a 1.23 Nm arm moment. At a 100 mm support half-width, even a simplified 1.5 Nm resisting target requires about 1.53 kg effective weight behind the tipping edge. Use printed table-edge clamps with the user's screws/nuts or a positively screwed-down mount; do not hide an unspecified metal ballast in the base.
8. Initial test is unloaded, slow, and short. Measure base breakaway torque, backlash, printed-journal heating, servo temperature and actual printed masses. Recalculate moments for the as-built masses, then test 25 g before considering 50 g. Stop before any servo/PLA thermal or deformation limit.

## Primary references checked

- [ROBOTIS AX-12A manual](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/): published motor dimensions, mass, voltage/position range, stall torque, and one-fifth-stall design guidance.
- [ROBOTIS XM430-W350-T specification](https://robotis.us/products/dynamixel-xm430-w350-t): motor dimensions, 82 g mass, 4.1 Nm stall, and the explicitly estimated 0.82 Nm continuous value. The manufacturer's radial/axial load limits apply to its output, not to a guaranteed tip payload for this arm.
- [ROBOTIS XM430-W350-T engineering specification](https://www.robotis.com/shop/item.php?it_id=902-0124-000): available operating modes, dimensions and rated-voltage data; continuous-operation fields are unfilled.
- [ROBOTIS U2D2 manual](https://emanual.robotis.com/docs/en/parts/interface/u2d2/): interface layout and separate motor power requirement; confirm connector revision against the user's unit.

Conclusion: a compact low-payload educational prototype is mechanically plausible with actual external J2/J3 reductions, independently supported printed pivots, a secured base and measured fit/friction. This study does not certify that a visual model, an animation or the untested printed assembly works under load.

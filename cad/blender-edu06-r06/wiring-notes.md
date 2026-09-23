# EDU06 R06 wiring and service routing

The six motors share one half-duplex TTL bus. They are addressed peers and parallel electrical loads. The drawing's physical cable order is:

`PC USB → U2D2 → external power-injection junction → J1 AX → J2 XM → J3 XM → J4 AX → J5 AX → gripper AX`

An external regulated supply injects VDD and GND at the junction. **U2D2 does not supply motor power.** The junction shown in Blender is a generic reserved envelope; its particular board, fuse, current rating and terminals have not been selected. The separate slotted mounting plate is adaptable, not a claim of a verified PCB hole pattern. U2D2's published case envelope is 48 × 18 × 14.9 mm. Its USB revision must be checked: ROBOTIS changed from Micro-B to USB-C in August 2025. [ROBOTIS U2D2 manual](https://emanual.robotis.com/docs/en/parts/interface/u2d2/)

## Connector families and polarity

| Motor/interface | Cable housing | Pin 1 | Pin 2 | Pin 3 |
|---|---|---|---|---|
| AX-12A | Molex 50-37-5033 | GND | VDD | DATA |
| XM430-W350-T | JST EHR-03 | GND | VDD | DATA |
| U2D2 TTL | JST EHR-03 | GND | VDD | DATA |

The XM-to-AX links require the correct Molex–JST conversion cable; the housings are mechanically different. ROBOTIS specifies 21 AWG cable for these interfaces. The model's black/red/yellow colors mean GND/VDD/DATA; do not infer physical pin order from a camera view or a third-party cable's colors. Check the keyed connector orientation and numbered pins on the actual hardware before powering it. [AX connector specification](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/#connector-information), [XM connector specification](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#connector-information), [ROBOTIS XM package and conversion cable](https://en.robotis.com/shop_en/item.php?it_id=902-0124-000)

## What the connector geometry establishes

All motor coordinates use the installed stock-horn front as Z = 0, output along +Z, case height along Y.

- **AX:** the two separately identified official STEP headers have X ranges −9.9…0 and 0.1…10.0 mm, Y −17.62…−12.72 mm and Z −33.70…−24.30 mm. Rear-facing connector route datums are at X −4.95/+5.05, Y −15.17, Z −33.70 mm.
- **XM:** the official STEP cable cover has openings on both **side faces**, X = ±14.25 mm. Their centre is Y = −14.55 mm; the visible opening extends approximately Z −32.20…−27.55 mm. Route datums use Z = −29.875 mm and the outward direction ±X. These are case-exit datums; the simplified CAD does not establish the hidden electrical contact depth.
- The displayed cable plug envelopes are provisional purchased-part references. They are not printable housings and do not establish verified connector engagement. Measure actual plug bodies, latch access and crimp exits before manufacturing adjacent guides.
- The final gripper's second socket is intentionally unused. No unattached cable is placed there.

The motor solids are the official ROBOTIS STEP tessellation already documented in `motor-references/README-official-cad.md`. Printed cradles retain access to the AX rear sockets and XM side exits. Cable clearance still needs to be checked with the actual supplied housing/latch revision.

## Bus configuration

Assign six unique IDs, for example 1–6 in the physical order above. Set a common supported baud rate before connecting the full chain; 1 Mbps is a supported candidate. AX uses Protocol 1.0; XM defaults to Protocol 2.0. A controller retaining that mixed configuration must send model-specific packet formats sequentially on the same half-duplex bus, use the correct control-table addresses, and avoid overlapping replies. XM can be switched to Protocol 1.0, but that can restrict access to some control-table areas; this design does not silently change the motors' configuration. [AX control table](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/), [XM Protocol Type and baud-rate settings](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#protocol-type13), [ROBOTIS SDK](https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/)

## Power is an unresolved hardware selection

At 12 V, published stall currents total **10.6 A**: four AX motors at 1.5 A and two XM motors at 2.3 A. Stall is an exceptional operating condition, not a continuous design target. This sum does **not** rate the first cable, connector, power junction or supply. With a single upstream feed, early harness sections carry the sum of downstream currents. Choose protective current limits and rated distribution hardware, then measure voltage drop and connector temperature under the intended load. Additional fused VDD/GND feeds may be needed; DATA remains the common TTL bus. No safe simultaneous full-stall operating condition is claimed. [AX electrical specification](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/#specifications), [XM electrical specification](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#specifications)

## Mechanical route and Blender behavior

The old decorative motor looms and service leads are removed. Every new conductor uses a NURBS spline whose control coordinates are driven by native world-space transform variables. Both endpoints follow connector-attached empties; intermediate guides follow the relevant rigid link or a weighted moving service loop. Forward and backward parallel-transport frame chains use native rotation/track constraints to orient the separate conductors. The connector pin-row orientations are retained. This dependency network survives saving/reopening without a frame handler or an auto-run Python script.

The base USB jacket is 4.7 mm in diameter through the 5.2 mm split saddle; the external DC jacket is 5.6 mm through the 6.4 mm saddle. These are routing assumptions, not measurements of the user's cables. Saddle axes and rear wall openings come from `base_module.py`; use its actual screw/nut stack. The front accessory bay is kept reserved. The fixed-to-yaw loom uses the hollow yaw shaft, with allowance for the limited yaw range rather than unlimited rotation.

`wiring-connectivity.json` records connector endpoints, cable families, conversion links, conductor colors and native guide names. `audit_wiring.py` checks 31 animation frames for endpoint attachment, approximate minimum curve radius, route-length variation and clearance to actual printed parts and manufacturer motor cases. `--operating-range` additionally checks the 19 named within-limit poses generated by the independent mechanical auditor, including individual extremes, combined extremes and wrist corner poses. These discrete screens do not prove every point of the continuous workspace.

The clearance envelope follows the actual evaluated outer conductors plus their 0.72 mm assumed insulation radius. Connector pin pitch is 2.5 mm; intermediate bundle pitch defaults to 1.8 mm, with explicit guide overrides up to 3.0 mm on selected free loops and strain-relief approaches to keep the insulation separate. Each actual guide pitch is recorded in the connectivity manifest. Nearest sampled point-to-polyline distances check strand separation against the 1.44 mm modelled insulation diameter. The only motor-case exemption is that endpoint's own case within 18 mm of its wire exit, on the outward side of the matching port mouth; no printed parts or other motor cases receive that exemption. Hidden plug engagement remains provisional. Fixed USB and DC jacket screening is reported separately because those routes have intentional close-fitting saddle interfaces.

The initial bend-radius target is 12 mm; replace it with the selected cable manufacturer's dynamic bend specification. Provisional cut lengths include additional slack beyond the sampled maximum geometric route. Upper service-loop control anchors are kinematic references, not additional installed printable clips. The modelled screw clamps retain the base USB and power jackets; upper-link cable retention and strain relief still need to be established using the selected cables and physical travel checks.

Strand-spacing checks compare the three conductors within each harness. They do not establish clearance between different harnesses or an exhaustive self-contact solution for a flexible cable.

The wire curves do not have separately weighed masses or measured centres of mass. The load audit uses a 10% lumped moving-mass allowance for screws and wiring; it has not been verified against the actual selected harness and hardware. Weigh the finished moving harness and fasteners before treating the payload estimate as established.

## Final saved-model checks

The final R06 model passed the complete 31-frame animation screen and 19 named operating-pose screen. Each contains all seven TTL harnesses and 28 curves: seven route centrelines and 21 conductors. All five checks passed: attached endpoints, gear clearance, printed-part/motor-case clearance, at least 12 mm sampled conductor bend radius, and separation of the three conductors within each harness.

Across those 50 samples, the minimum conductor bend radius was **12.176 mm**, the minimum within-harness strand centre separation was **1.481 mm** against 1.44 mm modelled insulation diameter, and the minimum structural envelope gap was **0.596 mm** against the 0.5 mm screen target. Maximum endpoint drift was **0.000 mm**. The final reports are `wiring-audit.json`, `wiring-operating-range-audit.json` and the compact `wiring-final-summary.json`; fixed USB/DC jackets have their own `fixed-jacket-audit.json`.

The seven provisional segment cut lengths total **3.33 m of three-conductor harness** (9.99 m of individual conductor before trimming). These include the chosen slack allowance and use the largest sampled conductor path, not just the centreline. They remain fitting estimates: select the real connectors/cable and prove free travel before cutting the final harness.

**This is a geometric kinematic harness, not a constant-length flexible-body simulation.** Curve shape changes do not prove insulation strain, torsional life, latch retention, continuous swept clearance or fatigue. A failed route audit must be fixed or reported as unresolved. Before powered operation, assemble the actual cables, move all axes through their limits by hand with power off, verify that no cable is pulled taut or can enter teeth, and secure the final guides without pinching insulation.

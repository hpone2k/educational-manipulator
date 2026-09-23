"""Summarize completed independent checks without upgrading them to physical proof."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
stl=json.loads((ROOT/'stl-audit.json').read_text())
audit=json.loads((ROOT/'mass-load-audit.json').read_text())
gear=json.loads((ROOT/'gear-profile-audit.json').read_text(encoding='utf-8-sig'))
assert audit.get('complete'), 'Wait for complete load/motion audit'
poses=[p for p in audit['poses'] if not p['outside_declared_limits']]
home=next(p for p in poses if p['name']=='home')
def case(p,g=25):return next(c for c in p['load_cases'] if c['payload_g']==g)
rows=[]
for j in ['J2','J3','J4','J5','J6']:
    h=case(home)['joints'][j]
    maximum=max(case(p)['joints'][j]['estimated_motor_gravity_torque_nm'] for p in poses)
    rows.append(f"| {j} | {h['ratio']:g}:1 | {h['estimated_motor_gravity_torque_nm']:.3f} | {maximum:.3f} | {1.5*maximum:.3f} | {h['comparison_nm']:.2f} |")
s=stl['summary'];a=audit['summary'];m=audit['mass_summary']
failures=a['load_cases_exceeding_gravity_motor_comparison']
within=[r for r in failures if not r['outside_declared_limits']]
physical='No physical prototype has been assembled or loaded. This release is an editable, dimensioned engineering prototype, with prototype STL exports. It is not a certified payload rating or a production release.'
report=f'''# EDU06 R03 — engineering review

{physical}

The Blender scene is the actual manufacturing geometry and kinematic assembly. Its green/ivory appearance follows the concept image. Motor cases, gear centres, printed plain bearings, nut pockets, rear-access screw stacks and link lengths determine the geometry; they are not traced from an AI image. All fabricated structure, gears, bushings, journals and spacers are printed. Purchased motors retain their supplied hardware; additional fastening hardware is nuts and screws.

## Completed digital checks

| Check | Recorded result | Scope |
|---|---|---|
| Exported STL geometry | {s['passed']}/{s['parts_found']} passed; {s['failed']} failed; {s['requires_review']} review | Nondegenerate triangles, closed consistently directed edges, positive volume, connected surface, grounded and within a 256 mm cube |
| Exact gear-profile samples | {sum(x['tested_phases'] for x in gear['checks'])} samples across four pairs; {gear['status']} | 61 phases over each pinion tooth pitch, polygon penetration checks and deliberately wrong-phase negative control |
| Joint/control responses | {audit['control_response_checks']['control_count']} controls × {audit['control_response_checks']['samples_per_control']} values; all passed = {a['control_response_all_passed']} | Evaluated output angles, pinion ratios, end-effector pose and jaw opening |
| Assembly pose samples | {a['pose_count']} poses, including an explicitly out-of-range horizontal stress case | Mesh intersection/containment screening at selected poses, not continuous collision proof |
| Physical validation | Not performed | Print fit, strength, friction, creep, heat, durability and powered operation remain unmeasured |

Audit details and limitations are retained in `stl-audit.json`, `gear-profile-audit.json` and `mass-load-audit.json`. STL topology checks do not test every possible triangle self-intersection or establish minimum wall strength. Collision screening excludes same-body mating parts, fasteners and visual cables; the manual fastener-stack review is separate.

## Dimensions and moving interfaces

| Feature | Nominal geometry in mm |
|---|---|
| Base | 240 × 190 nominal floor; 241 × 190 actual case envelope including tab ends; 5 floor; 4 walls; lid top95; printed feet8 |
| AX-12A envelope / purchased mass | 32 × 50 × 40 / 54.6 g |
| XM430-W350-T case / purchased mass | 28.5 × 46.5 × 34 / 82 g; installed horn datum detailed in motor guide |
| U2D2 envelope | 48 × 18 × 14.9; tray centred at(-61,-64), above the base floor |
| Yaw | 20/60 teeth, module1.5, centre distance60, 10 face width |
| Shoulder | 20/80 teeth, module1.25, centre distance62.5, 12 face width |
| Elbow | 20/60 teeth, module1.25, centre distance50, 10 face width |
| Gripper | 20/20 teeth, module1.5, centre distance30, 6 face width; pivoting jaws |
| Gear profile | 20° involute working flanks; nominal total tangential backlash0.20; relieved radial roots, no tooth-fatigue validation |
| Upper arm | 100 pivot spacing; hollow printed corner rails |
| Forearm | 85 nominal beam length plus integral roll-motor bulkhead; see actual joint datums for complete reach |
| Main yaw journal | Ø32 printed shaft, Ø32.5 running bore; two separated sleeves and printed thrust ring |
| Shoulder / elbow journals | Ø24 / Ø20 shafts, Ø24.5 / Ø20.5 bores; printed retainers leave axial clearance |
| Pinion journals | Ø8 / Ø8.5 running fits |
| General M3 clearance / nut | Ø3.4 / 5.8 across-flats pocket; side-loading entrances6.4 where used |

AX and XM horn patterns use Ø16 pitch circles with four/eight M2 holes respectively. AX pinion/gripper M2×6 through4 mm floors gives2 mm engagement; XM M2×6 through4.5 mm gives1.5 mm. Raised wrist adapters use AX M2×10 through7 mm, giving3 mm engagement. Compare the supplied horn revision, actual screw length and printed thickness before fastening. Manufacturer datum drawings, mounting stacks and assembly sequence are in `motor-and-fastener-guide.md` and `motor-interface-schedule.json`.

The elbow's front/rear supports are tied with four38 mm printed spacers and shared M3×70 bolts. Central pivot-retaining bolts load rotating shafts/caps rather than clamping stationary bearing cheeks. The gripper idler uses a stationary compression sleeve so tightening its bolt does not lock the rotating jaw. Base-lid and deck-flange nuts have side-loading pockets with material above them to carry screw tension. The base uses sliding polymer bearings: gears provide reduction, but do not eliminate bearing friction.

## Gravity and motor-torque screening

The selected planning payload is **25 g**, pending the user's intended object weight. It is a calculation input, not an approved operating payload. Five AX motors plus two XM motors alone weigh437 g; distal AX motors make the wrist mass significant.

Printed mass is integrated from the closed CAD volumes at PLA1.24 g/cm³, assuming solid material. Actual sliced mass depends on walls, infill and supports. A10% allowance is added to moving mass for fasteners and wiring. Motor centres of mass use the external reference envelopes. Gravity calculations use:

`joint torque = axis · Σ[(centre of mass − joint origin) × mass × gravity]`

`estimated motor torque = |joint torque| / (gear ratio × assumed efficiency)`

Total printed solid mass: **{m['total_printed_structural_solid_mass_g']:.0f} g**. Moving mass before/after the10% allowance: **{m['moving_mass_g_before_allowance']:.0f} / {m['moving_mass_g_with_10percent_allowance']:.0f} g**. These are CAD estimates, not weighed parts.

The following are motor-shaft torques in N·m with25 g at the fingertips. Maxima use only the sampled poses inside the declared limits. The1.5 column is an illustrative extra allowance, not a dynamics simulation.

| Joint | Ratio | Home gravity | Sampled maximum | Maximum ×1.5 | Planning comparison |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

The comparisons0.30 N·m AX /0.82 N·m XM are20% of published stall values. They are **not manufacturer continuous-duty guarantees**. See the JSON for assumed gear efficiencies. There are **{len(within)}** sampled gravity cases above these comparisons across the0/25/50 g load cases within the declared limits. A zero gravity torque at vertical yaw does not mean zero required torque: breakaway friction, acceleration and cable forces are absent from that value. Full bending moments on the joint bearings are also recorded separately; motor-axis torque alone cannot validate those bearings.

## Motion limits and remaining checks

Declared control ranges are J1 −40…40°, J2 45…85°, J3 30…75°, J4 −50…50°, J5 −30…30°, J6 −50…50°, GRIP0…24°. These are modeled ranges, not verified servo calibration values. Rotation signs and horn assembly zeros must be mapped to physical servo IDs before any powered test. There is no motor-control script in this release.

Pose names with sampled gross interpenetration: **{', '.join(a['poses_with_sampled_gross_interpenetration']) or 'none'}**. Poses flagged for crossing/contact review: **{', '.join(a['poses_requiring_collision_review']) or 'none'}**. Contact classifications and sampled penetration points are preserved for inspection; intended contacts are not silently reported as a universal clearance pass. The rigid-body animation is not a friction/contact simulation.

Before printing the full arm, print the hole/nut coupon, both horn coupons, one cradle/shim set and a shaft/bushing pair. Confirm material identity and measure actual parts with calipers. The0.20 mm spacers and0.30 mm shims require suitable layer settings and measurement. STL orientation is an initial export orientation; inspect supports, bridging, layer direction and small-feature resolution in Bambu Studio. A1 volume fit excludes brim and plate restrictions.

Before assigning a payload, measure breakaway/running torque of the printed bearings, check gear tooth/root strength and backlash, measure joint deflection, establish stable mounting, and perform supported low-speed thermal/load tests. PLA creep, friction and layer strength are not solved by mesh checks. Wrist AX horns still transmit wrist bending loads; allowable radial/axial loads and printed-carrier stiffness need verification. There is no finite-element analysis, full cable-flex simulation, fatigue test or load certification in this release. Visual cable curves reserve routes but do not replace real service-loop fitting. U2D2 is the communication adapter; motor power requires its own appropriate supply and distribution.

## Primary references

- [ROBOTIS AX-12A](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/)
- [ROBOTIS XM430-W350](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/)
- [ROBOTIS U2D2](https://emanual.robotis.com/docs/en/parts/interface/u2d2/)
- Manufacturer drawing extracts and datum research: `research-motors.md`.
'''
demo_path=ROOT/'demo-trajectory-audit.json'
if demo_path.exists():
    demo=json.loads(demo_path.read_text())
    summary=demo['summary']
    report=report.replace('## Dimensions and moving interfaces',f"The saved animation was also checked at **{summary['sample_count']} actual timeline snapshots**. Unresolved crossings/penetrations: **{len(summary['frames_with_unresolved_crossings_or_penetrations'])}**; joint-limit violations: **{len(summary['frames_outside_declared_joint_limits'])}**. See `demo-trajectory-audit.json`. This is discrete sampling, not a continuous swept-volume proof.\n\n## Dimensions and moving interfaces")
report=report.replace('A zero gravity torque at vertical yaw does not mean zero required torque:', 'J1 is excluded from the motor-gravity table because its axis is vertical. Zero gravity torque at yaw does not mean zero required torque:')
report=report.replace('## Motion limits and remaining checks','The illustrative 1.5× allowance exceeds the planning comparisons at several joints, including shoulder and elbow. The 50 g static shoulder case has only about 4% margin. Retain 25 g as a provisional fit/load-testing target; no operational payload is assigned. The 25 g static centre-of-mass projection remains at least 37.46 mm inside the foot-centre support polygon in the sampled poses. This does not replace bench attachment or dynamic tipping checks.\n\n## Motion limits and remaining checks')
for word in ['four','module','distance','width','backlash','floor','walls','top','feet','weigh','PLA','A','the','with','The','comparisons','are','across','giving','through','circles','patterns','GRIP']:
    report=re.sub(r'\b'+word+r'(?=\d)',word+' ',report)
report=report.replace('0/25/50','0 / 25 / 50').replace(' g; installed',' g; installed')
(ROOT/'engineering-review.md').write_text(report,encoding='utf-8')
print('Wrote engineering-review.md from completed audits')

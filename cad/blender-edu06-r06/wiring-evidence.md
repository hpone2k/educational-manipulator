# H06 gripper wiring evidence

The J5-to-gripper harness uses the existing Ø26 mm fixed wrist heel opening, an external service loop, and the gripper's 20 × 10 mm rear passage with its 20 mm open assembly gap. Motor connector datums and printed geometry were not changed to route it. `gripper_wiring_guides.py` contains the local guide coordinates.

The supplemental checks used a separate native test scene built from the completed R06 mechanical assembly:

| Check | Recorded result |
|---|---|
| 31 animation frames | Endpoints attached; no sampled structure/gear contact; bend and strand-spacing targets met |
| 19 named operating poses, including combined arm limits | Same checks passed |
| 275 wrist combinations at 5° increments; 401 points per curve | Minimum individual-wire radius **12.263 mm**, against the provisional 12 mm target |
| Closest sampled wire-to-polyline spacing across those wrist combinations | **1.573 mm** between wire centres, versus **1.44 mm** modelled insulation diameter |

Native forward/backward frame transport keeps the wire layout consistent around bends. Three external loop guides use 2.4 mm wire-centre pitch; constrained passages retain the default 1.8 mm pitch and connector endpoints retain 2.5 mm pin pitch. Checking only equal curve parameters would miss wires that touch at neighbouring parameters; the supplementary spacing check compares each sampled point to nearby segments of the other wires.

These results are summarized in [H06-route-evidence.json](H06-route-evidence.json). The final delivery-wide [wiring-audit.json](wiring-audit.json), [wiring-operating-range-audit.json](wiring-operating-range-audit.json) and [wiring-kinematics-audit.json](wiring-kinematics-audit.json) govern the delivered native model.

This is a kinematic routing prototype. The geometric route length varies with motion; guide empties are not installed clips. These checks do not establish constant cable length, connector fit, strain relief, fatigue, continuous swept clearance or contact between separate harnesses. Select and measure the actual cables, then fit their retention and verify full unpowered travel before operation. Electrical assumptions and connector families are in [wiring-notes.md](wiring-notes.md).

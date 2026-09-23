# EDU-06 DYNAMIXEL concept — 23 September 2026

This is an image-led design study, not a verified CAD assembly or a printable file. Motor casings, gear engagement, tooth counts, axis packaging and clearances in the AI illustration are approximate. Use the intended architecture below rather than taking dimensions or gear tooth counts from the image.

## Joint assignment
Six independent arm axes, with gripper opening separate:
- J1 base yaw: AX-12A, proposed external 3:1 spur reduction.
- J2 shoulder pitch: XM430-W350-T, proposed external 4:1 reduction.
- J3 elbow pitch: XM430-W350-T, proposed external 2:1 reduction.
- J4 forearm roll: AX-12A.
- J5 wrist pitch: AX-12A.
- J6 tool roll: AX-12A.
- G gripper: additional AX-12A, central pinion driving two opposed racks on supported parallel guides.
Total: five AX-12A + two XM430-W350-T. If the gripper is counted as the sixth actuator, that would instead be five arm axes plus gripper.

## Proposed construction
Short ribbed plastic links, split covers, captive metal nuts, bearing-supported shafts, bolted base and printed motor brackets tailored separately to AX and XM mounting patterns. All custom structural parts and external gears are intended to be printed; motors, shafts, bearings, nuts, bolts and guide rails remain purchased hardware. Filament, print orientation, tooth strength, creep, fit and fastening details remain open.

Upper-arm and forearm pivot spacings: 140 and 120 mm. Preliminary distal assembly extends another 150 mm to the tool centre; horizontal shoulder-to-tool distance approximately410 mm. These are proposed study dimensions, not dimensions extracted from the image.

The base turntable bearing carries weight and overturning moment; it does not eliminate the overturning load. Gearing trades speed/travel for torque and introduces losses and backlash. Bearing selection must check axial/radial load, overturning moment, stiffness, mounting and preload. A simple turntable product without a moment rating is not yet selected.

An illustrative base gear layout is module2, 20-tooth pinion and60-tooth externally toothed driven gear: pitch diameters40 and120 mm, shaft centres80 mm. Both axes vertical and gears coplanar, small gear outside the large gear. Final gear guard and bolt clearance may enlarge the nominal220x200 mm base. The generated image's other tooth-count/diameter text is not a released gear specification.

AX-12A position travel is300 degrees: external3:1 base reduction leaves at most100 degrees total base travel, before mechanical/cable restrictions. Wider travel requires a different control architecture, e.g. external output sensing and a homed closed-loop controller with wheel mode. Wheel mode alone does not retain joint-mode position control. Do not promise360-degree positioning from the standard servo encoder through this reduction.

## Preliminary moment calculation
Horizontal straight-arm screening case, gravity9.80665 m/s². Below are assumed lumped component masses and horizontal positions from J2. Servo masses use manufacturer data; structure/transmission/hardware mass budgets are provisional targets and must be replaced by CAD/measured masses. The wrist frame is lumped near J5. This is not an all-pose load envelope.

| Assumed lump | Mass kg | Horizontal position from J2 m |
|---|---:|---:|
| upper | 0.1 | 0.07 |
| elbow | 0.082 | 0.14 |
| forearm | 0.08 | 0.2 |
| AX4 | 0.0546 | 0.26 |
| AX5 | 0.0546 | 0.295 |
| AX6 | 0.0546 | 0.33 |
| AXg | 0.0546 | 0.36 |
| wrist frame | 0.06 | 0.3 |
| gripper | 0.04 | 0.385 |
| payload | 0.1 | 0.41 |

Total distal mass including100 g payload:0.6804 kg.
- J2 static gravity moment:1.734 N·m.
- J3 static gravity moment:0.869 N·m.
- J5 approximate static pitch moment:0.205 N·m.
- J1 vertical yaw has no gravity torque in this ideal stationary case, but the turntable and base structure carry approximately1.734 N·m overturning moment plus the remaining support loads. Yaw drive sizing also needs rotational inertia, acceleration, bearing friction and cable resistance.
- J4/J6 roll moments depend on off-axis centre of gravity and tool orientation; they are not validated by this planar screening calculation.

Manufacturer estimated continuous torque is0.82 N·m XM430-W350-T and0.30 N·m AX-12A, estimated as20% of stall, not a guaranteed application rating.
Assuming80% efficiency for each complete external reduction:
- J2 motor requirement1.734/(4x0.8)=0.542 N·m; estimated joint screening torque0.82x4x0.8=2.624 N·m.
- J3 motor requirement0.869/(2x0.8)=0.543 N·m; estimated joint screening torque0.82x2x0.8=1.312 N·m.
- J5 direct-drive requirement approximately0.205 N·m versus estimated0.30 N·m.
These imply only about1.5 times static headroom in this mass scenario. They exclude acceleration, impacts, wire loads, heavier actual prints, thermal enclosure effects, structural deflection and gear durability. No validated payload rating follows. The100 g figure is a study assumption; not a lifting claim.

Added gear ratios reduce output speed; shoulder/elbow ranges and homing need to be designed around XM430 operating modes. Keep the distal AX motors and gripper compact; adding distal mass is costly at J2. Spring assistance is an optional later study, not credited in these calculations.

## Electrical considerations
AX-12A and XM430-W350-T are TTL smart servos, not steppers. A regulated12 V bus is within both published voltage ranges, but12 V is the AX maximum; do not connect AX motors directly to a fully charged3S pack at12.6 V. Confirm supply behavior and wiring. AX uses Protocol1.0; the XM supports configurable protocol options. Use compatible correctly pinned conversion cables; model mounting patterns/connectors are not interchangeable.

## Primary references
- AX specifications, mass, travel and voltage: https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/
- XM specifications, mass, dimensions, stall torque and modes: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/
- AX estimated continuous torque disclosure: https://robotis.us/products/dynamixel-ax-12a
- XM estimated continuous torque disclosure: https://robotis.us/products/dynamixel-xm430-w350-t

At12 V the e-manual stall figures are1.5 N·m for AX and4.1 N·m for XM. Stall torque is not continuous lifting capability. The current AX US storefront contains an inconsistent stall field; this note uses the AX e-manual's1.5 N·m figure and identifies the storefront's0.30 N·m continuous figure as an estimate.

## Image
Generated with the built-in image-generation tool. Initial generation prompt: dynamixel-edu06-prompt.txt. Refined to clarify base external gearing, wrist roll and gripper racks. Image mechanisms remain illustrative; CAD geometry must establish actual meshes, axes, shaft support and interference before fabrication.


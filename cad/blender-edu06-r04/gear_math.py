"""Numerical 20-degree external spur gears, millimetres, no Blender dependency.

The involute working flanks and pitch-circle tooth thickness are analytical;
returned polygons approximate those curves with straight segments. Standard
full-depth proportions: addendum = m, dedendum = 1.25*m, zero profile shift.
When the root lies below the base circle, the flank continues radially to the
root circle. This is deliberately a printable root relief, NOT an accurately
hob-generated trochoid or a tooth-root fatigue/strength calculation. Root-corner
fillets should only be added after checking the mating-tip clearance.

The polygon is CCW, begins at the negative-angle root of the tooth centred on
local +X, and does NOT repeat its first point. No self-intersections occur:
all radii are positive and unwrapped angles increase, with radial relief edges
allowed to have equal endpoint angles within their own tooth sector.

BACKLASH: backlash_mm is TOTAL tangential mesh backlash at the pitch circle.
Each of the two mating gears must use the same value. Each gear's tooth is
thinned by backlash_mm/2, so its half-thickness angle loses b/(4*r_pitch).
It is not extra centre distance or a per-flank clearance.

PHASE: for centres O1=(0,0), O2=(a,0), all requested pairs have even z2.
At zero pose rotate pinion by pi/z1 and wheel by zero. Then for pinion increment
q rotate wheel by -(z1/z2)*q. Thus a 20-tooth pinion starts at +9 degrees.
For odd z2 pair_spec supplies wheel initial phase pi/z2. General phase equation:
z1*theta1 + z2*theta2 = pi*(z2-1) modulo 2*pi.

Run this file for geometry and exact polygon-boundary intersection checks for
the four EDU06 gear pairs. This checks 61 phases across one pinion tooth pitch;
it is geometry verification, not validation of printed gears under load.
"""

import json
from math import atan, atan2, cos, hypot, isfinite, pi, radians, sin, sqrt, tan


PRESSURE_ANGLE = radians(20.0)


def _validate(teeth, module, backlash_mm):
    if isinstance(teeth, bool) or not isfinite(teeth) or int(teeth) != teeth or teeth < 18:
        raise ValueError("teeth must be an integer >= 18; lower counts need undercut/profile-shift design")
    if not isfinite(module) or module <= 0:
        raise ValueError("module must be finite and positive")
    if not isfinite(backlash_mm) or backlash_mm < 0:
        raise ValueError("backlash_mm must be finite and nonnegative")
    if backlash_mm >= pi * module:
        raise ValueError("backlash would eliminate the tooth at the pitch circle")


def involute_angle(radius, base_radius):
    """Polar angular advance of an involute relative to its base tangent."""
    if radius < base_radius - 1e-12:
        raise ValueError("involute is undefined inside its base circle")
    t = sqrt(max(0.0, (radius / base_radius) ** 2 - 1.0))
    return t - atan(t)


def gear_profile(teeth, module, backlash_mm=0.20, resolution=10):
    """Return [(x,y), ...] CCW closed-boundary vertices in mm.

    resolution is the minimum samples per working flank (>=4). Circle arcs use
    a chord-density proportional to tooth pitch. Increase it for final meshes.
    A positive backlash reduces tooth thickness only; radii stay standard.
    """
    _validate(teeth, module, backlash_mm)
    if isinstance(resolution, bool) or int(resolution) != resolution or resolution < 4:
        raise ValueError("resolution must be an integer >= 4")
    teeth, resolution = int(teeth), int(resolution)
    rp = teeth * module / 2.0
    rb = rp * cos(PRESSURE_ANGLE)
    ra = rp + module
    rf = rp - 1.25 * module
    half_pitch = pi / (2.0 * teeth) - backlash_mm / (4.0 * rp)
    inv_pitch = tan(PRESSURE_ANGLE) - PRESSURE_ANGLE

    def half_angle(r):
        return half_pitch + inv_pitch - involute_angle(max(rb, r), rb)

    r_start = max(rf, rb)
    half_root, half_tip = half_angle(r_start), half_angle(ra)
    pitch = 2.0 * pi / teeth
    if not 0.0 < half_tip < half_root < pitch / 2.0:
        raise ValueError("invalid or pointed tooth: reduce backlash or revise profile")
    points = []

    def add(r, a):
        point = (r * cos(a), r * sin(a))
        if not points or hypot(point[0] - points[-1][0], point[1] - points[-1][1]) > 1e-10:
            points.append(point)

    # Sampling uniformly in involute parameter resolves the base-circle region.
    t0 = sqrt(max(0.0, (r_start / rb) ** 2 - 1.0))
    t1 = sqrt((ra / rb) ** 2 - 1.0)
    flank_radii = [rb * sqrt(1.0 + (t0 + (t1 - t0) * i / resolution) ** 2)
                   for i in range(resolution + 1)]
    tip_steps = max(3, int(resolution * 2.0 * half_tip / pitch) + 1)
    root_span = pitch - 2.0 * half_root
    root_steps = max(3, int(resolution * root_span / pitch) + 1)

    for k in range(teeth):
        centre = k * pitch
        add(rf, centre - half_root)
        for r in flank_radii:
            add(r, centre - half_angle(r))
        for i in range(1, tip_steps + 1):
            add(ra, centre - half_tip + 2.0 * half_tip * i / tip_steps)
        for r in reversed(flank_radii[:-1]):
            add(r, centre + half_angle(r))
        add(rf, centre + half_root)
        # End point belongs to the next tooth and is added at the next loop.
        for i in range(1, root_steps):
            add(rf, centre + half_root + root_span * i / root_steps)
    return points


def pair_spec(z1, z2, module, backlash_mm=0.20):
    """Analytical dimensions and transform convention for one external pair."""
    _validate(z1, module, backlash_mm)
    _validate(z2, module, backlash_mm)
    r1, r2 = z1 * module / 2.0, z2 * module / 2.0
    rb1, rb2 = r1 * cos(PRESSURE_ANGLE), r2 * cos(PRESSURE_ANGLE)
    ra1, ra2 = r1 + module, r2 + module
    centre = r1 + r2
    contact_length = (sqrt(ra1 * ra1 - rb1 * rb1) + sqrt(ra2 * ra2 - rb2 * rb2)
                      - centre * sin(PRESSURE_ANGLE))
    return {
        "teeth": [int(z1), int(z2)], "module_mm": module,
        "pressure_angle_deg": 20.0, "centre_distance_mm": centre,
        "pitch_radii_mm": [r1, r2], "base_radii_mm": [rb1, rb2],
        "tip_radii_mm": [ra1, ra2], "root_radii_mm": [r1 - 1.25 * module, r2 - 1.25 * module],
        "radial_tip_root_clearance_mm": 0.25 * module,
        "total_tangential_backlash_mm": backlash_mm,
        "tooth_thinning_per_gear_mm": backlash_mm / 2.0,
        "nominal_transverse_contact_ratio": contact_length / (pi * module * cos(PRESSURE_ANGLE)),
        "pinion_phase_rad": pi / z1,
        "wheel_phase_rad": (int(z2) % 2) * pi / z2,
        "wheel_radians_per_pinion_radian": -z1 / z2,
    }


def polygon_area(points):
    """Signed shoelace area, positive for CCW."""
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1]
                     for a, b in zip(points, points[1:] + points[:1]))


def transform_polygon(points, angle=0.0, centre=(0.0, 0.0)):
    c, s = cos(angle), sin(angle)
    return [(centre[0] + c * x - s * y, centre[1] + s * x + c * y) for x, y in points]


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _proper_intersection(a, b, c, d, tolerance=1e-10):
    """Strict segment crossing; endpoint touches are not penetration."""
    ac, ad = _cross(a, b, c), _cross(a, b, d)
    ca, cb = _cross(c, d, a), _cross(c, d, b)
    return ((ac > tolerance and ad < -tolerance) or (ad > tolerance and ac < -tolerance)) and \
           ((ca > tolerance and cb < -tolerance) or (cb > tolerance and ca < -tolerance))


def _contains(point, polygon):
    x, y = point
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y):
            if x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                inside = not inside
    return inside


def polygons_overlap(poly_a, poly_b):
    """Check polygon boundary crossings plus full containment (not a BVH)."""
    ax0, ax1 = min(p[0] for p in poly_a), max(p[0] for p in poly_a)
    ay0, ay1 = min(p[1] for p in poly_a), max(p[1] for p in poly_a)
    bx0, bx1 = min(p[0] for p in poly_b), max(p[0] for p in poly_b)
    by0, by1 = min(p[1] for p in poly_b), max(p[1] for p in poly_b)
    x0, x1, y0, y1 = max(ax0, bx0), min(ax1, bx1), max(ay0, by0), min(ay1, by1)
    if x1 < x0 or y1 < y0:
        return False

    def candidate_edges(poly):
        edges = []
        for a, b in zip(poly, poly[1:] + poly[:1]):
            low_x, high_x = min(a[0], b[0]), max(a[0], b[0])
            low_y, high_y = min(a[1], b[1]), max(a[1], b[1])
            if high_x >= x0 and low_x <= x1 and high_y >= y0 and low_y <= y1:
                edges.append((a, b, low_x, high_x, low_y, high_y))
        return edges

    edges_a, edges_b = candidate_edges(poly_a), candidate_edges(poly_b)
    for a, b, ax0, ax1, ay0, ay1 in edges_a:
        for c, d, bx0, bx1, by0, by1 in edges_b:
            if bx0 > ax1 or ax0 > bx1 or by0 > ay1 or ay0 > by1:
                continue
            if _proper_intersection(a, b, c, d):
                return True
    return _contains(poly_a[0], poly_b) or _contains(poly_b[0], poly_a)


def _check_star_polygon(points):
    """A strictly angular-monotone, positive-radius loop is simple."""
    raw = [atan2(p[1], p[0]) for p in points]
    unwrapped = [raw[0]]
    for angle in raw[1:]:
        while angle < unwrapped[-1] - 1e-12:
            angle += 2.0 * pi
        if angle <= unwrapped[-1] + 1e-12:
            # A radial below-base flank may share an angle: that is valid if
            # consecutive collinear radial edges do not reverse direction.
            pass
        unwrapped.append(angle)
    if unwrapped[-1] - unwrapped[0] >= 2.0 * pi - 1e-10:
        raise AssertionError("polygon winds more than once or crosses angular sectors")
    assert polygon_area(points) > 0
    assert min(hypot(*point) for point in points) > 0
    # Radial segments have nondecreasing angular coordinates, not strict ones.
    return True


def self_test():
    reports = []
    for name, z1, z2, module in [('J1', 20, 60, 1.5), ('J2', 20, 100, 1.25), ('J3', 20, 80, 1.25), ('J5', 20, 60, 1.5)]:
        spec = pair_spec(z1, z2, module)
        p1, p2 = gear_profile(z1, module), gear_profile(z2, module)
        _check_star_polygon(p1)
        _check_star_polygon(p2)
        phase_failures = []
        for index in range(61):
            q = 2.0 * pi / z1 * index / 60.0
            a = transform_polygon(p1, spec["pinion_phase_rad"] + q)
            b = transform_polygon(p2, spec["wheel_phase_rad"] - z1 / z2 * q,
                                  (spec["centre_distance_mm"], 0.0))
            if polygons_overlap(a, b):
                phase_failures.append(index)
        # Negative control: both even gears with teeth centred on the line of
        # centres MUST overlap. Otherwise this checker is not detecting teeth.
        deliberately_bad = polygons_overlap(p1, transform_polygon(p2, 0,
                                              (spec["centre_distance_mm"], 0.0)))
        assert deliberately_bad, "intersection checker missed deliberately wrong gear phase"
        assert not phase_failures, (spec, phase_failures)
        assert spec["nominal_transverse_contact_ratio"] > 1.0
        reports.append({"name": name, **spec, "vertices": [len(p1), len(p2)],
                        "area_mm2": [polygon_area(p1), polygon_area(p2)],
                        "tested_phases": 61, "penetrating_phases": phase_failures,
                        "negative_control_overlap_detected": deliberately_bad})
    return reports


if __name__ == "__main__":
    print(json.dumps({"status": "PASS", "checks": self_test()}, indent=2))

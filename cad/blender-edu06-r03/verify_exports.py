"""Independent binary-STL audit; uses only the Python standard library and NumPy.

Coordinates are interpreted as millimetres. This audits exported geometry, not
mechanical strength, fit, self-intersection, gear contact, or powered motion.
Run with --self-test to exercise positive and negative reference meshes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import sys
import tempfile

import numpy as np


RECORD_DTYPE = np.dtype([
    ("normal", "<f4", (3,)),
    ("vertices", "<f4", (3, 3)),
    ("attribute", "<u2"),
])


def read_binary_stl(path: Path) -> tuple[np.ndarray, np.ndarray]:
    size = path.stat().st_size
    if size < 84:
        raise ValueError("File is shorter than the 84-byte binary STL header")
    with path.open("rb") as handle:
        header = handle.read(84)
        count = struct.unpack_from("<I", header, 80)[0]
        expected = 84 + count * 50
        if size != expected:
            raise ValueError(
                f"Binary STL byte length mismatch: declared {count} triangles "
                f"requires {expected} bytes, actual {size}; ASCII STL is not accepted"
            )
        records = np.fromfile(handle, dtype=RECORD_DTYPE, count=count)
    return (records["vertices"].astype(np.float64),
            records["normal"].astype(np.float64))


def edge_components(face_count: int, inverse: np.ndarray,
                    counts: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Connect faces sharing a complete welded edge, including nonmanifold edges."""
    parents = np.arange(face_count, dtype=np.int64)
    ranks = np.zeros(face_count, dtype=np.int8)

    def find(value: int) -> int:
        while int(parents[value]) != value:
            parents[value] = parents[int(parents[value])]
            value = int(parents[value])
        return value

    def union(first: int, second: int) -> None:
        first, second = find(first), find(second)
        if first == second:
            return
        if ranks[first] < ranks[second]:
            first, second = second, first
        parents[second] = first
        if ranks[first] == ranks[second]:
            ranks[first] += 1

    ordering = np.argsort(inverse, kind="stable")
    starts = np.cumsum(counts) - counts
    for start, count in zip(starts[counts > 1], counts[counts > 1]):
        incident_faces = ordering[int(start):int(start + count)] // 3
        first = int(incident_faces[0])
        for second in incident_faces[1:]:
            union(first, int(second))
    roots = np.fromiter((find(i) for i in range(face_count)),
                        dtype=np.int64, count=face_count)
    _, labels, component_sizes = np.unique(
        roots, return_inverse=True, return_counts=True)
    return labels, [int(value) for value in component_sizes]


def audit_stl(path: Path, weld_tolerance: float = 1e-4,
              ground_tolerance: float = 0.01,
              build_size: float = 256.0) -> dict:
    report = {
        "file": path.name,
        "bytes": path.stat().st_size,
        "status": "fail",
        "checks": {},
        "failures": [],
        "review_notes": [],
    }
    checks = report["checks"]
    failures = report["failures"]
    notes = report["review_notes"]
    try:
        vertices, stored_normals = read_binary_stl(path)
    except (OSError, ValueError) as error:
        report["error"] = str(error)
        failures.append("readable_binary_stl")
        return report

    face_count = len(vertices)
    report["triangle_count"] = face_count
    checks["has_triangles"] = face_count > 0
    if not face_count:
        failures.append("has_triangles")
        return report

    finite_triangle = np.isfinite(vertices).all(axis=(1, 2))
    checks["all_vertex_coordinates_finite"] = bool(finite_triangle.all())
    report["nonfinite_triangle_count"] = int((~finite_triangle).sum())
    report["nonfinite_stored_normal_count"] = int(
        (~np.isfinite(stored_normals).all(axis=1)).sum())
    if report["nonfinite_stored_normal_count"]:
        notes.append("Some stored facet normals are nonfinite; normals can be recomputed")
    if not checks["all_vertex_coordinates_finite"]:
        failures.append("all_vertex_coordinates_finite")
        return report

    flat = vertices.reshape(-1, 3)
    lower, upper = flat.min(axis=0), flat.max(axis=0)
    dimensions = upper - lower
    report["bounds_mm"] = {"min": lower.tolist(), "max": upper.tolist()}
    report["dimensions_mm"] = dimensions.tolist()
    checks["fits_256mm_cube_by_axis_permutation"] = bool(
        (np.sort(dimensions) <= build_size + 1e-5).all())
    checks["grounded_at_z_zero"] = bool(abs(float(lower[2])) <= ground_tolerance)
    checks["no_vertex_below_build_plane"] = bool(float(lower[2]) >= -ground_tolerance)
    report["z_ground_error_mm"] = float(lower[2])

    cross = np.cross(vertices[:, 1] - vertices[:, 0],
                     vertices[:, 2] - vertices[:, 0])
    double_areas = np.linalg.norm(cross, axis=1)
    # The geometric epsilon is much smaller than the coordinate welding grid.
    near_zero_area = double_areas <= 1e-10

    # Integer-grid welding makes the topology check independent of STL vertex
    # duplication and minor float32 round-off. It does not alter exported files.
    quantized = np.rint(flat / weld_tolerance).astype(np.int64)
    welded_vertices, face_ids = np.unique(quantized, axis=0, return_inverse=True)
    face_ids = face_ids.reshape(face_count, 3)
    repeated_vertex = ((face_ids[:, 0] == face_ids[:, 1]) |
                       (face_ids[:, 1] == face_ids[:, 2]) |
                       (face_ids[:, 2] == face_ids[:, 0]))
    degenerate = near_zero_area | repeated_vertex
    report["degenerate_triangle_count"] = int(degenerate.sum())
    report["geometrically_zero_area_triangle_count"] = int(near_zero_area.sum())
    report["triangles_collapsed_at_weld_tolerance"] = int(repeated_vertex.sum())
    checks["all_triangles_nondegenerate"] = not bool(degenerate.any())
    report["welded_vertex_count"] = int(len(welded_vertices))
    report["surface_area_mm2"] = float(double_areas.sum() / 2.0)

    edges = np.stack((face_ids[:, [0, 1]], face_ids[:, [1, 2]],
                      face_ids[:, [2, 0]]), axis=1).reshape(-1, 2)
    undirected = np.sort(edges, axis=1)
    unique_edges, edge_inverse, counts = np.unique(
        undirected, axis=0, return_inverse=True, return_counts=True)
    directions = np.where(edges[:, 0] < edges[:, 1], 1, -1)
    direction_sums = np.bincount(edge_inverse, weights=directions,
                                 minlength=len(counts))
    boundary_count = int((counts == 1).sum())
    nonmanifold_count = int((counts > 2).sum())
    bad_winding_count = int(((counts == 2) & (direction_sums != 0)).sum())
    report["unique_edge_count"] = int(len(unique_edges))
    report["boundary_edge_count"] = boundary_count
    report["nonmanifold_edge_count"] = nonmanifold_count
    report["inconsistently_wound_shared_edge_count"] = bad_winding_count
    checks["every_edge_used_twice"] = bool((counts == 2).all())
    checks["shared_edges_have_opposite_directions"] = bad_winding_count == 0

    labels, component_sizes = edge_components(face_count, edge_inverse, counts)
    report["edge_connected_surface_components"] = len(component_sizes)
    report["component_triangle_counts"] = component_sizes
    checks["single_edge_connected_surface"] = len(component_sizes) == 1
    if len(component_sizes) != 1:
        notes.append(
            "Multiple edge-connected surface shells: inspect for detached solids "
            "or intentional enclosed cavities; this is not automatically a single printable part"
        )

    # An origin near the mesh keeps the closed-surface signed-volume integral
    # numerically stable even when exported coordinates are far from the origin.
    reference = (lower + upper) * 0.5
    local = vertices - reference
    triangle_volumes = np.einsum(
        "ij,ij->i", local[:, 0], np.cross(local[:, 1], local[:, 2])) / 6.0
    signed_volume = float(triangle_volumes.sum())
    component_volumes = np.bincount(labels, weights=triangle_volumes)
    report["signed_volume_mm3"] = signed_volume
    report["signed_volume_cm3"] = signed_volume / 1000.0
    report["component_signed_volumes_mm3"] = component_volumes.tolist()
    checks["positive_signed_volume"] = signed_volume > 1e-9
    report["volume_is_closed_surface_measure"] = bool(
        checks["every_edge_used_twice"] and
        checks["shared_edges_have_opposite_directions"])
    report["euler_characteristic"] = int(
        len(welded_vertices) - len(unique_edges) + face_count)

    for name, passed in checks.items():
        if not passed and name != "single_edge_connected_surface":
            failures.append(name)
    report["status"] = "fail" if failures else ("review" if notes else "pass")
    return report


def write_test_stl(path: Path, triangles: np.ndarray) -> None:
    records = np.zeros(len(triangles), dtype=RECORD_DTYPE)
    records["vertices"] = triangles
    with path.open("wb") as handle:
        handle.write(b"Independent verification reference mesh".ljust(80, b" "))
        handle.write(struct.pack("<I", len(triangles)))
        records.tofile(handle)


def run_self_tests() -> None:
    points = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                       [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], float)
    faces = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
                      [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
                      [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
    cube = points[faces]
    with tempfile.TemporaryDirectory(prefix="edu06_stl_audit_") as directory:
        folder = Path(directory)

        def check(name: str, mesh: np.ndarray) -> dict:
            file_path = folder / f"{name}.stl"
            write_test_stl(file_path, mesh)
            return audit_stl(file_path)

        good = check("unit_cube", cube)
        assert good["status"] == "pass", good
        assert abs(good["signed_volume_mm3"] - 1.0) < 1e-9
        assert good["euler_characteristic"] == 2
        assert good["edge_connected_surface_components"] == 1
        inverted = check("inverted", cube[:, ::-1])
        assert "positive_signed_volume" in inverted["failures"]
        opened = check("open", cube[:-1])
        assert opened["boundary_edge_count"] == 3
        flipped = cube.copy()
        flipped[0] = flipped[0, ::-1]
        assert check("inconsistent", flipped)["inconsistently_wound_shared_edge_count"] == 3
        doubled = check("duplicate_face", np.concatenate([cube, cube[:1]]))
        assert doubled["nonmanifold_edge_count"] == 3
        detached = check("disconnected", np.concatenate([cube, cube + [3, 0, 0]]))
        assert detached["edge_connected_surface_components"] == 2
        assert detached["status"] == "review"
        assert not check("oversize", cube * 300)["checks"]["fits_256mm_cube_by_axis_permutation"]
        assert not check("raised", cube + [0, 0, 1])["checks"]["grounded_at_z_zero"]
        invalid = cube.copy()
        invalid[0, 0, 0] = np.nan
        assert "all_vertex_coordinates_finite" in check("nonfinite", invalid)["failures"]
        zero = np.concatenate([cube, np.zeros((1, 3, 3))])
        assert check("degenerate", zero)["degenerate_triangle_count"] == 1
    print("PASS: 10 independent STL audit reference cases")


def main() -> int:
    location = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=location / "prototype_stl")
    parser.add_argument("--output", type=Path, default=location / "stl-audit.json")
    parser.add_argument("--weld-tolerance", type=float, default=1e-4)
    parser.add_argument("--ground-tolerance", type=float, default=0.01)
    parser.add_argument("--build-size", type=float, default=256.0)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_tests()
        return 0
    if args.weld_tolerance <= 0 or args.ground_tolerance < 0 or args.build_size <= 0:
        parser.error("Weld tolerance/build size must be positive, ground tolerance nonnegative")

    files = sorted(args.input.glob("*.stl"))
    parts = [audit_stl(path, args.weld_tolerance, args.ground_tolerance,
                       args.build_size) for path in files]
    passed = sum(part["status"] == "pass" for part in parts)
    failed = sum(part["status"] == "fail" for part in parts)
    review = sum(part["status"] == "review" for part in parts)
    output = {
        "audit": "independent_binary_stl_geometry_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_directory": str(args.input.resolve()),
        "units": "mm",
        "coordinate_weld_tolerance_mm": args.weld_tolerance,
        "ground_tolerance_mm": args.ground_tolerance,
        "build_cube_mm": [args.build_size] * 3,
        "summary": {
            "parts_found": len(parts), "passed": passed, "failed": failed,
            "requires_review": review, "input_present": bool(files),
            "all_checks_passed": bool(files) and not failed and not review,
            "total_triangles": sum(part.get("triangle_count", 0) for part in parts),
        },
        "limits": [
            "Binary STL carries no units; millimetres are assumed from the export contract.",
            "Build fit uses only axis-aligned dimensions and axis permutations; it excludes brim and printer exclusions.",
            "No triangle-triangle self-intersection, vertex-link manifoldness, wall thickness, tolerance stack or mesh-to-mesh collision test is performed.",
            "Multiple closed surface shells require inspection; an enclosed cavity and a disconnected solid are different cases.",
            "A geometric pass is not a strength, print-process, load, kinematic or hardware validation.",
        ],
        "parts": parts,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(output["summary"], indent=2))
    print(f"Report: {args.output.resolve()}")
    return 0 if output["summary"]["all_checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""Tessellate untouched ROBOTIS STEP assemblies for Blender reference import.

Uses project-local cascadio (OpenCASCADE), chordal tolerance 0.01 mm and
angular tolerance 0.15 radians. STEP originals remain the authoritative geometry.
Run with the bundled Python. This does not launch or modify Blender.
"""
from pathlib import Path
import sys, json, struct

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'converter-runtime'))
import cascadio
import trimesh


def main():
    report = []
    for name in ['AX-12A', 'XM_H-430_idler']:
        source = ROOT / (name + '.stp')
        dest = ROOT / (name + '-official.glb')
        result = cascadio.step_to_glb(
            str(source), str(dest), tol_linear=0.01, tol_angular=0.15,
            tol_relative=False, merge_primitives=True, use_parallel=True,
            include_brep=True, include_materials=True)
        raw = dest.read_bytes()
        json_len, json_type = struct.unpack_from('<II', raw, 12)
        document = json.loads(raw[20:20 + json_len])
        (ROOT / (name + '-gltf-metadata.json')).write_text(
            json.dumps(document, indent=2), encoding='utf-8')
        scene = trimesh.load_scene(dest)
        item = dict(name=name, converter='cascadio ' + cascadio.__version__,
                    source_file=source.name, output_file=dest.name,
                    return_code=result, linear_deflection_mm=0.01,
                    angular_deflection_rad=0.15,
                    glb_scene_bounds=scene.bounds.tolist(),
                    glb_scene_extents=scene.extents.tolist(),
                    meshes=[], nodes=[])
        for key, geom in scene.geometry.items():
            item['meshes'].append(dict(name=key, vertices=len(geom.vertices),
                                       triangles=len(geom.faces),
                                       bounds=geom.bounds.tolist()))
        for key in scene.graph.nodes_geometry:
            matrix, geometry = scene.graph[key]
            item['nodes'].append(dict(name=key, geometry=geometry,
                                     transform=matrix.tolist()))
        report.append(item)
        print(json.dumps(item, indent=2), flush=True)
    (ROOT / 'cad-conversion-report.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

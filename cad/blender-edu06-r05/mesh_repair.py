"""Dimension-preserving cleanup for EDU06 Boolean duplicates.

No voxel remesh, smoothing, vertex relocation, hole filling, or scaling.
The G04 exact Boolean union creates coincident faces with identical geometry
and winding; keep one instance. Tangent features in B01/B05 need source-geometry
overlap/web corrections and are deliberately NOT concealed by this helper.

For STL: triangulate the original local-coordinate mesh BEFORE print rotation.
The B03 face-with-multiple-cutouts is otherwise susceptible to triangulation
artifacts from floating-point noncoplanarity introduced by the 90-degree turn.
"""

import math


def _zero_area_after_stl_grounding(bm):
    """Check the exact float32 coordinates emitted by the existing STL writer.

    Using Python float arithmetic for the cross product matches the independent
    audit; mathutils' single-precision vector cross can mask collinearity.
    This evaluates only, and does not relocate any vertices.
    """
    from mathutils import Vector
    lo=Vector(tuple(min(v.co[i] for v in bm.verts) for i in range(3)))
    hi=Vector(tuple(max(v.co[i] for v in bm.verts) for i in range(3)))
    shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
    count=0
    for face in bm.faces:
        if len(face.verts)!=3:
            raise ValueError('STL preparation retained a non-triangle')
        a,b,c=[tuple(float(x) for x in v.co+shift) for v in face.verts]
        u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        count+=sum(x*x for x in cross)<=1e-20
    return count


def remove_duplicate_faces(bm, coordinate_decimals=6):
    """Delete identical, equally wound face copies; leave coordinates untouched."""
    import bmesh
    bm.normal_update()
    seen={};duplicates=[]
    for face in bm.faces:
        key=tuple(sorted(tuple(round(float(v),coordinate_decimals) for v in vert.co)
                         for vert in face.verts))
        matches=seen.setdefault(key,[])
        if any(face.normal.dot(other.normal) > .999999 for other in matches):
            duplicates.append(face)
        else:
            matches.append(face)
    if duplicates:
        bmesh.ops.delete(bm,geom=duplicates,context='FACES_ONLY')
    return len(duplicates)


def clean_object(o):
    """Remove duplicate faces from a bpy mesh object, preserving local geometry."""
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data)
    before=sum(not e.is_manifold for e in bm.edges)
    removed=remove_duplicate_faces(bm)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    after=sum(not e.is_manifold for e in bm.edges)
    bm.to_mesh(o.data);bm.free();o.data.update()
    return {'part':o.name,'duplicate_faces_removed':removed,
            'nonmanifold_edges_before':before,'nonmanifold_edges_after':after,
            'vertex_relocation_mm':0.0}


def prepare_export_bmesh(o, rotation_degrees=(0,0,0)):
    """Return an owned triangulated BMesh; caller must eventually bm.free()."""
    import bmesh
    from mathutils import Euler
    rotation=Euler(tuple(math.radians(v) for v in rotation_degrees)).to_matrix()
    for method in ('EAR_CLIP','BEAUTY'):
        bm=bmesh.new();bm.from_mesh(o.data)
        remove_duplicate_faces(bm)
        # Work in original coordinate planes, before single-precision rotation.
        bmesh.ops.triangulate(bm,faces=list(bm.faces),ngon_method=method)
        remove_duplicate_faces(bm)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        for vert in bm.verts:
            vert.co=rotation@vert.co
        bm.normal_update()
        # Exact-collinear Boolean intersection vertices can make EAR_CLIP emit
        # zero-area triangles (observed in E_01). Re-tessellating the ORIGINAL
        # faces with BEAUTY changes diagonals only, preserving every vertex and
        # hole. No area threshold or independent audit criterion is relaxed.
        # Concave Boolean n-gons can also acquire a repeated triangulation
        # diagonal (B01). Reject it rather than exporting an invalid mesh.
        bad_surface_edge=any(len(e.link_faces)>0 and not e.is_manifold for e in bm.edges)
        if not bad_surface_edge and not _zero_area_after_stl_grounding(bm):
            return bm
        bm.free()
    raise ValueError(o.name+': both triangulators produced degenerate or nonmanifold STL triangles')

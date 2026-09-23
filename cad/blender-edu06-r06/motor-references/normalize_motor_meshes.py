"""Export official tessellation in the robot model's millimetre horn datum.

No resampling, remeshing, inferred hole creation or geometry reconstruction.
Each node transform from the official assembly is applied to its own vertices.
Then metres become millimetres and the horn mounting face is shifted to Z=0.
Local X=width, +Y=case top, +Z=output direction. JSON gzip needs only Python's
standard library to read inside Blender; faces use zero-based vertex indices.
"""
from pathlib import Path
import gzip, json, sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'converter-runtime'))
import numpy as np
import trimesh


def main():
    summaries=[]
    for kind,name,face_z in [('AX','AX-12A',21.0),('XM','XM_H-430_idler',19.0)]:
        scene=trimesh.load_scene(ROOT/(name+'-official.glb'))
        parts=[]
        for node in scene.graph.nodes_geometry:
            matrix,key=scene.graph[node]
            mesh=scene.geometry[key]
            verts=trimesh.transform_points(mesh.vertices,matrix)*1000
            verts[:,2]-=face_z
            role='fastener'
            if node in ['ASSY_DUMMY___','DUMMY_DC12']:role='case'
            elif 'HORN' in node:role='stock_horn'
            elif node in ['PRT0004','099990987____']:role='connector'
            elif 'CVR_CABLE' in node:role='cable_cover'
            elif 'SPACER' in node:role='spacer'
            parts.append(dict(name=node,source_geometry=key,role=role,
                              vertices=np.round(verts,7).tolist(),
                              faces=mesh.faces.tolist(),
                              bounds_mm=[verts.min(axis=0).tolist(),verts.max(axis=0).tolist()]))
        allverts=np.concatenate([np.asarray(x['vertices']) for x in parts])
        document=dict(kind=kind,source_step=name+'.stp',units='mm',
                      datum='Horn mounting face at Z=0; output +Z; case top +Y; width X',
                      glb_to_this_mesh='Apply node world transform, multiply by 1000, subtract horn_z from Z',
                      glb_horn_front_z_mm=face_z,
                      bounds_mm=[allverts.min(axis=0).tolist(),allverts.max(axis=0).tolist()],
                      tessellation=dict(chord_mm=0.01,angle_rad=0.15),parts=parts)
        outfile=ROOT/(kind+'-official-mm.json.gz')
        with gzip.open(outfile,'wt',encoding='utf-8') as f:json.dump(document,f,separators=(',',':'))
        summary={k:v for k,v in document.items() if k!='parts'}
        summary.update(file=outfile.name,part_count=len(parts),
                       triangle_count=sum(len(p['faces']) for p in parts),
                       parts=[{k:v for k,v in p.items() if k not in ['vertices','faces']} for p in parts])
        summaries.append(summary)
        print(kind,summary['bounds_mm'],summary['triangle_count'],str(outfile))
    (ROOT/'normalized-mesh-summary.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')


if __name__=='__main__':main()

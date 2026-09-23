"""H06 cable-only route through the existing wrist heel access bore.

Connector positions and mechanical geometry are unchanged. Fixed guides reserve
one side of the Ø26 heel bore; the outer loop provides room for ±60° tool roll.
This is a kinematic routing prototype, not a constant-length flex simulation.
"""
import math
import bpy
from mathutils import Matrix


def configure_gripper_route(ports,cases,B):
    from wiring_module import _empty
    source=ports['J5_AX'][1]
    dest=ports['GRIP'][0]
    fork=bpy.data.objects['W02_centred_fixed_pitch_fork']
    # Leave the purchased socket along its actual normal. Then lead through
    # the existing access bore on fixed guides, clear of the moving heel edge.
    source['straight'].location=(0,0,19)
    for anchor,xyz in [(source['far'],(25,0,-5.05)),
                       (source['turn'],(50,0,-5.05))]:
        anchor.parent=fork
        anchor.location=xyz
        anchor.rotation_euler=(0,math.pi/2,0)
    # Route through the palm's 20×10 mm opening and the existing 20 mm open
    # gap; the sideways offset skirts the lower PCD48 spacer post.
    dest['straight'].location=(0,0,14)
    dest['far'].location=(0,0,24)
    dest['turn'].location=(-8,18,40)
    guides = [
        _empty('H06_J5_GRIP / rear exterior sweep',fork,(85,0,-5.05),Matrix.Rotation(math.pi/2,4,'Y')),
        _empty('H06_J5_GRIP / lower exterior sweep',fork,(95,78,-5.05),Matrix.Rotation(math.pi/2,4,'Y')),
        _empty('H06_J5_GRIP / roll exterior sweep',cases['J5_AX'],(65,-170,-25)),
        _empty('H06_J5_GRIP / rotating service sweep',cases['GRIP'],(-12.95,-140,-73.7)),
        _empty('H06_J5_GRIP / palm approach sweep',cases['GRIP'],(-12.95,-80,-73.7)),
    ]

    # Wider layup through the external roll loop prevents insulated strands
    # touching after the spatial curve interpolates the transported frames.
    for guide in guides[2:]:
        guide['bundle_pitch_mm']=2.4
    return guides

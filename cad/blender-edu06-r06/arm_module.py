"""Centred, bilateral R06 link plates. Dimensions in millimetres."""
import math, sys
import bpy
from mathutils import Matrix
import blender_lib as L
from blender_lib import T,R,cube,cyl,poly,hole,hexhole,ring,union,boolean,bolt,nut

def build_arm(B):
    M=B.M
    _,j2,f2=B.reducer('S',B.BASE_ROOT,T(0,0,186)@R('X',90),'J2',5,1.25,B.HOME['J2'],(45,90))
    _,j3,f3=B.reducer('E',j2,T(100,0,0)@R('X',180),'J3',4,1.25,B.HOME['J3'],(30,75))
    ears=[(160,40),(168,12)]
    for side in [-1,1]:
        z=54.5 if side==1 else -60.5
        plate=poly('_upper curved fork',L.hull_circles([(0,0,26),(70,30,15),(160,40,9),(168,12,9)]),z,6,M['green'])
        boolean(plate,poly('_fork lightening',L.hull_circles([(39,9,3),(81,29,5),(142,29,3)]),z-1,8))
        hole(plate,(0,0,z+3),26,9)
        B.holes(plate,B.pcd(4,18,math.pi/4)+ears,z+3,3.4,9)
        p=B.add_part(plate,f'A01_{"left" if side<0 else "right"}_upper_fork',j2,note='Matched 6mm curved side plate; shoulder/elbow pivot centres100mm. Fixed elbow ears beyond gear sweep. No lateral joint offset.')
        p['bilateral_stage']='upper_arm';p['bilateral_side']=side;p['driven_joint']='J2'
        # Stationary elbow posts never cross the rotating flange or gear disk.
        for i,(x,y) in enumerate(ears):
            post=ring('_elbow fork mounting post',5.5,1.7,29.5,25 if side==1 else -54.5,M['green'])
            B.add_part(post,f'A02_{side}_elbow_outer_support_{i}',j2,T(x,y),note='29.5mm support between fixed cheek and outer fork; ear radius exceeds gear tip radius.')
            # Separate readily available45mm bolts enter from the outside of each fork.
            bolt('Elbow bilateral ear M3x45',j2,T(x,y,60.5 if side==1 else -60.5)@(R('X',180) if side==-1 else Matrix.Identity(4)),45,M['steel'])
            nut('Elbow bilateral ear M3 nut',j2,T(x,y,16.6 if side==1 else -19),M['steel'])
    # Root output plates are connected to both ends of the external geared shaft.
    root_fasteners(B,'A01',j2,54.5,f2)

    for side in [-1,1]:
        z=41.5 if side==1 else -47.5
        plate=poly('_rounded forearm side',L.hull_circles([(0,0,26),(58.8,-11,7),(58.8,11,7)]),z,6,M['green'])
        hole(plate,(0,0,z+3),26,9)
        boolean(plate,poly('_forearm lightening',L.rounded_profile(18,15,6,(39,0)),z-1,8))
        B.holes(plate,B.pcd(4,18,math.pi/4)+[(58.8,-11),(58.8,11)],z+3,3.4,9)
        p=B.add_part(plate,f'A03_{"left" if side<0 else "right"}_forearm_fork',j3,note='Matched6mm rounded forearm side plates; both output-shaft ends support the centred wrist crossmember.')
        p['bilateral_stage']='forearm';p['bilateral_side']=side;p['driven_joint']='J3'
        for y in [-11,11]:
            if side==1:
                bolt('Forearm crossmember M3x16',j3,T(58.8,y,47.5),16,M['steel'])
                nut('Forearm crossmember captive M3',j3,T(58.8,y,32.2),M['steel'])
            else:
                bolt('Forearm crossmember M3x16',j3,T(58.8,y,-47.5)@R('X',180),16,M['steel'])
                nut('Forearm crossmember captive M3',j3,T(58.8,y,-34.6),M['steel'])
    root_fasteners(B,'A03',j3,41.5,f3)
    # Separate removable crossmember reaches both plates, unlike an offset flange.
    mount_tf=T(78.8,0,0)@R('Y',90)
    # Construct entirely in wrist-flange coordinates; transform only after Booleans.
    cross=cube('_wrist structural crossmember',(83,36,10),(0,0,-20),M['green'],2)
    end=cyl('_centred fixed wrist flange',30,17,(0,0,-8.5),mat=M['green'])
    union(cross,end);hole(cross,(0,0,-13.5),26,29)
    for x in [-33.4,33.4]:
        for y in [-11,11]:
            hole(cross,(x,y,-20),3.4,23,'X')
            hexhole(cross,(x,y,-20),5.8,2.9,'X')
            boolean(cross,cube('_crossmember nut side entry',(2.9,6.7,12),(x,y,-20)))
    for x,y in B.pcd(4,24):
        hole(cross,(x,y,-7.5),3.4,18)
        hexhole(cross,(x,y,-5.35),5.8,2.9)
        a=math.atan2(y,x)
        cut=cube('_wrist radial nut entry',(20,6.7,2.9),(x+10*math.cos(a),y+10*math.sin(a),-5.35));cut.rotation_euler[2]=a;boolean(cross,cut)
        nut('Centred wrist flange captive M3',j3,mount_tf@T(x,y,-6.8),M['steel'])
    B.add_part(cross,'A05_centred_wrist_crossmember',j3,mount_tf,note='83mm transverse bridge atx53.8..63.8 behind wrist gear sweep; centredØ60neck/flange to frontdatumx78.8. Ø26access,fourM3on48PCD; open radial nut slots.')
    from wrist_module import build_wrist
    j5,grip,pair=build_wrist(j3,mount_tf,B.control,M,B.HOME)
    B.PAIRS.append(pair)
    return j5,grip

def root_fasteners(B,prefix,j,inner,gear_face):
    pts=B.pcd(4,18,math.pi/4)
    if inner>gear_face:
        s=ring('_front torque flange spacer',26,13,inner-gear_face,gear_face,B.M['green'])
        B.holes(s,pts,(inner+gear_face)/2,3.4,inner-gear_face+2)
        B.add_part(s,prefix+'_front_flange_spacer',j,note='Four through-fasteners transmit torque; bore clears central pivot retainer.')
    head=65.6 if prefix=='A01' else 50.6
    length=40 if prefix=='A01' else 25
    for i,(x,y) in enumerate(pts):
        s=ring('_front bolt head spacer',3.5,1.7,head-(inner+6),inner+6,B.M['ivory'])
        B.add_part(s,f'{prefix}_front_bolt_washer_{i}',j,T(x,y))
        bolt(prefix+' front root M3x'+str(length),j,T(x,y,head),length,B.M['steel'])
        bolt(prefix+' rear root M3x12',j,T(x,y,-inner-6)@R('X',180),12,B.M['steel'])
        nut(prefix+' rear root captive M3',j,T(x,y,-inner+3.2),B.M['steel'])

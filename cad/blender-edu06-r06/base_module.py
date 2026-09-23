"""R06 enlarged open service base. All geometry and datums use millimetres.

The internal 3:1 yaw drive is retained from R05; accessory clear space does not
imply a selected controller, power hub, certified cable gland or load rating.
"""
import json, math
from pathlib import Path
from mathutils import Matrix
import blender_lib as L
from blender_lib import T,R,cube,cyl,poly,hole,hexhole,ring,union,boolean,part,reference,empty,bolt,nut
from gear_math import pair_spec
from motor_models import make_motor

def build_base(B):
    for key in ("say","M","control","HOME","PAIRS","FASTENERS","pcd","holes","gear","screw_pattern","add_part","rotating_horn"):
        globals()[key]=getattr(B,key)
    say('Building serviceable base, printed plain bearings and 3:1 yaw drive')
    floor=cube('Base floor',(240,240,5),(0,0,2.5),M['green'],2)
    # Rear and side walls form an open-front case. Separate front panel stays removed in scene.
    for dims,loc in [((4,240,85.5),(-118,0,47.25)),((4,240,85.5),(118,0,47.25)),((240,4,85.5),(0,118,47.25))]:union(floor,cube('_wall',dims,loc,bevel=1))
    lidpts=[(-110,-110),(110,-110),(-110,110),(110,110),(0,110)]
    for x,y in lidpts:
        union(floor,cyl('_lid post',7,85.5,(x,y,47.25)))
        hole(floor,(x,y,86),3.4,14);hexhole(floor,(x,y,86.6),5.8,2.8)
        # Side-loaded nuts retain 2 mm of post material above the pocket.
        # A top-open pocket would let the nut pull against only the lid.
        if x:
            inward=1 if x<0 else -1
            boolean(floor,cube('_lid nut side entry',(10,6.4,2.8),(x+inward*5,y,86.6)))
        else:
            boolean(floor,cube('_lid nut side entry',(6.4,10,2.8),(x,y-5,86.6)))
        nut('Base lid side captive M3',None,T(x,y,85.4),M['steel'])
    for x in [-108,108]:
        for y in [-103,103]:hole(floor,(x,y,2.5),4.5,9)
    motorpts=[(32+x,y) for x in (-21,21) for y in (-42.5,15.5)]
    holes(floor,motorpts,2.5)
    # Lower journal support is bolted to four floor holes; separate printable column.
    lowerpts=[(-28+x,y) for x in (-26,26) for y in (-24,24)]
    holes(floor,lowerpts,2.5)
    for y in [-40,-22,-4,14,32]:boolean(floor,cube('_vent',(8,10,22),(118,y,63),bevel=2))
    # Rear-wall connector access and clamp attachment geometry are added below.
    for x,z,width,height in [(-84,28,26,20),(84,24,22,18)]:
        boolean(floor,cube('_rounded rear cable outlet',(width,14,height),(x,118,z),bevel=4))
    add_part(floor,'B01_open_front_base_240x240',note='4 mm walls, 5 mm floor; four M4 fasteners attach printed feet. External bench attachment must be provided separately. M3 captive nuts in top posts.')
    deck=cube('Deck',(240,240,5),(0,0,92.5),M['green'],2)
    holes(deck,lidpts,92.5);hole(deck,(-28,0,92.5),42.4,12)
    holes(deck,[(-28+x,y) for x,y in pcd(4,36,math.pi/4)],92.5)
    holes(deck,[(32,-15),(32,15)],92.5)
    for x in [62,74,86]:boolean(deck,cube('_vent',(5,42,12),(x,49,92.5),bevel=1))
    add_part(deck,'B02_structural_lid',note='Remove to access drive. Hole Ø42.4 captures upper printed journal bushing.')
    screw_pattern('Base lid M3x12 ',None,T(z=95),lidpts,12)
    front=cube('Front',(230,3,85),(0,0,42.5),M['green'],.8)
    for x in [-103,103]:
        for z in [5,68]:hole(front,(x,0,z),3.4,10,'Y')
    for x in [-55,-40,-25,-10,5,20,35,50]:boolean(front,cube('_vent',(5,12,26),(x,0,39),bevel=.7))
    panel=add_part(front,'B03_service_front_panel',tf=T(0,-152,-6.5)@R('X',90),note='Removable front panel; shown lying in front. Assembly transform: translation(0,-118.5,5) with no rotation.',orient=[90,0,0])
    # Four internal tabs share front panel attachment holes.
    for si,x in enumerate([-103,103]):
        for zi,z in enumerate([10,73]):
            tab=cube('_tab',(22,10,12),(x,-112,z),M['green'],1)
            hole(tab,(x,-112,z),3.4,20,'Y');hexhole(tab,(x,-108.3,z),5.8,2.8,'Y')
            # Support arm reaches fixed side wall without leaving an unconnected island.
            union(tab,cube('_arm',(17,10,12),((-112 if x<0 else 112),-112,z)))
            union(floor,tab)
            bolt('Service panel M3x16',panel,T(x,-1.5,z-5)@R('X',90),16,M['steel'])
            nut('Service tab M3 nut',None,T(x,-107.2,z)@R('X',90),M['steel'])
    L.finish(floor)
    # Lower stand: ring + four columns + foot. No metal bearing.
    stand=ring('_lower stand',27,21.15,8,38,M['green'])
    baseplate=cube('_stand foot',(64,62,5),(0,0,2.5),M['green'],2);hole(baseplate,(0,0,2.5),33,8);union(stand,baseplate)
    pts=[(x,y) for x in [-26,26] for y in [-24,24]]
    for x,y in pts:union(stand,cyl('_post',5,39,(x,y,21.5)))
    # Connect the upper ring to each post using short radial ribs.
    for x,y in pts:union(stand,cube('_rib',(18,17,8),(x*.8,y*.8,42)))
    holes(stand,pts,23)
    hole(stand,(0,0,23),33,50)
    hole(stand,(0,0,42),42.3,8.2)
    add_part(stand,'B05_lower_journal_support',tf=T(-28,0,5),note='Four M3 floor bolts; lower sleeve seat Ø42.3. Printed support carries overturning load.')
    screw_pattern('Lower journal stand M3x55 ',None,T(-28,0,51),pts,55)
    for x,y in pts:nut('Lower journal stand M3nut',None,T(-28+x,y,-2.4),M['steel'])
    lower=ring('_lower sleeve',21,16.25,10,43,M['ivory'])
    union(lower,ring('_flange',26,16.25,2,51,M['ivory']))
    add_part(lower,'B06_replaceable_lower_bushing',tf=T(-28,0,0),note='Ø32.5 running bore for Ø32 shaft. Trial clearance 0.25 radial.')
    upper=ring('_upper sleeve',21,16.25,11,84,M['ivory'])
    union(upper,ring('_thrust flange',45,16.25,3,95,M['ivory']))
    holes(upper,pcd(4,36,math.pi/4),96)
    add_part(upper,'B07_upper_bushing_and_thrust_ring',tf=T(-28,0),note='Replaceable polymer plain bearing, not a ball bearing. Printed thrust surface; friction unmeasured.')
    screw_pattern('Upper bushing M3 ',None,T(-28,0,98),pcd(4,36,math.pi/4),12)
    for x,y in pcd(4,36,math.pi/4):nut('Upper bushing underside M3nut',None,T(-28+x,y,87.6),M['steel'])
    station,j1=L.joint('J1 • base yaw',None,T(-28,0,0),control,'J1',-40,40,HOME['J1'])
    shaft=ring('_shaft',16,7,74,32,M['green'])
    union(shaft,ring('_coupling',31,7,6.5,75,M['green']))
    union(shaft,ring('_thrust collar',32,7,7.7,98.3,M['green']))
    union(shaft,ring('_top flange',38,7,6,106,M['green']))
    holes(shaft,pcd(4,25,math.pi/4),79,3.4,9);holes(shaft,pcd(4,29,math.pi/4),109,3.4,9)
    for x,y in pcd(4,29,math.pi/4):
        # Radial nut entry at Z106.8..109.6 leaves a 2.4 mm load-bearing roof.
        hexhole(shaft,(x,y,108.2),5.8,2.8)
        a=math.atan2(y,x)
        entry=cube('_deck nut radial entry',(12,6.4,2.8),
                   (x+6*math.cos(a),y+6*math.sin(a),108.2))
        entry.rotation_euler[2]=a;boolean(shaft,entry)
    add_part(shaft,'B08_printed_hollow_yaw_shaft',j1,note='Ø32 journal; 14 mm cable bore. Radial gap0.25, axial running allowance0.3. No metal shaft.')
    collar=ring('_yaw clamp',19,16.25,10,32.7,M['green'])
    union(collar,cube('_clamp ears',(12,9,10),(23,0,37.7),M['green']))
    boolean(collar,cube('_split',(16,1,12),(23,0,37.7)))
    hole(collar,(23,0,37.7),3.4,16,'Y');hexhole(collar,(23,3.05,37.7),5.8,3.1,'Y')
    add_part(collar,'B17_split_yaw_retaining_collar',j1,note='Split printed collar under lower sleeve;0.3 axial gap prevents lifting without clamping the bearing.')
    bolt('Yaw collar M3x10',j1,T(23,-4.5,37.7)@R('X',90),10,M['steel'])
    nut('Yaw collar M3nut',j1,T(23,1.7,37.7)@R('X',-90),M['steel'])
    wheel=gear('_yaw60',60,1.5,10,65);hole(wheel,(0,0,70),32.5,14);holes(wheel,pcd(4,25,math.pi/4),70)
    for x,y in pcd(8,36):hole(wheel,(x,y,70),9,14)
    add_part(wheel,'B09_yaw_60T_module1p5',j1,note='60 teeth, pitch Ø90, 20° involute. 60 mm centre distance.')
    for i,(x,y) in enumerate(pcd(4,25,math.pi/4)):
        washer=ring('_yaw gear washer',3.5,1.7,.5,81.5,M['ivory']);add_part(washer,f'B18_yaw_gear_screw_spacer_{i}',j1,T(x,y))
        nut('Yaw gear M3nut',j1,T(x,y,62.6),M['steel'])
    screw_pattern('Yaw gear coupling M3 ',j1,T(z=82),pcd(4,25,math.pi/4),20)
    rotordeck=cube('_rotor deck',(160,108,6),(-23,0,115),M['green'],8)
    hole(rotordeck,(0,0,115),14,10);holes(rotordeck,pcd(4,29,math.pi/4),115)
    footpts=[(x,y) for x in [-76,44] for y in [-20,20]];holes(rotordeck,footpts,115)
    add_part(rotordeck,'B10_rotating_pedestal_deck',j1,note='Structural deck 160×108×6; keyed bolt patterns to yaw flange and shoulder stand.')
    screw_pattern('Deck flange M3x12 ',j1,T(z=118.8),pcd(4,29,math.pi/4),12)
    for i,(x,y) in enumerate(pcd(4,29,math.pi/4)):
        spacer=ring('_deck screw spacer',3.5,1.7,.8,118,M['ivory'])
        add_part(spacer,f'B19_deck_screw_spacer_{i}',j1,T(x,y))
        nut('Deck flange side captive M3',j1,T(x,y,107.0),M['steel'])
    for x,y in footpts:
        bolt('Pedestal to deck M3x25',j1,T(x,y,132),25,M['steel']);nut('Pedestal deck M3nut',j1,T(x,y,109.6),M['steel'])
    motor=make_motor('AX','J1_BASE',None,T(32,0,65),M,attachment_depth=20.05)
    pin=empty('J1 pinion • minus three times yaw',None,T(32,0,65));L.drive(pin,control,'J1','(9-3*q)*pi/180')
    rotating_horn(motor,pin)
    pinion=gear('_pin20',20,1.5,10);holes(pinion,pcd(4,8),5,2.3)
    for x,y in pcd(4,8):hole(pinion,(x,y,8),4.3,8)
    union(pinion,ring('_pinion journal',4,1.7,11,10,M['ivory']))
    hole(pinion,(0,0,.1),6.0,.4)
    add_part(pinion,'B11_yaw_20T_pinion',pin,note='M2×6 through 4 mm counterbore floor into AX horn (2 mm). External printed Ø8 journal support.')
    screw_pattern('J1 horn M2x6 ',pin,T(z=4),pcd(4,8),6,2)
    PAIRS.append({'name':'J1','pinion':pin.name,'wheel':j1.name,**pair_spec(20,60,1.5)})
    # Tall printed pinion journal bracket tied to underside of lid.
    support=ring('_pin support',11,4.25,6,79,M['ivory'])
    for y in [-15,15]:union(support,cube('_ear',(12,10,6),(0,y,82)))
    for y in [-15,15]:union(support,cyl('_leg',4,8,(0,y,86)))
    holes(support,[(0,-15),(0,15)],86)
    add_part(support,'B12_yaw_pinion_journal_support',tf=T(32,0),note='Ø8.5 printed bearing bore; 0.25 mm radial gap. Top ears attach underside deck.')
    for i,y in enumerate([-15,15]):
        washer=ring('_pin support screw spacer',3.5,1.7,1.5,95,M['ivory']);add_part(washer,f'B19_pinion_support_screw_spacer_{i}',tf=T(32,y))
        bolt('Yaw pinion support M3x20',None,T(32,y,96.5),20,M['steel']);nut('Yaw pinion support underside M3nut',None,T(32,y,76.6),M['steel'])
    # Motor floor spacers derive from rear-cap datum, not a guessed motor mounting hole.
    capz=float(motor['rear_cap_back'])+65
    for i,(x,y) in enumerate(motorpts):
        sp=ring('_motor standoff',5,1.7,capz-5,5,M['green']);add_part(sp,f'B13_motor_floor_standoff_{i+1}',tf=T(x,y))
    for i,(x,y) in enumerate([(x,y) for x in [-108,108] for y in [-103,103]]):
        foot=ring('_base foot',12,2.25,8,-8,M['green']);hexhole(foot,(0,0,-6.25),7.3,3.5)
        add_part(foot,f'B15_printed_foot_{i}',tf=T(x,y),note='Printed 8mm foot clears underside motor screw heads; captive M4 nut, no rubber or metal bearing.')
        washer=ring('_anchor stack spacer',5,2.25,3.1,5,M['ivory']);add_part(washer,f'B16_foot_bolt_spacer_{i}',tf=T(x,y))
        bolt('Base foot M4x16',None,T(x,y,8.1),16,M['steel'],4);nut('Base foot M4nut',None,T(x,y,-7.8),M['steel'],4)
    # U2D2 tray — true envelope, separate power entry.
    tray=cube('_tray',(60,30,3),(0,0,1.5),M['green'],2)
    # Low end stops locate the module without blocking USB/TTL plug access.
    for x in [-26,26]:union(tray,cube('_tray low end stop',(3,23,2.4),(x,0,3.8)))
    for y in [-11.5,11.5]:union(tray,cube('_tray rim',(54,3,7),(0,y,5)))
    holes(tray,[(-27,-11),(-27,11),(27,-11),(27,11)],1.5)
    for x,y in [(-27,-11),(-27,11),(27,-11),(27,11)]:
        hole(tray,(x,y,9),6.2,12)
        hole(floor,(-84-y,35+x,2.5),3.4,9)
        bolt('U2D2 tray M3x12',None,T(-84-y,35+x,8),12,M['steel']);nut('U2D2 tray underside M3nut',None,T(-84-y,35+x,-2.4),M['steel'])
    for y in [-16,16]:
        union(tray,cyl('_U2D2 strap post',4.5,15.65,(0,y,10.425),mat=M['green']))
        hole(tray,(0,y,9),3.4,24);hexhole(tray,(0,y,5.6),5.8,2.8)
        boolean(tray,cube('_strap nut side entry',(6.4,8,2.8),(0,y+math.copysign(4,y),5.6)))
        nut('U2D2 strap captive M3nut',None,T(-84,35,5)@R('Z',90)@T(0,y,4.4),M['steel'])
    add_part(tray,'B14_U2D2_tray',tf=T(-84,35,5)@R('Z',90),note='Cavity49×20, U2D2 nominal48×18×14.9. Low end stops and removable roof strap mechanically retain the case. Connector revision must be checked.')
    strap=cube('_U2D2 removable retention strap',(10,41,2.5),(0,0,19.5),M['ivory'],.6)
    for y in [-16,16]:
        hole(strap,(0,y,19.5),3.4,8)
        bolt('U2D2 retention M3x20',None,T(-84,35,5)@R('Z',90)@T(0,y,20.75),20,M['steel'])
    add_part(strap,'B23_U2D2_removable_retention_strap',tf=T(-84,35,5)@R('Z',90),note='0.35mm nominal case-roof clearance; two M3×20 into side-loaded tray nuts. No invented holes in the U2D2 PCB.')
    u=cube('U2D2 USB–TTL converter',(48,18,14.9),(0,0,7.45),M['black'],1.1);reference(u,None,T(-84,35,8)@R('Z',90),mass=9,collision=True)
    L.text('U2D2 marking','U2D2',(-84,35,23.1),4,M['text'])
    _electronics_additions(floor,B)
    return j1


def _slot(obj,x,y,z,length,width,axis='X',depth=8):
    """True capsule slot, with centres separated by length minus width."""
    half=(length-width)/2
    centres=[(x-half,y,width/2),(x+half,y,width/2)] if axis=='X' else [(x,y-half,width/2),(x,y+half,width/2)]
    boolean(obj,poly('_adjustment slot',L.hull_circles(centres),z-depth/2,depth))


def _electronics_additions(floor,B):
    # Full controller-sized clear volume sits ahead of every yaw mechanism.
    # Long slots accept sliding mounting screws after the actual board is known;
    # no Arduino-specific mounting-hole pattern is asserted.
    tray=cube('_accessory slotted tray',(112,68,3),(0,0,1.5),M['green'],1.2)
    mountpts=[(x,y) for x in [-60,60] for y in [-24,24]]
    for x,y in mountpts:
        union(tray,cyl('_tray mounting ear',5,3,(x,y,1.5),mat=M['green']))
        union(tray,cube('_tray ear neck',(9,10,3),(math.copysign(56.5,x),y,1.5),M['green']))
        hole(tray,(x,y,1.5),3.4,8)
        gx,gy=x,y-83
        union(floor,cyl('_accessory floor spacer',5,3.2,(gx,gy,6.4),mat=M['green']))
        hole(floor,(gx,gy,4),3.4,12)
        bolt('Accessory tray M3x16',None,T(gx,gy,11),16,M['steel'])
        nut('Accessory tray underside M3nut',None,T(gx,gy,-2.4),M['steel'])
    for y in [-22,0,22]:
        for x in [-27,27]:_slot(tray,x,y,1.5,32,3.4)
    for y in [-16,16]:_slot(tray,0,y,1.5,17,3.4,'Y')
    add_part(tray,'B20_adjustable_accessory_tray',tf=T(0,-83,8),
             note='112×68×3 mm deck plus mounting ears; 3.4 mm capsule slots. Four removable M3×16 mount screws. Clear accessory envelope100×65×30 above deck; board-hole positions are intentionally not assumed. Select screw length and removable printed standoffs from the actual PCB, keeping underside fasteners above the floor.')

    # Separate universal mounting plate reserves room for a power-injection hub.
    # The hub is not selected, so its only representation is an envelope datum.
    power=cube('_power hub mounting plate',(54,58,3),(0,0,1.5),M['green'],1.2)
    for x,y in [(x,y) for x in [-22,22] for y in [-24,24]]:
        hole(power,(x,y,1.5),3.4,8)
        gx,gy=84+x,60+y
        union(floor,cyl('_power plate floor spacer',5,3.2,(gx,gy,6.4),mat=M['green']))
        hole(floor,(gx,gy,4),3.4,12)
        bolt('Power plate M3x16',None,T(gx,gy,11),16,M['steel'])
        nut('Power plate underside M3nut',None,T(gx,gy,-2.4),M['steel'])
    for y in [-12,0,12]:_slot(power,0,y,1.5,38,3.4)
    add_part(power,'B21_adjustable_power_module_plate',tf=T(84,60,8),
             note='54×58×3 slotted universal plate, four M3×16 mounting screws. Reserved hub envelope45×35×22; actual power distribution hardware and board standoffs remain unselected.')

    # Reusable split printed cable saddles. Their clamp seats are away from the
    # gears and attach through the floor; actual cable diameters must be checked.
    clamps=[]
    for index,(label,x,z,diam,length) in enumerate([('USB',-84,28,5.2,40),('POWER',84,24,6.4,35)]):
        y=98;split=z;capbottom=split+.2;capheight=6
        post=cube('_cable saddle lower',(24,14,split-.2-5),(x,y,(split-.2+5)/2),M['green'],1)
        boolean(post,cyl('_cable saddle groove',diam/2,18,(x,y,z),'Y'))
        union(floor,post)
        cap=cube('_cable saddle upper',(24,14,capheight),(0,0,capbottom+capheight/2),M['ivory'],1)
        boolean(cap,cyl('_cable saddle groove',diam/2,18,(0,0,z),'Y'))
        for sx in [-8.5,8.5]:
            hole(floor,(x+sx,y,split/2),3.4,split+8)
            hole(cap,(sx,0,capbottom+3),3.4,10)
            bolt(label+' cable saddle M3x'+str(length),None,T(x+sx,y,capbottom+capheight),length,M['steel'])
            nut(label+' cable saddle underside M3nut',None,T(x+sx,y,-2.4),M['steel'])
        add_part(cap,'B22_'+label.lower()+'_split_cable_saddle',tf=T(x,y),
                 note=f'Nominal cable bore Ø{diam:g}; 0.4 mm split gap. Two M3×{length} through floor. Fit to actual flexible cable jacket; this is a printable clamp, not a rated gland or connector.')
        clamps.append({'type':label,'centre_mm':[x,y,z],'bore_mm':diam,'split_gap_mm':.4,
                       'screws':'2×M3×'+str(length),'head_z_mm':capbottom+capheight,
                       'tip_z_mm':capbottom+capheight-length})
    L.finish(floor)

    datums={
        'ACCESSORY controller volume':((0,-83,26),(100,65,30),'Reserved unobstructed volume; controller mounting pattern unselected.'),
        'POWER module volume':((84,60,24),(45,35,22),'Reserved generic power-injection hardware volume; not a selected electronic module.'),
        'U2D2 USB service volume':((-84,-4,15.45),(16,30,10),'Provisional plug-removal space along local−X, global−Y; confirm actual cable connector.'),
    }
    for name,(pos,size,note) in datums.items():
        datum=empty(name,None,T(*pos));datum.empty_display_type='CUBE';datum.empty_display_size=1
        datum.scale=tuple(d/2 for d in size);datum['reference_only']=True;datum['service_envelope_mm']=list(size);datum['description']=note
        datum['audit_role']='electronics_keepout';datum['component_name']=name
        datum['reserved_only']=True;datum['collision_check']=False
    for name,pos,direction in [('U2D2 USB connector datum',(-84,11,15.45),[0,-1,0]),
                               ('U2D2 TTL connector datum',(-84,59,15.45),[0,1,0]),
                               ('BASE USB outlet datum',(-84,118,28),[0,1,0]),
                               ('BASE power inlet datum',(84,118,24),[0,-1,0])]:
        datum=empty(name,None,T(*pos));datum['connector_direction']=direction
        datum['reference_only']=True;datum['provisional_connector_datum']=True
    layout={
        'revision':'R06','units':'mm','case_outer_envelope_mm':[241,240,95],
        'nominal_shell_and_lid_envelope_mm':[240,240,95],
        'outer_envelope_note':'Front-panel support arms extend 0.5 mm beyond each nominal X side; measured maximum case width is 241 mm.',
        'fixed_case_bounds_mm':{'x':[-120.5,120.5],'y':[-120,120],'z':[0,95]},
        'feet_bottom_z_mm':-8,'front_panel_installed':{'translation_mm':[0,-118.5,5],'rotation_degrees':[0,0,0]},
        'front_service_opening_mm':{'x':[-92,92],'y':[-120,-117],'z':[5,90]},
        'controller_usable_clear_bounds_mm':{'x':[-50,50],'y':[-115.5,-50.5],'z':[11,41]},
        'controller_tray':{'centre_mm':[0,-83,8],'deck_mm':[112,68,3],'slot_width_mm':3.4,
                           'mount_centres_mm':[[x,y-83] for x,y in mountpts],
                           'board_hole_pattern':'None assumed; use the actual board and suitable printed standoffs.'},
        'controller_connector_service':{'left_bounds_mm':{'x':[-91,-65],'y':[-112,-53],'z':[11,46]},
                                        'right_bounds_mm':{'x':[65,91],'y':[-112,-53],'z':[11,46]},
                                        'front_plug_access':'Remove the front panel for unrestricted forward access; route operating cables to the rear service ports.'},
        'u2d2':{'manufacturer_case_envelope_mm':[48,18,14.9],'case_bottom_centre_mm':[-84,35,8],
                'rotation_z_degrees':90,'usb_datum_mm':[-84,11,15.45],'ttl_datum_mm':[-84,59,15.45],
                'plug_clearance_mm':30,'connector_datums_provisional':True},
        'power_module_reserved_bounds_mm':{'x':[61.5,106.5],'y':[42.5,77.5],'z':[13,35]},
        'rear_ports':[{'name':'USB/data','centre_mm':[-84,118,28],'opening_mm':[26,20],'corner_radius_mm':4},
                      {'name':'power','centre_mm':[84,118,24],'opening_mm':[22,18],'corner_radius_mm':4}],
        'cable_saddles':clamps,
        'fixed_interfaces_unchanged':{'yaw_axis_xy_mm':[-28,0],'yaw_gear_face_z_mm':[65,75],
                                     'lid_z_mm':[90,95],'pedestal_deck_z_mm':[112,118]},
        'print_envelope_note':'Largest case STL is 241×240 mm including front-panel tab arms; lid is 240×240 mm. Check Bambu A1 plate orientation, brim and slicer exclusions.',
        'assembly_note':'Remove lid for drive work. Slide service tray out through open front after removing its four screws. Install electronics, select board standoffs and verify connector removal before securing the front panel. All custom mechanical components are printed; only motors, electronics, screws and nuts are purchased references.'
    }
    (Path(__file__).parent/'base-layout.json').write_text(json.dumps(layout,indent=2),encoding='utf-8')

// All linear geometry is in millimetres. These are design inputs, not measurements.
export const SPEC = Object.freeze({
  revision:'P03', units:'mm', status:'Nominal concept; hardware fit and strength unverified',
  base:{width:180,depth:160,height:32,wall:4,corner:14,mountHole:6.6,mountX:150,mountZ:130},
  shoulderHeight:120,
  upper:{length:180,height:52,depth:62,wall:3,rib:3},
  forearm:{length:150,height:44,depth:46,wall:3,rib:3},
  wrist:{length:52,height:36,depth:34,wall:3,rib:3},
  toolLength:78,gripper:{opening:34,maxOpening:50,palmWidth:72,fingerLength:40,railSpan:84,guideBore:4.3},
  bearing:{id:8,od:22,width:7,seat:22.2,seatDepth:7.2,boss:30},
  fastening:{thread:'M3',clearance:3.4,bossOD:12,bossLength:9,nutAF:5.5,nutThickness:2.4,pocketAF:5.8,pocketDepth:2.8,headDiameter:5.5,headHeight:3},
  motorEnvelope:{base:[42,23,42],shoulder:[40,32,28],elbow:[32,26,24],wrist:[24,20,20]},
  massAssumptionsKg:{upper:.22,forearm:.16,wrist:.09,tool:.10,elbowMotor:.12,wristMotor:.06,payload:.10},
  home:[20,65,-80,-20,0,34],
  joints:[
    {name:'Base',axis:'YAW · Z',min:-160,max:160},
    {name:'Shoulder',axis:'PITCH',min:10,max:145},
    {name:'Elbow',axis:'PITCH',min:-135,max:125},
    {name:'Wrist pitch',axis:'PITCH',min:-100,max:100},
    {name:'Wrist roll',axis:'ROLL',min:-160,max:160}
  ]
});

export function kinematics(angles){
  const r=Math.PI/180,b=angles[0]*r,s=angles[1]*r,e=s+angles[2]*r,w=e+angles[3]*r;
  const p0=[0,0,SPEC.shoulderHeight];
  const advance=(p,length,angle)=>[p[0]+length*Math.cos(angle)*Math.cos(b),p[1]+length*Math.cos(angle)*Math.sin(b),p[2]+length*Math.sin(angle)];
  const p1=advance(p0,SPEC.upper.length,s),p2=advance(p1,SPEC.forearm.length,e),p3=advance(p2,SPEC.wrist.length,w),tip=advance(p3,SPEC.toolLength,w);
  return {points:[p0,p1,p2,p3,tip],angles:[s,e,w]};
}

// Signed static gravity moments. Pitch axes are parallel; yaw and tool-axis roll
// gravity torques are zero under the stated centred, planar mass assumptions.
export function gravityTorques(angles,masses=SPEC.massAssumptionsKg){
  const {points}=kinematics(angles),b=angles[0]*Math.PI/180;
  const centre=(a,c)=>a.map((v,i)=>(v+c[i])/2);
  const loads=[
    {p:centre(points[0],points[1]),m:masses.upper,start:0},
    {p:points[1],m:masses.elbowMotor,start:0},
    {p:centre(points[1],points[2]),m:masses.forearm,start:1},
    {p:points[2],m:masses.wristMotor,start:1},
    {p:centre(points[2],points[3]),m:masses.wrist,start:2},
    {p:centre(points[3],points[4]),m:masses.tool,start:2},
    {p:points[4],m:masses.payload,start:2}
  ];
  return [0,1,2].map(j=>loads.filter(l=>l.start>=j).reduce((sum,l)=>sum+l.m*9.80665*((l.p[0]-points[j][0])*Math.cos(b)+(l.p[1]-points[j][1])*Math.sin(b))/1000,0));
}

export const PARTS=[
  {id:'drives',name:'Servo + stepper hardware',type:'Illustrative purchased hardware',dims:()=>[['Base body width',42],['Base body depth',42],['Base body height',23],['Shoulder servo body length',40],['Servo body height',32],['Servo body depth',28]],note:'Generic casings show laminations, end plates, mounting ears, output horns and connectors. Body dimensions exclude shafts, ears and wires. They do not identify motors compatible with this arm; confirm your actual hardware and transmission.'},
  {id:'base',name:'Base enclosure',type:'Printed plastic',dims:()=>[['Outer width',SPEC.base.width],['Outer depth',SPEC.base.depth],['Height',SPEC.base.height],['Shell wall',SPEC.base.wall],['Anchor holes Ø',SPEC.base.mountHole]],note:'Four through-holes on a 150 × 130 mm pattern. Anchor loads and the base drive interface need verification.'},
  {id:'shoulder',name:'Shoulder bearing support',type:'Printed plastic + hardware',dims:()=>[['Pivot height',SPEC.shoulderHeight],['Bearing ID / shaft Ø',8],['Bearing OD',22],['Bearing width',7],['Trial seat Ø',22.2],['Seat depth',7.2]],note:'Two bearing seats support an 8 mm shaft. The 0.2 mm diametral allowance is a fit-trial value, not a production tolerance.'},
  {id:'upper',name:'Upper-arm split shell',type:'Printed plastic',dims:()=>[['Pivot spacing',SPEC.upper.length],['Overall length',SPEC.upper.length+SPEC.upper.height],['Section height',SPEC.upper.height],['Section depth',SPEC.upper.depth],['Cover / wall',SPEC.upper.wall],['Cross ribs',SPEC.upper.rib]],note:'Deep box section with removable side covers. Internal ribs join the shell walls; screw bosses clamp the covers.'},
  {id:'forearm',name:'Forearm split shell',type:'Printed plastic',dims:()=>[['Pivot spacing',SPEC.forearm.length],['Overall length',SPEC.forearm.length+SPEC.forearm.height],['Section height',SPEC.forearm.height],['Section depth',SPEC.forearm.depth],['Cover / wall',SPEC.forearm.wall],['Cross ribs',SPEC.forearm.rib]],note:'A smaller section reduces distal mass. Print orientation, wall count and creep must be checked for the chosen filament.'},
  {id:'wrist',name:'Pitch fork & roll module',type:'Printed plastic + hardware',dims:()=>[['Pitch to roll axis',SPEC.wrist.length],['Pitch module width',SPEC.wrist.depth],['Roll-to-tool centre',SPEC.toolLength],['Shaft Ø',8],['Bearing seat Ø',22.2]],note:'J4 tilts the wrist; J5 rotates the tool about its length. Motor envelopes illustrate space reservations, not selected products.'},
  {id:'gripper',name:'Parallel gripper',type:'Printed plastic + hardware',dims:()=>[['Palm span',SPEC.gripper.palmWidth],['Finger length',SPEC.gripper.fingerLength],['Maximum clear gap',SPEC.gripper.maxOpening],['Guide rod Ø',4],['Guide rod span',SPEC.gripper.railSpan],['Trial guide bore Ø',SPEC.gripper.guideBore]],note:'Two symmetric sliding fingers with actual guide bores and separate contact pads. Sliding fit, actuation and retention mechanisms still require development.'},
  {id:'fastener',name:'Printed captive-nut boss',type:'Printed pocket + M3 hardware',dims:()=>[['Bolt clearance Ø',SPEC.fastening.clearance],['Printed boss Ø',SPEC.fastening.bossOD],['Boss length',SPEC.fastening.bossLength],['Nut pocket across flats',SPEC.fastening.pocketAF],['Pocket depth',SPEC.fastening.pocketDepth],['Reference nut across flats',SPEC.fastening.nutAF]],note:'A real hexagonal pocket retains a standard metal M3 nut. The boss and seat are plastic; the bolt and nut are purchased hardware.'}
];

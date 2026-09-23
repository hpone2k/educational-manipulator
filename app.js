import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';

const $ = id => document.getElementById(id);
const viewport = $('viewport');
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const specs = [
  {name:'Base',min:-180,max:180,axis:'YAW',description:'Turns the entire arm around the vertical axis. The shoulder, elbow and wrist rotate together.'},
  {name:'Shoulder',min:10,max:150,axis:'PITCH',description:'Raises the upper arm. Every joint farther along the arm moves with it.'},
  {name:'Elbow',min:-140,max:140,axis:'PITCH',description:'Bends the forearm relative to the upper arm, changing the reach of the tool.'},
  {name:'Wrist pitch',min:-110,max:110,axis:'PITCH',description:'Tilts the gripper relative to the forearm to change its approach angle.'},
  {name:'Wrist roll',min:-180,max:180,axis:'ROLL',description:'Rotates the gripper around the tool axis. Its centre stays in the same position.'}
];
const poses = {home:[25,65,-80,-20,15,34],reach:[5,35,-30,-5,0,48],fold:[-15,115,-130,20,65,12]};
const angles = [...poses.home];
const rows=[],sliders=[],numbers=[],labelButtons=[],leaderLines=[],dots=[];
let selected=1, labelsVisible=true, axesVisible=false, motion=null, demoPlaying=false;
let scene, camera, renderer, orbit, robot, joints=[],tip,fingers=[],highlightRings=[],axesHelpers=[];
let width=0,height=0,lastTime=0,lastReadout=0,needRender=true,cameraMotion=null;
const DEG=Math.PI/180;
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const svgNS='http://www.w3.org/2000/svg';

specs.forEach((spec,i)=>{
  const row=document.createElement('div');row.className='joint-row';row.dataset.joint=i;
  row.innerHTML=`<div class="joint-heading"><button class="joint-select" type="button" aria-label="Select joint ${i+1}, ${spec.name}" aria-pressed="${i===selected}"><span class="joint-index">J${i+1}</span>${spec.name}</button><div class="angle-field"><input type="number" min="${spec.min}" max="${spec.max}" step="1" value="${angles[i]}" aria-label="${spec.name} angle in degrees"><span>°</span></div></div><input type="range" min="${spec.min}" max="${spec.max}" step="1" value="${angles[i]}" aria-label="${spec.name} angle"><div class="range-labels"><span>${spec.min}°</span><span>${spec.max}°</span></div>`;
  $('joint-controls').append(row);rows.push(row);
  const slider=row.querySelector('input[type=range]'),number=row.querySelector('input[type=number]');sliders.push(slider);numbers.push(number);
  row.querySelector('button').addEventListener('click',()=>select(i));
  slider.addEventListener('input',()=>{cancelMotion();select(i);angles[i]=Number(slider.value);applyPose();});
  number.addEventListener('change',()=>{cancelMotion();select(i);const value=number.value===''?angles[i]:Number(number.value);angles[i]=clamp(Number.isFinite(value)?value:angles[i],spec.min,spec.max);applyPose();number.value=Math.round(angles[i]);announce();});
  slider.addEventListener('change',announce);
  const label=document.createElement('button');label.className='joint-label';label.type='button';label.setAttribute('aria-label',`Select J${i+1}, ${spec.name}`);label.innerHTML=`<span class="label-id">J${i+1}</span><span>${spec.name}</span><span class="label-angle"></span>`;label.addEventListener('click',()=>select(i));$('joint-labels').append(label);labelButtons.push(label);
  const line=document.createElementNS(svgNS,'line'),dot=document.createElementNS(svgNS,'circle');dot.setAttribute('r','3.5');$('leaders').append(line,dot);leaderLines.push(line);dots.push(dot);
});

function select(i){
  selected=i;rows.forEach((row,j)=>{row.classList.toggle('active',j===i);row.querySelector('button').setAttribute('aria-pressed',String(j===i));});
  labelButtons.forEach((button,j)=>{button.classList.toggle('selected',j===i);button.setAttribute('aria-pressed',String(j===i));leaderLines[j].classList.toggle('selected-line',j===i);});
  highlightRings.forEach((ring,j)=>{ring.material.emissiveIntensity=j===i?1.3:.15;ring.material.color.set(j===i?0xa1f4d1:0x559b84);});
  $('selected-id').textContent=`J${i+1}`;$('selected-title').textContent=specs[i].name;$('selected-description').textContent=specs[i].description;$('selected-axis').textContent=specs[i].axis;needRender=true;
}

function progress(input,value){input.style.setProperty('--progress',`${(value-Number(input.min))/(Number(input.max)-Number(input.min))*100}%`);}
function applyPose(){
  if(joints.length){joints[0].rotation.y=angles[0]*DEG;joints[1].rotation.z=angles[1]*DEG;joints[2].rotation.z=angles[2]*DEG;joints[3].rotation.z=angles[3]*DEG;joints[4].rotation.x=angles[4]*DEG;fingers.forEach((finger,i)=>finger.position.z=(i===0?1:-1)*(angles[5]/2+5));robot.updateMatrixWorld(true);}
  specs.forEach((_,i)=>{sliders[i].value=angles[i];if(document.activeElement!==numbers[i])numbers[i].value=Math.round(angles[i]);progress(sliders[i],angles[i]);labelButtons[i].querySelector('.label-angle').textContent=Math.round(angles[i])+'°';});
  $('gripper').value=angles[5];if(document.activeElement!==$('gripper-value'))$('gripper-value').value=Math.round(angles[5]);progress($('gripper'),angles[5]);needRender=true;
}
function readPosition(){const p=new THREE.Vector3();tip.getWorldPosition(p);return [p.x,-p.z,p.y];}
function announce(){if(!tip)return;const p=readPosition();$('a11y-status').textContent=`${specs[selected].name}: ${Math.round(angles[selected])} degrees. Tool position X ${p[0].toFixed(1)}, Y ${p[1].toFixed(1)}, Z ${p[2].toFixed(1)} millimetres.`;}

function roundedRect(path,x,y,w,h,r){path.moveTo(x+r,y);path.lineTo(x+w-r,y);path.quadraticCurveTo(x+w,y,x+w,y+r);path.lineTo(x+w,y+h-r);path.quadraticCurveTo(x+w,y+h,x+w-r,y+h);path.lineTo(x+r,y+h);path.quadraticCurveTo(x,y+h,x,y+h-r);path.lineTo(x,y+r);path.quadraticCurveTo(x,y,x+r,y);}
function setupScene(){
  renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.35;viewport.prepend(renderer.domElement);renderer.domElement.setAttribute('aria-label','Three-dimensional five-joint robot arm. Use the joint controls to move it.');renderer.domElement.setAttribute('role','img');
  scene=new THREE.Scene();scene.fog=new THREE.Fog(0x1a2426,1000,2100);
  camera=new THREE.PerspectiveCamera(36,1,1,4000);camera.position.set(630,430,760);
  orbit=new OrbitControls(camera,renderer.domElement);orbit.target.set(110,150,0);orbit.enableDamping=true;orbit.dampingFactor=.085;orbit.minDistance=320;orbit.maxDistance=1700;orbit.maxPolarAngle=Math.PI*.49;orbit.addEventListener('change',()=>needRender=true);orbit.addEventListener('start',()=>{cameraMotion=null;$('camera-name').textContent='Custom view';document.querySelectorAll('[data-view]').forEach(b=>{b.classList.remove('selected');b.setAttribute('aria-pressed','false');});});
  scene.add(new THREE.HemisphereLight(0xe1fff5,0x52625b,2.5));
  const key=new THREE.DirectionalLight(0xfff5e8,4);key.position.set(200,650,350);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-600,right:600,top:600,bottom:-600,near:10,far:1500});key.shadow.bias=-.0003;key.shadow.normalBias=1.5;key.shadow.radius=4;scene.add(key);
  const rim=new THREE.DirectionalLight(0x93dccc,2.8);rim.position.set(-350,400,-300);scene.add(rim);const fill=new THREE.DirectionalLight(0xe2efff,1.6);fill.position.set(500,200,-500);scene.add(fill);
  const envScene=new THREE.Scene();envScene.background=new THREE.Color(0x62726f);[[0,400,0,500,500],[-400,100,0,300,700],[400,200,-200,450,600]].forEach(([x,y,z,w,h])=>{const panel=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:0xffffff,side:THREE.DoubleSide}));panel.position.set(x,y,z);panel.lookAt(0,0,0);envScene.add(panel);});
  const pmrem=new THREE.PMREMGenerator(renderer);const environment=pmrem.fromScene(envScene,.08);scene.environment=environment.texture;pmrem.dispose();envScene.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
  const material=(color,metalness=.5,roughness=.3)=>new THREE.MeshStandardMaterial({color,metalness,roughness});
  const white=material(0xc5d1c9,.72,.27),edge=material(0xeff3e8,.55,.3),dark=material(0x222f30,.65,.28),black=material(0x0e181b,.2,.6),steel=material(0x94a7a5,.88,.2),mint=material(0x78d5b0,.65,.24);
  function mesh(parent,geo,mat,pos=[0,0,0]){const m=new THREE.Mesh(geo,mat);m.position.set(...pos);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;}
  function box(parent,w,h,d,mat,pos=[0,0,0],bevel=2){const shape=new THREE.Shape();roundedRect(shape,-w/2,-h/2,w,h,Math.min(4,w/4,h/4));const geo=new THREE.ExtrudeGeometry(shape,{depth:d,bevelEnabled:bevel>0,bevelSegments:2,steps:1,bevelSize:bevel,bevelThickness:bevel,curveSegments:5});geo.translate(0,0,-d/2);return mesh(parent,geo,mat,pos);}
  function cylinder(parent,r,length,mat,pos=[0,0,0],axis='z'){const m=mesh(parent,new THREE.CylinderGeometry(r,r,length,48),mat,pos);if(axis==='z')m.rotation.x=Math.PI/2;if(axis==='x')m.rotation.z=Math.PI/2;return m;}
  function bolt(parent,pos,axis='z',size=2.3){const b=cylinder(parent,size,2.5,steel,pos,axis);const slot=mesh(b,new THREE.BoxGeometry(size*1.05,.5,.6),black,[0,1.4,0]);return b;}
  function ring(parent,r,tube,pos,axis='z',mat=mint){const m=mesh(parent,new THREE.TorusGeometry(r,tube,10,72),mat,pos);if(axis==='y')m.rotation.x=Math.PI/2;if(axis==='x')m.rotation.y=Math.PI/2;return m;}
  function motor(parent,r,depth,index,axis='z'){
    const group=new THREE.Group();if(axis==='x')group.rotation.y=Math.PI/2;parent.add(group);
    cylinder(group,r,depth,dark);cylinder(group,r*.92,depth+2,black);[-1,1].forEach(sign=>{cylinder(group,r*.92,5,white,[0,0,sign*(depth/2+2)]);cylinder(group,r*.72,6,dark,[0,0,sign*(depth/2+5)]);cylinder(group,r*.46,7,steel,[0,0,sign*(depth/2+7)]);for(let k=0;k<6;k++){const t=k*Math.PI/3;bolt(group,[Math.cos(t)*r*.79,Math.sin(t)*r*.79,sign*(depth/2+6)]);}});
    const highlight=mint.clone();highlight.emissive=new THREE.Color(0x61d6ab);highlight.emissiveIntensity=.15;highlightRings[index]=ring(group,r*.60,1.5,[0,0,depth/2+9],'z',highlight);
    group.userData.joint=index;return group;
  }
  function link(parent,length,width,depth){
    [-1,1].forEach(sign=>{const shape=new THREE.Shape();roundedRect(shape,11,-width/2,length-22,width,10);const hole=new THREE.Path();roundedRect(hole,36,-width*.19,length-72,width*.38,5);shape.holes.push(hole);const geo=new THREE.ExtrudeGeometry(shape,{depth:5,bevelEnabled:true,bevelThickness:1,bevelSize:1,bevelSegments:2,curveSegments:10});geo.translate(0,0,-2.5);mesh(parent,geo,white,[0,0,sign*depth/2]);[25,length-25].forEach(x=>bolt(parent,[x,0,sign*(depth/2+4)]));});
    [-1,1].forEach(sign=>{cylinder(parent,3.5,length-45,dark,[length/2,sign*width*.3,0],'x');box(parent,length-65,5,depth-5,black,[length/2,sign*width*.33,0],1);});
    box(parent,length*.44,2,depth+3,mint,[length*.5,width/2+1,0],.5);
  }
  const floor=mesh(scene,new THREE.PlaneGeometry(10000,10000),material(0x101918,.15,.9),[0,-2,0]);floor.rotation.x=-Math.PI/2;floor.castShadow=false;
  const grid=new THREE.GridHelper(1300,26,0x4d655d,0x344942);grid.position.y=-.9;grid.material.transparent=true;grid.material.opacity=.43;scene.add(grid);
  [250,400].forEach(r=>{const geo=new THREE.RingGeometry(r-.6,r+.6,128);const m=mesh(scene,geo,new THREE.MeshBasicMaterial({color:0x53756a,transparent:true,opacity:.24,side:THREE.DoubleSide}),[0,-.5,0]);m.rotation.x=-Math.PI/2;m.castShadow=false;});
  robot=new THREE.Group();scene.add(robot);
  cylinder(robot,108,12,dark,[0,6,0],'y');cylinder(robot,102,3,steel,[0,13,0],'y');cylinder(robot,96,3,black,[0,16,0],'y');ring(robot,100,1.1,[0,15.5,0],'y');
  for(let i=0;i<8;i++){const t=i*Math.PI/4;bolt(robot,[86*Math.cos(t),18,86*Math.sin(t)],'y',3);}
  const base=new THREE.Group();base.position.y=19;robot.add(base);joints.push(base);base.userData.joint=0;
  cylinder(base,52,33,white,[0,17,0],'y');cylinder(base,53,5,dark,[0,33,0],'y');const baseHighlight=mint.clone();baseHighlight.emissive=new THREE.Color(0x61d6ab);baseHighlight.emissiveIntensity=.15;highlightRings[0]=ring(base,53,1.8,[0,35,0],'y',baseHighlight);cylinder(base,43,13,dark,[0,41,0],'y');
  [-1,1].forEach(sign=>box(base,44,41,12,edge,[0,52,sign*30]));
  const shoulder=new THREE.Group();shoulder.position.y=71;base.add(shoulder);joints.push(shoulder);shoulder.userData.joint=1;motor(shoulder,30,75,1);link(shoulder,180,43,37);
  const elbow=new THREE.Group();elbow.position.x=180;shoulder.add(elbow);joints.push(elbow);elbow.userData.joint=2;motor(elbow,25,57,2);link(elbow,150,35,29);
  const wrist=new THREE.Group();wrist.position.x=150;elbow.add(wrist);joints.push(wrist);wrist.userData.joint=3;motor(wrist,20,45,3);box(wrist,41,23,25,white,[29,0,0]);
  const roll=new THREE.Group();roll.position.x=52;wrist.add(roll);joints.push(roll);roll.userData.joint=4;motor(roll,17,21,4,'x');
  cylinder(roll,14,12,steel,[16,0,0],'x');box(roll,17,26,77,dark,[26,0,0]);box(roll,5,23,73,white,[36,0,0]);cylinder(roll,2.5,67,steel,[38,0,0],'z');
  [1,-1].forEach(sign=>{const finger=new THREE.Group();finger.position.x=38;roll.add(finger);box(finger,28,17,8,white,[12,0,0]);box(finger,12,17,10,dark,[30,0,0]);for(let j=0;j<4;j++)box(finger,1.5,15,1,black,[26+j*2,0,-sign*5.5],0);bolt(finger,[3,10,0],'y',2);fingers.push(finger);});
  tip=new THREE.Object3D();tip.position.x=73;roll.add(tip);
  const tipMarker=new THREE.Mesh(new THREE.SphereGeometry(2,12,12),new THREE.MeshBasicMaterial({color:0x8feac6}));tip.add(tipMarker);
  // Robotics coordinates: X = scene X, Y = -scene Z, Z = scene Y.
  const worldAxes=new THREE.Group();scene.add(worldAxes);[[new THREE.Vector3(1,0,0),0xe29d87],[new THREE.Vector3(0,0,-1),0x9cd0ab],[new THREE.Vector3(0,1,0),0x98bfe3]].forEach(([direction,c])=>worldAxes.add(new THREE.ArrowHelper(direction,new THREE.Vector3(0,20,0),145,c,10,5)));worldAxes.visible=false;axesHelpers.push(worldAxes);
  joints.forEach((joint,i)=>{const direction=i===0?new THREE.Vector3(0,1,0):i===4?new THREE.Vector3(1,0,0):new THREE.Vector3(0,0,1);const axis=new THREE.ArrowHelper(direction,new THREE.Vector3(),60,0xb8efce,8,4);joint.add(axis);axis.visible=false;axesHelpers.push(axis);});
  renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();$('loading').hidden=false;$('loading').textContent='The 3D view was interrupted. Reload this page to restore it.';});
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let pointerDown=null;
  renderer.domElement.addEventListener('pointerdown',e=>pointerDown=[e.clientX,e.clientY]);
  renderer.domElement.addEventListener('pointerup',e=>{if(!pointerDown||Math.hypot(e.clientX-pointerDown[0],e.clientY-pointerDown[1])>5)return;const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObject(robot,true)[0];let object=hit?.object;while(object){if(object.userData.joint!==undefined){select(object.userData.joint);return;}object=object.parent;}});
  applyPose();select(selected);new ResizeObserver(resize).observe(viewport);resize();$('loading').hidden=true;
  // Read-only state makes coordinate conventions and model behavior inspectable.
  window.robotStudio={getState:()=>({angles:[...angles],tool:readPosition(),selected,playing:demoPlaying,labels:labelsVisible,camera:camera.position.toArray(),dimensions:{shoulderHeight:90,upperArm:180,forearm:150,wrist:52,tool:73}})};
  requestAnimationFrame(tick);
}

function resize(){const changed=width!==viewport.clientWidth||height!==viewport.clientHeight;width=viewport.clientWidth;height=viewport.clientHeight;if(!width||!height)return;renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();if(changed){const fitted=fitCamera(camera.position.clone().sub(orbit.target).normalize());camera.position.copy(fitted.position);orbit.target.copy(fitted.center);cameraMotion=null;}needRender=true;}
function placeLabels(){
  if(!labelsVisible)return;const points=joints.map((joint,i)=>{const world=new THREE.Vector3();joint.getWorldPosition(world);if(i===0)world.y=45;world.project(camera);return {i,x:(world.x*.5+.5)*width,y:(-.5*world.y+.5)*height,visible:world.z>=-1&&world.z<=1};});
  const small=width<520;const margin=small?10:20;const top=small?113:92;const bottom=height-73;
  // Separate callouts into two columns, then resolve vertical overlap in each column.
  [[0,1,2],[3,4]].forEach((ids,side)=>{const group=ids.map(i=>points[i]).sort((a,b)=>a.y-b.y);let previous=top-42;group.forEach(p=>{p.ly=clamp(p.y-15,top,bottom);p.ly=Math.max(p.ly,previous+42);previous=p.ly;});const overflow=group.at(-1).ly-bottom;if(overflow>0)group.forEach(p=>p.ly-=overflow);group.forEach(p=>{const button=labelButtons[p.i];const labelWidth=button.offsetWidth||120;const left=side===0?margin:width-margin-labelWidth;button.style.left=left+'px';button.style.top=p.ly+'px';button.style.visibility=p.visible?'visible':'hidden';const x2=side===0?left+labelWidth:left;const y2=p.ly+button.offsetHeight/2;const line=leaderLines[p.i];line.setAttribute('x1',p.x);line.setAttribute('y1',p.y);line.setAttribute('x2',x2);line.setAttribute('y2',y2);line.style.visibility=p.visible?'visible':'hidden';dots[p.i].setAttribute('cx',p.x);dots[p.i].setAttribute('cy',p.y);dots[p.i].style.visibility=p.visible?'visible':'hidden';});});
}

function cancelMotion(){motion=null;demoPlaying=false;$('demo-text').textContent='Play demonstration';$('play-symbol').textContent='▶';$('motion-state').textContent='Manual';$('demo-progress').style.width='0%';$('app-status').textContent='Local simulation · ready to explore';}
function movePose(pose){cancelMotion();if(reducedMotion){angles.splice(0,6,...pose);applyPose();announce();return;}motion={start:performance.now(),duration:1000,from:[...angles],to:[...pose]};$('motion-state').textContent='Moving';}
document.querySelectorAll('[data-pose]').forEach(button=>button.addEventListener('click',()=>movePose(poses[button.dataset.pose])));
$('demo').addEventListener('click',()=>{if(demoPlaying){cancelMotion();announce();return;}cancelMotion();demoPlaying=true;motion={start:performance.now(),duration:12000,keyframes:[[...angles],poses.reach,[55,75,-85,-25,110,8],poses.fold,[...angles]]};$('demo-text').textContent='Stop demonstration';$('play-symbol').textContent='■';$('motion-state').textContent='Demo';$('app-status').textContent='Demonstration running · 12-second sequence';});
function setGripper(value){cancelMotion();angles[5]=clamp(Number.isFinite(value)?value:angles[5],0,60);applyPose();}
$('gripper').addEventListener('input',e=>setGripper(Number(e.target.value)));
$('gripper-value').addEventListener('change',e=>{setGripper(e.target.value===''?angles[5]:Number(e.target.value));e.target.value=Math.round(angles[5]);});
$('toggle-labels').addEventListener('click',()=>{labelsVisible=!labelsVisible;$('toggle-labels').setAttribute('aria-pressed',String(labelsVisible));$('toggle-labels').classList.toggle('active',labelsVisible);$('joint-labels').hidden=!labelsVisible;$('leaders').style.display=labelsVisible?'':'none';needRender=true;});
$('toggle-axes').addEventListener('click',()=>{axesVisible=!axesVisible;$('toggle-axes').setAttribute('aria-pressed',String(axesVisible));$('toggle-axes').classList.toggle('active',axesVisible);axesHelpers.forEach(axis=>axis.visible=axesVisible);needRender=true;});

function fitCamera(direction){
  robot.updateMatrixWorld(true);const bounds=new THREE.Box3(),corners=[];robot.traverse(object=>{if(object.isMesh){object.geometry.computeBoundingBox();const b=object.geometry.boundingBox;for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){const p=new THREE.Vector3(x,y,z).applyMatrix4(object.matrixWorld);bounds.expandByPoint(p);corners.push(p);}}});
  const center=bounds.getCenter(new THREE.Vector3()),right=new THREE.Vector3().crossVectors(new THREE.Vector3(0,1,0),direction).normalize(),up=new THREE.Vector3().crossVectors(direction,right).normalize();
  const tanV=Math.tan(camera.fov*DEG/2),tanH=tanV*camera.aspect;let distance=320;
  for(const corner of corners){const p=corner.sub(center);distance=Math.max(distance,Math.abs(p.dot(right))/tanH*1.3+p.dot(direction),Math.abs(p.dot(up))/tanV*1.36+p.dot(direction));}
  return {center,position:center.clone().addScaledVector(direction,distance)};
}
function view(name){if(!camera)return;const directions={perspective:[.68,.46,1],front:[0,.12,1],side:[1,.12,0],top:[0,1,.001]};const {center,position:destination}=fitCamera(new THREE.Vector3(...directions[name]).normalize());cameraMotion={start:performance.now(),from:camera.position.clone(),to:destination,fromTarget:orbit.target.clone(),toTarget:center};if(reducedMotion){camera.position.copy(destination);orbit.target.copy(center);cameraMotion=null;needRender=true;}document.querySelectorAll('[data-view]').forEach(button=>{const active=button.dataset.view===name;button.classList.toggle('selected',active);button.setAttribute('aria-pressed',String(active));});$('camera-name').textContent=name.charAt(0).toUpperCase()+name.slice(1);}
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>view(button.dataset.view)));
$('fit-view').addEventListener('click',()=>view('perspective'));
document.addEventListener('keydown',event=>{if(event.key==='Escape'){cancelMotion();announce();}});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&demoPlaying)cancelMotion();});

function tick(time){
  requestAnimationFrame(tick);if(document.hidden)return;
  if(cameraMotion){const t=clamp((time-cameraMotion.start)/650,0,1),s=t*t*(3-2*t);camera.position.lerpVectors(cameraMotion.from,cameraMotion.to,s);orbit.target.lerpVectors(cameraMotion.fromTarget,cameraMotion.toTarget,s);needRender=true;if(t===1)cameraMotion=null;}
  if(motion){const t=clamp((time-motion.start)/motion.duration,0,1);let from,to,s;
    if(motion.keyframes){const scaled=t*(motion.keyframes.length-1),index=Math.min(Math.floor(scaled),motion.keyframes.length-2);from=motion.keyframes[index];to=motion.keyframes[index+1];s=scaled-index;$('demo-progress').style.width=`${t*100}%`;}else{from=motion.from;to=motion.to;s=t;}
    s=s*s*(3-2*s);angles.forEach((_,i)=>angles[i]=from[i]+(to[i]-from[i])*s);applyPose();if(t===1){cancelMotion();announce();}
  }
  orbit.update();if(needRender){renderer.render(scene,camera);placeLabels();if(time-lastReadout>60||!motion){const position=readPosition();['pos-x','pos-y','pos-z'].forEach((id,i)=>$(id).textContent=(Math.abs(position[i])<.05?0:position[i]).toFixed(1));lastReadout=time;}needRender=false;}lastTime=time;
}

try{setupScene();}catch(error){console.error(error);$('loading').hidden=false;$('loading').textContent='The 3D renderer could not start. Open this page in a browser with WebGL 2 enabled, then reload.';$('app-status').textContent='3D renderer unavailable';}

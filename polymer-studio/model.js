import * as THREE from 'three';
import {SPEC} from './spec.js';

export function buildModel(scene){
  const root=new THREE.Group(),detail=new THREE.Group();scene.add(root,detail);detail.visible=false;detail.position.y=30;
  const parts={},joints=[],covers=[],skins=[],ribs=[],hardware=[],motors=[],pickable=[],edgeLines=[],serviceLoops=[];
  const material=(color,metalness=0,roughness=.5)=>new THREE.MeshStandardMaterial({color,metalness,roughness});
  const mats={cream:material(0xe2e2d4,0,.29),mint:material(0x80b3a2,0,.32),graphite:material(0x242e2d,0,.32),rib:material(0x63a885,0,.51),steel:material(0xc3ced0,.88,.23),bearing:material(0x687778,.7,.25),black:material(0x101818,0,.68),motor:material(0x303738,.7,.32),copper:material(0xb98856,.65,.32),panel:material(0xc9cdbf,0,.4),gasket:material(0x172221,0,.78),alloy:material(0x909a9d,.86,.31),wireRed:material(0x9c4a38,0,.5),wireGold:material(0xc6994c,0,.5),wireWhite:material(0xd2d5c5,0,.5)};
  // Fine, deterministic surface grain. All textures are generated locally.
  const grainCanvas=document.createElement('canvas');grainCanvas.width=grainCanvas.height=128;const gc=grainCanvas.getContext('2d'),grain=gc.createImageData(128,128);let seed=17;
  for(let i=0;i<grain.data.length;i+=4){seed=(seed*1664525+1013904223)>>>0;const n=120+(seed%28);grain.data.set([n,n,n,255],i);}gc.putImageData(grain,0,0);
  const grainMap=new THREE.CanvasTexture(grainCanvas);grainMap.wrapS=grainMap.wrapT=THREE.RepeatWrapping;grainMap.repeat.set(.65,.65);
  for(const m of [mats.cream,mats.mint,mats.panel]){m.bumpMap=grainMap;m.bumpScale=.035;}
  const braidCanvas=document.createElement('canvas');braidCanvas.width=braidCanvas.height=128;const bc=braidCanvas.getContext('2d');bc.fillStyle='#111816';bc.fillRect(0,0,128,128);
  for(let k=-8;k<16;k++){bc.lineWidth=7;bc.strokeStyle=k%2?'#39433f':'#242e29';bc.beginPath();bc.moveTo(k*16,0);bc.lineTo(k*16+128,128);bc.stroke();bc.lineWidth=3;bc.strokeStyle='#4e5751';bc.beginPath();bc.moveTo(k*16,0);bc.lineTo(k*16-128,128);bc.stroke();}
  const braidMap=new THREE.CanvasTexture(braidCanvas);braidMap.wrapS=braidMap.wrapT=THREE.RepeatWrapping;braidMap.colorSpace=THREE.SRGBColorSpace;braidMap.anisotropy=4;
  function group(parent,name,pos=[0,0,0]){const g=new THREE.Group();g.name=name;g.position.set(...pos);parent.add(g);return g;}
  mats.darkSteel=material(0x424b48,.72,.3);
  const skinMaterials=new Map();
  function mesh(parent,geometry,mat,role='skin',pos=[0,0,0]){if(role==='skin'){if(!skinMaterials.has(mat))skinMaterials.set(mat,mat.clone());mat=skinMaterials.get(mat);}const m=new THREE.Mesh(geometry,mat);m.position.set(...pos);m.castShadow=true;m.receiveShadow=true;m.userData.role=role;parent.add(m);if(role==='skin')skins.push(m);if(role==='rib')ribs.push(m);if(role==='hardware')hardware.push(m);if(role==='motor')motors.push(m);pickable.push(m);return m;}
  function roundedRect(path,x,y,w,h,r){r=Math.min(r,w/2,h/2);path.moveTo(x+r,y);path.lineTo(x+w-r,y);path.quadraticCurveTo(x+w,y,x+w,y+r);path.lineTo(x+w,y+h-r);path.quadraticCurveTo(x+w,y+h,x+w-r,y+h);path.lineTo(x+r,y+h);path.quadraticCurveTo(x,y+h,x,y+h-r);path.lineTo(x,y+r);path.quadraticCurveTo(x,y,x+r,y);}
  function circleHole(shape,x,y,r){const p=new THREE.Path();p.absarc(x,y,r,0,Math.PI*2,true);shape.holes.push(p);}
  function extrusion(shape,depth){return new THREE.ExtrudeGeometry(shape,{depth,bevelEnabled:false,curveSegments:20,steps:1});}
  function box(parent,w,h,d,mat,role='skin',pos=[0,0,0],radius=3){const b=Math.min(.65,w/8,h/8,d/4),shape=new THREE.Shape();roundedRect(shape,-w/2+b,-h/2+b,w-2*b,h-2*b,Math.max(.1,radius-b));const geo=new THREE.ExtrudeGeometry(shape,{depth:d-2*b,bevelEnabled:true,bevelThickness:b,bevelSize:b,bevelSegments:3,curveSegments:16});geo.translate(0,0,-d/2+b);return mesh(parent,geo,mat,role,pos);}
  function filletedFace(parent,shape,depth,mat,role='skin',pos=[0,0,0],bevel=.65){return mesh(parent,new THREE.ExtrudeGeometry(shape,{depth:depth-2*bevel,bevelEnabled:true,bevelThickness:bevel,bevelSize:bevel,bevelSegments:4,curveSegments:24}),mat,role,[pos[0],pos[1],pos[2]+bevel]);}
  function plaque(parent,text,w,h,pos,fg='#243b33',bg='#a0baab',role='skin'){const c=document.createElement('canvas');c.width=768;c.height=192;const ctx=c.getContext('2d');ctx.fillStyle=bg;ctx.fillRect(0,0,c.width,c.height);ctx.strokeStyle=fg;ctx.globalAlpha=.32;ctx.lineWidth=3;ctx.strokeRect(14,14,740,164);ctx.globalAlpha=1;ctx.fillStyle=fg;ctx.font='500 66px Segoe UI';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,384,99);const texture=new THREE.CanvasTexture(c);texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=4;const mat=new THREE.MeshStandardMaterial({map:texture,roughness:.42,metalness:0});return mesh(parent,new THREE.PlaneGeometry(w,h),mat,role,pos);}
  function ring(parent,r,tube,mat,role,pos,axis='z'){const m=mesh(parent,new THREE.TorusGeometry(r,tube,8,80),mat,role,pos);if(axis==='x')m.rotation.y=Math.PI/2;if(axis==='y')m.rotation.x=Math.PI/2;return m;}
  function cylinder(parent,r,depth,mat,role='hardware',pos=[0,0,0],axis='z'){const m=mesh(parent,new THREE.CylinderGeometry(r,r,depth,64),mat,role,pos);if(axis==='z')m.rotation.x=Math.PI/2;if(axis==='x')m.rotation.z=Math.PI/2;return m;}
  function annulus(parent,outer,inner,depth,mat,role='rib',pos=[0,0,0],axis='z'){const shape=new THREE.Shape();shape.absarc(0,0,outer,0,Math.PI*2,false);circleHole(shape,0,0,inner);const geo=extrusion(shape,depth);geo.translate(0,0,-depth/2);const m=mesh(parent,geo,mat,role,pos);if(axis==='y')m.rotation.x=-Math.PI/2;if(axis==='x')m.rotation.y=Math.PI/2;return m;}
  function hexPath(radius){const p=new THREE.Path();for(let k=0;k<6;k++){const a=(k+.5)*Math.PI/3;const x=radius*Math.cos(a),y=radius*Math.sin(a);if(k===0)p.moveTo(x,y);else p.lineTo(x,y);}p.closePath();return p;}
  function hexNut(parent,pos,af=SPEC.fastening.nutAF,depth=SPEC.fastening.nutThickness){const p=hexPath(af/Math.sqrt(3));const shape=new THREE.Shape(p.getPoints());circleHole(shape,0,0,1.5);return mesh(parent,extrusion(shape,depth),mats.steel,'hardware',pos);}
  function boss(parent,pos,sign=1){const f=SPEC.fastening,g=group(parent,'Printed M3 captive-nut boss',pos);g.rotation.y=sign>0?Math.PI:0;g.userData.part='fastener';
    annulus(g,f.bossOD/2,f.clearance/2,f.bossLength-f.pocketDepth,mats.rib,'rib',[0,0,(f.bossLength-f.pocketDepth)/2]);
    const shape=new THREE.Shape();shape.absarc(0,0,f.bossOD/2,0,Math.PI*2,false);shape.holes.push(hexPath(f.pocketAF/Math.sqrt(3)));
    mesh(g,extrusion(shape,f.pocketDepth),mats.rib,'rib',[0,0,f.bossLength-f.pocketDepth]);
    hexNut(g,[0,0,f.bossLength-f.pocketDepth+.2]);return g;
  }
  function bolt(parent,pos,sign=1,length=13,mat=mats.steel){const g=group(parent,'M3 steel cover screw',pos);g.rotation.y=sign<0?Math.PI:0;g.userData.part='fastener';cylinder(g,1.5,length,mat,'hardware',[0,0,-length/2]);
    const shape=new THREE.Shape();shape.absarc(0,0,2.75,0,Math.PI*2,false);shape.holes.push(hexPath(2.5/Math.sqrt(3)));mesh(g,extrusion(shape,3),mat,'hardware');return g;
  }
  function bearing(parent,pos,axis='z'){
    const g=group(parent,'608 bearing · 8 × 22 × 7',pos);if(axis==='x')g.rotation.y=Math.PI/2;if(axis==='y')g.rotation.x=-Math.PI/2;
    annulus(g,11,9.1,7,mats.steel,'hardware');annulus(g,6.1,4,7,mats.steel,'hardware');
    [-1,1].forEach(s=>annulus(g,9.3,6,1,mats.bearing,'hardware',[0,0,s*3]));
    for(let k=0;k<8;k++){const a=k*Math.PI/4;mesh(g,new THREE.SphereGeometry(1.5,12,8),mats.steel,'hardware',[7.7*Math.cos(a),7.7*Math.sin(a),0]);}
    return g;
  }
  function cable(parent,points,radius=1.4,mat=null){const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));if(!mat){const texture=braidMap.clone();texture.repeat.set(Math.max(1,curve.getLength()/9),2);texture.needsUpdate=true;mat=new THREE.MeshStandardMaterial({map:texture,bumpMap:texture,bumpScale:.12,roughness:.83,color:0xaaaaaa});}return mesh(parent,new THREE.TubeGeometry(curve,64,radius,12,false),mat,'hardware');}
  function gland(parent,pos,r=3,axis='y'){const g=group(parent,'Printed cable gland + strain relief',pos);if(axis==='y')g.rotation.x=-Math.PI/2;if(axis==='x')g.rotation.y=Math.PI/2;annulus(g,r+2.7,r+.2,3,mats.graphite,'skin');annulus(g,r+1.5,r+.2,7,mats.black,'hardware',[0,0,4]);ring(g,r+1.55,.5,mats.black,'hardware',[0,0,7]);return g;}
  function loomClamp(parent,pos){const g=group(parent,'Printed loom clip',pos);box(g,13,4,11,mats.graphite,'skin',[0,0,0],2);for(let x of [-4.5,4.5]){const b=bolt(g,[x,2,0],1,5);b.rotation.x=-Math.PI/2;}return g;}
  function serviceLoop(a,pa,b,pb,bulge,radius=3){const tube=cable(root,[[0,0,0],[0,10,0],[10,10,0]],radius);tube.name='Braided service loop with moving endpoints';serviceLoops.push({a,pa:new THREE.Vector3(...pa),b,pb:new THREE.Vector3(...pb),bulge:new THREE.Vector3(...bulge),tube,radius});}
  function capsule(length,height){const r=height/2,s=new THREE.Shape();s.moveTo(0,-r);s.lineTo(length,-r);s.absarc(length,0,r,-Math.PI/2,Math.PI/2,false);s.lineTo(0,r);s.absarc(0,0,r,Math.PI/2,Math.PI*1.5,false);return s;}
  function reservation(parent,size,pos){const [w,h,d]=size,g=group(parent,'Generic servo assembly · illustrative hardware',pos);box(g,w,h,d-8,mats.motor,'motor',[0,0,-1],3);box(g,w,h,6,mats.black,'motor',[0,0,d/2-3],3);box(g,w,h,3,mats.black,'motor',[0,0,-d/2+1.5],3);
    for(const z of [-d/2+3,d/2-6])box(g,w+.15,h+.15,.55,mats.alloy,'motor',[0,0,z],3);
    for(const x of [-w/2+3,w/2-3])for(const y of [-h/2+3,h/2-3]){bolt(g,[x,y,d/2],1,d-2);}
    for(const sign of [-1,1]){const ear=new THREE.Shape();roundedRect(ear,sign*w/2-(sign<0?5:0),-h*.34,5,h*.68,1);circleHole(ear,sign*(w/2+2.5),0,1.7);mesh(g,extrusion(ear,2.5),mats.motor,'motor',[0,0,d/2-8]);}
    const output=-w/2+Math.min(h*.36,w*.3);cylinder(g,h*.21,4,mats.alloy,'motor',[output,0,d/2+1.5]);cylinder(g,2.4,7,mats.steel,'hardware',[output,0,d/2+4]);
    annulus(g,h*.29,2.5,1.6,mats.alloy,'motor',[output,0,d/2+6]);for(let i=0;i<4;i++){let a=i*Math.PI/2;bolt(g,[output+h*.22*Math.cos(a),h*.22*Math.sin(a),d/2+7],1,4);}
    const label=plaque(g,'SERVO / '+Math.round(w),w*.58,h*.25,[w*.14,0,d/2+.12],'#ccd9ce','#26302e','motor');
    box(g,6,5,5,mats.black,'motor',[w/2,0,-d/2+6],1);
    [mats.wireRed,mats.wireGold,mats.wireWhite].forEach((m,i)=>cable(g,[[w/2,0,-d/2+5+i],[w/2+6,-3,-d/2+5+i],[w/2+8,-h*.35,-d/2+3+i],[w/2+16,-h*.38,-d/2+3+i]],.55,m));return g;}
  function stepper(parent,pos){const g=group(parent,'Generic 42 mm pancake stepper',pos);box(g,42,17,42,mats.motor,'motor',[0,0,0],4);for(let y of [-10,10])box(g,42,3,42,mats.alloy,'motor',[0,y,0],4);for(let y=-7;y<=7;y+=1.4)box(g,42.25,.35,42.25,mats.black,'motor',[0,y,0],4);
    cylinder(g,11,2,mats.alloy,'motor',[0,12,0],'y');cylinder(g,2.5,14,mats.steel,'hardware',[0,18,0],'y');for(let x of [-15.5,15.5])for(let z of [-15.5,15.5]){const b=bolt(g,[x,11.6,z],1,20);b.rotation.x=-Math.PI/2;}
    box(g,12,6,5,mats.black,'motor',[0,-3,23.5],1);for(let i=0;i<4;i++)cable(g,[[-3+i*2,-3,25],[-3+i*2,-3,30],[-3+i*2,-7,37],[14+i*2,-7,43]],.65,[mats.wireRed,mats.wireGold,mats.wireWhite,mats.black][i]);plaque(g,'STEPPER  /  42',30,8,[0,0,21.25],'#c5d5ca','#242e2c','motor');return g;}
  function jointCover(parent,r,z,sign=1,id=''){const g=group(parent,'Layered printed joint cap',[0,0,z]);if(sign<0)g.rotation.y=Math.PI;annulus(g,r,4.2,3,mats.graphite,'skin');ring(g,r-.6,.65,mats.graphite,'skin',[0,0,1.4]);annulus(g,r-2.2,4.2,1.6,mats.black,'skin',[0,0,2]);ring(g,r-4,.28,mats.alloy,'hardware',[0,0,2.95]);cylinder(g,r*.47,2.4,mats.mint,'skin',[0,0,3.8]);ring(g,r*.47,.35,mats.graphite,'skin',[0,0,5]);
    for(let k=0;k<4;k++){const a=(k+.15)*Math.PI/2;bolt(g,[(r-5.7)*Math.cos(a),(r-5.7)*Math.sin(a),3],1,8,mats.darkSteel);}for(let k=0;k<2;k++){const a=k*Math.PI;bolt(g,[r*.30*Math.cos(a),r*.30*Math.sin(a),5],1,6,mats.darkSteel);}
    if(id)plaque(g,id,r*.45,r*.13,[0,0,5.08],'#254b40','#88afa0');return g;}
  function link(parent,s,id){const g=group(parent,id);g.userData.part=id;parts[id]=g;
    // Closed rectangular shell in the middle span. The ends remain open yokes.
    const middleLength=s.length-56,shape=new THREE.Shape();roundedRect(shape,28,-s.height/2,middleLength,s.height,7);
    const inner=new THREE.Path();roundedRect(inner,28+s.wall,-s.height/2+s.wall,middleLength-2*s.wall,s.height-2*s.wall,4);shape.holes.push(inner);
    mesh(g,extrusion(shape,s.depth-2*s.wall),mats.cream,'skin',[0,0,-s.depth/2+s.wall]);
    const screwPoints=[36,s.length-36].flatMap(x=>[-1,1].map(sign=>[x,sign*(s.height/2-8)]));
    [-1,1].forEach(sign=>{
      const cover=group(g,'Removable printed side cover',[0,0,sign>0?s.depth/2-s.wall:-s.depth/2]);cover.userData.part=id;
      const b=1.05,face=capsule(s.length,s.height-2*b);circleHole(face,0,0,4.2+b);circleHole(face,s.length,0,SPEC.bearing.seat/2+b);screwPoints.forEach(([x,y])=>circleHole(face,x,y,SPEC.fastening.clearance/2+b));
      // A rounded perimeter lip adds a visible split seam; bores stay true cylinders.
      filletedFace(cover,face,s.wall,mats.cream,'skin',[0,0,0],b);covers.push({group:cover,origin:cover.position.clone(),sign});
      const trim=capsule(s.length,s.height-1.5);const inside=capsule(s.length,s.height-5);trim.holes.push(new THREE.Path(inside.getPoints(80)));
      filletedFace(cover,trim,.9,mats.cream,'skin',[0,0,sign>0?s.wall-.3:-.6],.3);
      const z=sign>0?s.wall+.12:-.12;
      const relief=new THREE.Shape();relief.moveTo(29,-s.height*.30);relief.quadraticCurveTo(35,-s.height*.36,46,-s.height*.34);relief.lineTo(s.length-41,-s.height*.30);relief.quadraticCurveTo(s.length-27,-s.height*.22,s.length-29,0);relief.quadraticCurveTo(s.length-27,s.height*.22,s.length-41,s.height*.30);relief.lineTo(46,s.height*.34);relief.quadraticCurveTo(29,s.height*.35,29,s.height*.22);relief.closePath();
      const rg=group(cover,'Sculpted reinforcement panel',[0,0,z]);if(sign<0)rg.rotation.x=Math.PI;filletedFace(rg,relief,1.7,mats.cream,'skin',[0,0,0],.65);
      box(rg,s.length-85,1.1,.4,mats.panel,'skin',[s.length/2,-s.height*.22,1.8],.4);
      plaque(rg,id==='upper'?'ORBIT  /  180':'EDU–05  /  150',id==='upper'?42:38,5,[s.length*.52,2,1.75],'#728678','#e2e2d4');
      screwPoints.forEach(([x,y])=>{boss(g,[x,y,sign*(s.depth/2-s.wall)],sign);bolt(cover,[x,y,sign>0?s.wall:0],sign);});
      const seat=group(g,'Printed bearing seat',[s.length,0,sign*(s.depth/2-7.2/2)]);annulus(seat,15,11.1,7.2,mats.rib,'rib');annulus(g,15,4.2,2,mats.rib,'rib',[s.length,0,sign*(s.depth/2-8.2)]);
      bearing(g,[s.length,0,sign*(s.depth/2-3.5)]);
      const distal=group(cover,'Distal joint module',[s.length,0,sign>0?s.wall+1.5:-1.5]);jointCover(distal,s.height/2-2,0,sign,id==='upper'?'J3':'J4');
      jointCover(cover,s.height/2-2,sign>0?s.wall+1.5:-1.5,sign,id==='upper'?'J2':'J3');
    });
    // Rib plates bridge the two skins; a real opening leaves space for the cable loom.
    [s.length*.35,s.length*.65].forEach(x=>{const shape=new THREE.Shape();roundedRect(shape,-s.depth/2+s.wall,-s.height/2+s.wall,s.depth-2*s.wall,s.height-2*s.wall,2);const hole=new THREE.Path();roundedRect(hole,-8,-6,16,12,3);shape.holes.push(hole);const m=mesh(g,extrusion(shape,s.rib),mats.rib,'rib',[x-s.rib/2,0,0]);m.rotation.y=Math.PI/2;});
    cylinder(g,4,s.depth+14,mats.steel,'hardware',[s.length,0,0]);
    cable(g,[[24,-4,2],[s.length*.35,-3,2],[s.length*.65,2,2],[s.length-21,6,2]],1.5);
    const loomY=s.height/2+4,loomZ=-s.depth*.23;
    cable(g,[[19,loomY,loomZ],[43,loomY+2,loomZ],[s.length*.6,loomY+2,loomZ],[s.length-20,loomY,loomZ]],2.6);
    [47,s.length-43].forEach(x=>loomClamp(g,[x,loomY,loomZ]));
    gland(g,[19,loomY-1,loomZ],2.6);gland(g,[s.length-20,loomY-1,loomZ],2.6);
    // A narrow gasket follows the shell seam and makes the clamshell construction legible.
    for(const sign of [-1,1]){box(g,s.length-68,.8,1.1,mats.graphite,'skin',[s.length/2,s.height/2-.3,sign*(s.depth/2-s.wall)],.2);}
    return g;
  }

  // Base: actual anchor holes, hollow walls, bottom ribs, removable top cover.
  const baseGroup=group(root,'Printed base enclosure');baseGroup.userData.part='base';parts.base=baseGroup;
  const baseShape=new THREE.Shape();roundedRect(baseShape,-90,-80,180,160,14);for(const x of [-75,75])for(const y of [-65,65])circleHole(baseShape,x,y,3.3);
  const plate=mesh(baseGroup,extrusion(baseShape,4),mats.cream,'skin',[0,4,0]);plate.rotation.x=Math.PI/2;
  const walls=new THREE.Shape();roundedRect(walls,-90,-80,180,160,14);const baseInside=new THREE.Path();roundedRect(baseInside,-86,-76,172,152,10);walls.holes.push(baseInside);
  for(const x of [-75,75])for(const z of [-65,65]){annulus(baseGroup,9,3.3,24,mats.rib,'rib',[x,16,z],'y');}
  const wallMesh=mesh(baseGroup,extrusion(walls,24),mats.cream,'skin',[0,28,0]);wallMesh.rotation.x=Math.PI/2;
  const baseCover=group(baseGroup,'Base top cover',[0,32,0]);const top=mesh(baseCover,extrusion(baseShape,4),mats.cream,'skin');top.rotation.x=Math.PI/2;covers.push({group:baseCover,origin:baseCover.position.clone(),axis:'y',sign:1});
  const baseTrim=new THREE.Shape();roundedRect(baseTrim,-89.1,-79.1,178.2,158.2,13);const trimInside=new THREE.Path();roundedRect(trimInside,-87.1,-77.1,174.2,154.2,11);baseTrim.holes.push(trimInside);
  const topTrim=filletedFace(baseCover,baseTrim,1.6,mats.cream,'skin',[0,0,0],.6);topTrim.rotation.x=-Math.PI/2;topTrim.position.set(0,.2,0);
  for(const x of [-75,75])for(const z of [-65,65]){annulus(baseCover,6.8,3.3,1.1,mats.alloy,'hardware',[x,.45,z],'y');const foot=new THREE.Shape();roundedRect(foot,-12,-11,24,22,5);circleHole(foot,0,0,3.3);const f=mesh(baseGroup,extrusion(foot,5),mats.graphite,'skin',[x,5,z]);f.rotation.x=Math.PI/2;}
  box(baseGroup,96,19,1.8,mats.graphite,'skin',[0,17,80.3],4);box(baseGroup,94,17,1.3,mats.mint,'skin',[0,17,81],3);
  plaque(baseGroup,'EDUARM   5–DOF',88,13,[0,17,81.7]);
  [-58,58].forEach(x=>{for(let i=0;i<4;i++)box(baseGroup,1.8,8,.5,mats.graphite,'skin',[x+i*3,16,80.2],.7);});
  for(let z of [-1,1]){box(baseGroup,144,.8,1,mats.graphite,'skin',[0,5.5,z*79.9],.3);}
  [-38,38].forEach(z=>box(baseGroup,160,18,3,mats.rib,'rib',[0,13,z]));[-52,52].forEach(x=>box(baseGroup,3,18,140,mats.rib,'rib',[x,13,0]));
  stepper(baseGroup,[0,16,0]);cylinder(baseGroup,4,35,mats.steel,'hardware',[0,29,0],'y');
  const yaw=group(root,'J1 base yaw',[0,38,0]);yaw.userData.joint=0;joints.push(yaw);
  cylinder(yaw,55,8,mats.graphite,'skin',[0,0,0],'y');annulus(yaw,54,24,5,mats.cream,'skin',[0,6,0],'y');bearing(yaw,[0,8,0],'y');
  for(let y of [-2.5,.4,3])ring(yaw,54.7,.6,mats.black,'skin',[0,y,0],'y');
  for(let k=0;k<10;k++){const a=k*2*Math.PI/10,b=bolt(yaw,[49*Math.cos(a),4.4,49*Math.sin(a)],1,8);b.rotation.x=-Math.PI/2;}
  const yoke=group(yaw,'Printed shoulder yoke');yoke.userData.part='shoulder';parts.shoulder=yoke;
  const shoulderOffset=SPEC.shoulderHeight-38;
  [-1,1].forEach(sign=>{
    const shape=new THREE.Shape();roundedRect(shape,-28,8,56,shoulderOffset+21-8,20);circleHole(shape,0,shoulderOffset,11.1);
    const m=mesh(yoke,extrusion(shape,8),mats.cream,'skin',[0,0,sign>0?34:-42]);
    const inset=new THREE.Shape();roundedRect(inset,-20,17,40,shoulderOffset-17,16);filletedFace(yoke,inset,1.5,mats.mint,'skin',[0,0,sign>0?42:-43.5],.4);
    box(yoke,38,38,6,mats.cream,'skin',[0,27,sign*28],5);
    for(let x of [-18,18]){bolt(yoke,[x,26,sign*44],sign,12);}
    annulus(yoke,15,11.1,7.2,mats.rib,'rib',[0,shoulderOffset,sign*37.6]);bearing(yoke,[0,shoulderOffset,sign*37.5]);
    const cap=group(yoke,'Shoulder support end cap',[0,shoulderOffset,0]);jointCover(cap,25,sign*44,sign,'J2');
    box(yoke,48,12,27,mats.mint,'skin',[0,12,sign*27],5);
    for(let x of [-15,15]){const screw=bolt(yoke,[x,18.5,sign*24],1,12);screw.rotation.x=-Math.PI/2;}
  });
  const shoulder=group(yaw,'J2 shoulder pitch',[0,shoulderOffset,0]);shoulder.userData.joint=1;joints.push(shoulder);
  link(shoulder,SPEC.upper,'upper');cylinder(shoulder,4,91,mats.steel,'hardware');reservation(shoulder,SPEC.motorEnvelope.shoulder,[42,0,0]);
  const elbow=group(shoulder,'J3 elbow pitch',[SPEC.upper.length,0,0]);elbow.userData.joint=2;joints.push(elbow);link(elbow,SPEC.forearm,'forearm');reservation(elbow,SPEC.motorEnvelope.elbow,[38,0,0]);
  const wrist=group(elbow,'J4 wrist pitch',[SPEC.forearm.length,0,0]);wrist.userData.joint=3;joints.push(wrist);const wristGroup=group(wrist,'Printed wrist fork');wristGroup.userData.part='wrist';parts.wrist=wristGroup;
  // Two planar cheeks support the pitch hinge; a short coaxial drum provides roll.
  for(const sign of [-1,1]){const shape=capsule(SPEC.wrist.length,36);circleHole(shape,0,0,4.2);const m=mesh(wristGroup,extrusion(shape,5),mats.cream,'skin',[0,0,sign>0?12:-17]);
    jointCover(wristGroup,16,sign*19,sign,'J4');
    box(wristGroup,30,23,1.4,mats.panel,'skin',[30,0,sign*18],5);for(let x of [18,43])for(let y of [-10,10])bolt(wristGroup,[x,y,sign*18.5],sign,8);
  }
  box(wristGroup,26,22,24,mats.rib,'rib',[33,0,0]);reservation(wristGroup,SPEC.motorEnvelope.wrist,[31,0,0]);
  const carrier=annulus(wristGroup,21,11.1,14,mats.mint,'skin',[52,0,0],'x');bearing(wristGroup,[52,0,0],'x');cylinder(wristGroup,4,36,mats.steel,'hardware',[57,0,0],'x');
  for(let x of [46,58]){annulus(wristGroup,21.5,11.1,2,mats.graphite,'skin',[x,0,0],'x');ring(wristGroup,20.6,.5,mats.alloy,'hardware',[x,0,0],'x');}
  for(let k=0;k<6;k++){const a=(k+.5)*Math.PI/3,b=bolt(wristGroup,[60,17*Math.sin(a),17*Math.cos(a)],1,9);b.rotation.y=Math.PI/2;}
  const roll=group(wrist,'J5 wrist roll',[SPEC.wrist.length,0,0]);roll.userData.joint=4;joints.push(roll);
  annulus(roll,16,4.2,10,mats.graphite,'skin',[12,0,0],'x');
  const gripper=group(roll,'Printed parallel gripper');gripper.userData.part='gripper';parts.gripper=gripper;
  box(gripper,14,26,72,mats.graphite,'skin',[30,0,0],5);box(gripper,4,20,68,mats.mint,'rib',[39,0,0],3);
  box(gripper,14,29,44,mats.graphite,'skin',[22,0,0],4);box(gripper,2,24,40,mats.alloy,'hardware',[13.8,0,0],3);
  const palmLabel=plaque(gripper,'ORBIT',18,6,[30,13.2,0],'#b0c9bb','#273330');palmLabel.rotation.x=-Math.PI/2;
  for(let z of [-29,29])for(let y of [-9,9]){const b=bolt(gripper,[37.5,y,z],1,10);b.rotation.y=Math.PI/2;}
  for(const y of [-7,7])cylinder(gripper,2,SPEC.gripper.railSpan,mats.steel,'hardware',[44,y,0]);
  for(const sign of [-1,1]){const flange=new THREE.Shape();roundedRect(flange,-6,-12,12,24,3);[-7,7].forEach(y=>circleHole(flange,0,y,SPEC.gripper.guideBore/2));mesh(gripper,extrusion(flange,3),mats.graphite,'skin',[44,0,sign>0?39:-42]);box(gripper,12,23,5,mats.graphite,'skin',[38,0,sign*37],3);}
  const fingers=[];for(const sign of [-1,1]){const finger=group(gripper,'Printed gripper finger',[SPEC.toolLength-SPEC.gripper.fingerLength/2,0,sign*(SPEC.gripper.opening/2+5.5)]);box(finger,30,16,8,mats.graphite,'skin',[5,0,0],3);box(finger,24,11,1.2,mats.mint,'skin',[5,0,sign*4.3],2);box(finger,14,14,1.5,mats.black,'hardware',[12,0,-sign*4.75],1);
    const slider=new THREE.Shape();roundedRect(slider,-20,-12,12,24,2);[-7,7].forEach(y=>circleHole(slider,-14,y,SPEC.gripper.guideBore/2));mesh(finger,extrusion(slider,10),mats.graphite,'skin',[0,0,-5]);
    for(let x of [-14,13])bolt(finger,[x,0,sign*5.3],sign,8);for(let x of [7,10,13,16])box(finger,.6,11,.2,mats.gasket,'hardware',[x,0,-sign*5.35],.05);fingers.push(finger);}
  const tip=group(roll,'Tool centre',[SPEC.toolLength,0,0]);
  cable(yaw,[[-31,12,-28],[-36,28,-31],[-40,50,-33],[-25,64,-35]],3.2);
  serviceLoop(baseGroup,[-40,32,-28],yaw,[-31,12,-28],[-30,26,-18],3.2);
  serviceLoop(yaw,[-25,64,-35],shoulder,[19,30,-14],[-28,28,-18],3.0);
  serviceLoop(shoulder,[160,30,-14],elbow,[19,26,-10.6],[0,37,-20],2.7);
  serviceLoop(elbow,[130,26,-10.6],wrist,[25,20,-13],[0,28,-12],2.3);
  serviceLoop(wrist,[38,-17,0],roll,[25,-15,-18],[6,-24,4],2.1);
  gland(wrist,[25,18,-13],2.3);gland(roll,[25,-13,-18],2.1);
  // A magnified part inspection scene uses the exact same fastening geometry.
  detail.name='M3 fastening detail';detail.userData.part='fastener';parts.fastener=detail;
  const fastenerDetail=group(detail,'Captive nut inspection'),driveDetail=group(detail,'Drive hardware inspection');fastenerDetail.userData.part='fastener';driveDetail.userData.part='drives';driveDetail.visible=false;parts.drives=driveDetail;
  reservation(driveDetail,SPEC.motorEnvelope.shoulder,[-37,0,0]);
  stepper(driveDetail,[39,0,0]);
  box(driveDetail,52,4,40,mats.mint,'skin',[-37,-18,0],4);box(driveDetail,52,4,52,mats.mint,'skin',[39,-14,0],4);
  plaque(driveDetail,'SERVO  /  CONCEPT',46,8,[-37,-22,25],'#9cb7a6','#172c22','motor');plaque(driveDetail,'STEPPER  /  CONCEPT',52,8,[39,-22,29],'#9cb7a6','#172c22','motor');
  const dCover=group(fastenerDetail,'Cover with actual bolt clearance',[0,0,-3]);const ds=new THREE.Shape();roundedRect(ds,-13,-13,26,26,3);circleHole(ds,0,0,1.7);mesh(dCover,extrusion(ds,3),mats.cream,'skin');
  const actualBoss=boss(fastenerDetail,[0,0,0],-1);bolt(fastenerDetail,[0,0,-3],-1,13);
  // Pull the nut out along the same axis in this inspection-only detail.
  actualBoss.children.filter(o=>o.userData.role==='hardware').forEach(o=>o.position.z+=15);
  // Bracing ties the cylindrical boss to the surrounding printed wall.
  [-1,1].forEach(s=>box(fastenerDetail,3,12,9,mats.rib,'rib',[s*7.5,0,4.5],1));
  parts.fastener=actualBoss;

  function applyPose(a){joints[0].rotation.y=a[0]*Math.PI/180;for(let i=1;i<=3;i++)joints[i].rotation.z=a[i]*Math.PI/180;joints[4].rotation.x=a[4]*Math.PI/180;fingers.forEach((f,i)=>f.position.z=(i===0?-1:1)*(a[5]/2+5.5));root.updateMatrixWorld(true);
    for(const l of serviceLoops){const start=l.a.localToWorld(l.pa.clone()),end=l.b.localToWorld(l.pb.clone()),offset=l.bulge.clone().applyQuaternion(l.a.getWorldQuaternion(new THREE.Quaternion()));const p1=start.clone().lerp(end,.25).add(offset),p2=start.clone().lerp(end,.75).add(offset);const curve=new THREE.CatmullRomCurve3([start,p1,p2,end]);l.tube.geometry.dispose();l.tube.geometry=new THREE.TubeGeometry(curve,64,l.radius,12,false);l.tube.material.map.repeat.x=curve.getLength()/9;}
  }
  function setMode(mode){
    for(const m of new Set(skins.map(o=>o.material))){m.transparent=mode==='xray';m.opacity=mode==='xray'?.13:1;m.depthWrite=mode!=='xray';m.side=mode==='xray'?THREE.DoubleSide:THREE.FrontSide;m.needsUpdate=true;}
    skins.forEach(m=>{m.castShadow=mode==='exterior';});covers.forEach(c=>c.group.visible=mode!=='open');
    edgeLines.forEach(e=>e.material.opacity=mode==='xray'?.06:.15);
    mats.motor.color.set(mode==='exterior'?0x303738:0xad7850);mats.steel.color.set(mode==='exterior'?0xc3ced0:0x83bdc9);mats.bearing.color.set(mode==='exterior'?0x687778:0x6faec6);
  }
  function separate(value){covers.forEach(c=>{c.group.position.copy(c.origin);c.group.position[c.axis||'z']+=c.sign*value;});root.updateMatrixWorld(true);}
  function detailMode(show,kind='fastener'){detail.visible=show;root.visible=!show;fastenerDetail.visible=kind==='fastener';driveDetail.visible=kind==='drives';}
  function worldTip(){const p=new THREE.Vector3();tip.getWorldPosition(p);return [p.x,-p.z,p.y];}
  function cableEndpointError(){let error=0;for(const l of serviceLoops){const pos=l.tube.geometry.attributes.position;for(const [row,anchor,node] of [[0,l.pa,l.a],[64,l.pb,l.b]]){const centre=new THREE.Vector3();for(let i=0;i<12;i++)centre.add(new THREE.Vector3().fromBufferAttribute(pos,row*13+i));centre.divideScalar(12);error=Math.max(error,centre.distanceTo(node.localToWorld(anchor.clone())));}}return error;}
  applyPose(SPEC.home);
  return {root,detail,parts,joints,covers,skins,ribs,hardware,motors,pickable,mats,applyPose,setMode,separate,detailMode,worldTip,tip,serviceLoops,cableEndpointError};
}

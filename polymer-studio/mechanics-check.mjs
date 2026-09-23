import assert from 'node:assert/strict';
import {SPEC,kinematics,gravityTorques} from './spec.js';
const close=(a,b)=>assert(Math.abs(a-b)<1e-9,`${a} != ${b}`);
const mass=SPEC.massAssumptionsKg;
const horizontal=gravityTorques([0,0,0,0,0,34]);
const expected=[
  9.80665*(mass.upper*.09+mass.elbowMotor*.18+mass.forearm*.255+mass.wristMotor*.33+mass.wrist*.356+mass.tool*.421+mass.payload*.46),
  9.80665*(mass.forearm*.075+mass.wristMotor*.15+mass.wrist*.176+mass.tool*.241+mass.payload*.28),
  9.80665*(mass.wrist*.026+mass.tool*.091+mass.payload*.13)
];
horizontal.forEach((t,i)=>close(t,expected[i]));
gravityTorques([42,90,0,0,120,12]).forEach(t=>close(t,0));
gravityTorques([130,0,0,0,-70,50]).forEach((t,i)=>close(t,horizontal[i]));
const a=kinematics(SPEC.home).points.at(-1),b=kinematics([...SPEC.home.slice(0,4),140,0]).points.at(-1);a.forEach((v,i)=>close(v,b[i]));
const zeroMass={upper:0,forearm:0,wrist:0,tool:0,elbowMotor:0,wristMotor:0,payload:1};
gravityTorques([0,0,0,0,0,0],zeroMass).forEach((t,i)=>close(t,9.80665*[.46,.28,.13][i]));
console.log('PASS: independently calculated horizontal gravity moments, zero vertical moments, yaw invariance, tool-axis roll invariance, and payload-only SI units.');

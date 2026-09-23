const fs=require('node:fs');
const assert=require('node:assert/strict');
const s=JSON.parse(fs.readFileSync('design-concepts/edu06-lightweight-spec.json','utf8'));
const g=9.80665;
const axes=[['J2',0,2],['J3',120,3],['J5',255,5]];
const calculate=payload=>axes.map(([name,x,group])=>{
 const dead=s.movingMassAssumptions.filter(v=>v.loadGroup>=group).reduce((sum,v)=>sum+v.mass_g*(v.x_mm-x),0);
 return {joint:name,Nm:(dead+payload*(370-x))*g/1e6};
});
for(const [key,payload] of [['zero',0],['fifty',50],['hundred',100],['twohundred',200]]){
 const expected=s.screeningResults[key],actual=calculate(payload);
 actual.forEach((v,i)=>assert(Math.abs(v.Nm-expected[i].Nm)<1e-10));
}
assert.equal(5*s.motors.AX12A.mass_g+2*s.motors.XM430W350T.mass_g,437);
const fifty=calculate(50),hundred=calculate(100);
axes.forEach(([,x],i)=>assert(Math.abs(hundred[i].Nm-fifty[i].Nm-.05*g*(370-x)/1000)<1e-10));
assert(hundred[2].Nm*1.5>.3);assert(fifty[2].Nm*1.5<.3);
console.log('PASS: unit conversion, payload moment increments, seven-motor mass and wrist static-reserve comparison. These checks do not validate physical capacity.');
(async()=>{
 const {chromium}=require('C:/Users/hpone/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1200,height:710}});
 await page.setContent('<style>body{margin:0}</style>'+fs.readFileSync('design-concepts/edu06-mounting-patterns.svg','utf8'));
 await page.screenshot({path:'design-concepts/edu06-mounting-patterns.png'});await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});

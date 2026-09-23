const {chromium}=require('C:/Users/hpone/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:1180},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 await page.goto('http://127.0.0.1:4173/polymer-studio/index.html');await page.waitForFunction(()=>!!window.polymerStudio);await page.waitForTimeout(1600);
 fs.mkdirSync('polymer-studio/qa',{recursive:true});await page.screenshot({path:'polymer-studio/qa/exterior.png',fullPage:true});
 const state=()=>page.evaluate(()=>window.polymerStudio.getState());const near=(a,b)=>a.forEach((v,i)=>assert(Math.abs(v-b[i])<1e-6,`${v} != ${b[i]}`));
 let s=await state();near(s.tool,s.calculatedTool);assert(s.internalGeometry.ribs>20);assert(s.internalGeometry.hardware>50);assert.equal(s.skinOpacity,1);assert.equal(s.internalGeometry.serviceLoops,5);assert(s.cableEndpointErrorMm<.001);
 await page.getByRole('button',{name:'X-ray',exact:true}).click();s=await state();assert.equal(s.mode,'xray');assert(s.skinOpacity<.2);await page.waitForTimeout(700);await page.screenshot({path:'polymer-studio/qa/xray.png',fullPage:true});
 await page.getByRole('button',{name:'Open covers',exact:true}).click();s=await state();assert.equal(s.visibleCovers,0);await page.waitForTimeout(300);await page.screenshot({path:'polymer-studio/qa/open-covers.png',fullPage:true});
 await page.getByRole('button',{name:'Exterior',exact:true}).click();assert.equal((await state()).visibleCovers,5);
 await page.locator('#separation').fill('30');assert.equal((await state()).separation,30);await page.locator('#separation').fill('0');
 await page.getByRole('button',{name:'Labels',exact:true}).click();await page.waitForFunction(()=>[...document.querySelectorAll('.joint-label')].every(e=>e.hidden));assert.equal(await page.locator('.joint-label:visible').count(),0);await page.getByRole('button',{name:'Labels',exact:true}).click();await page.waitForFunction(()=>[...document.querySelectorAll('.joint-label')].every(e=>!e.hidden));assert.equal(await page.locator('.joint-label:visible').count(),5);
 await page.getByRole('button',{name:'Dimensions',exact:true}).click();await page.waitForFunction(()=>[...document.querySelectorAll('.dimension-label')].every(e=>!e.hidden));assert.equal(await page.locator('.dimension-label:visible').count(),2);
 await page.getByRole('slider',{name:'Elbow angle',exact:true}).fill('-40');s=await state();near(s.tool,s.calculatedTool);const before=s.tool;
 await page.getByRole('slider',{name:'Wrist roll angle',exact:true}).fill('130');near((await state()).tool,before);assert((await state()).cableEndpointErrorMm<.001);
 await page.getByRole('slider',{name:'Gripper opening',exact:true}).fill('50');near((await state()).tool,before);
 const n=page.getByRole('spinbutton',{name:'Shoulder degrees',exact:true});await n.fill('999');await n.press('Tab');assert.equal((await state()).angles[1],145);assert.equal(await n.inputValue(),'145');
 await page.getByRole('button',{name:'Home',exact:true}).click();await page.waitForTimeout(1250);
 await page.getByRole('tab',{name:'Loads',exact:true}).click();const t0=(await state()).torques[0];await page.locator('#payload').fill('200');const s1=await state();assert(s1.torques[0]>t0);const radial=Math.hypot(s1.tool[0],s1.tool[1]);assert(Math.abs(s1.torques[0]-t0-.1*9.80665*radial/1000)<1e-6);await page.screenshot({path:'polymer-studio/qa/loads.png',fullPage:true});
 await page.getByRole('button',{name:'Inspect motors',exact:false}).click();await page.waitForTimeout(900);assert((await state()).detailOn);assert.equal((await state()).detailKind,'drives');assert((await page.locator('#scene-mode').innerText()).includes('stepper'));await page.screenshot({path:'polymer-studio/qa/motors.png',fullPage:true});
 await page.getByRole('button',{name:'X-ray',exact:true}).click();assert((await page.locator('#scene-mode').innerText()).includes('stepper'));await page.getByRole('button',{name:'Exterior',exact:true}).click();
 await page.getByRole('tab',{name:'Parts',exact:true}).click();await page.locator('#part-select').selectOption('fastener');assert((await page.locator('#part-dimensions').innerText()).includes('5.8 mm'));
 await page.getByRole('button',{name:'Inspect M3 nut pocket',exact:true}).click();await page.waitForTimeout(900);assert((await state()).detailOn);await page.screenshot({path:'polymer-studio/qa/fastener.png',fullPage:true});
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Specification JSON',exact:false}).click();const download=await downloadPromise;assert(download.suggestedFilename().endsWith('.json'));
 await page.getByRole('button',{name:'Fit',exact:true}).click();await page.waitForTimeout(800);assert.equal((await state()).detailOn,false);
 for(const name of ['Front','Side','Top','3D']){await page.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(700);}
 await page.getByRole('tab',{name:'Motion',exact:true}).click();await page.getByRole('button',{name:'Play motion study',exact:false}).click();await page.waitForTimeout(500);assert.equal((await state()).playing,true);await page.keyboard.press('Escape');assert.equal((await state()).playing,false);await page.getByRole('button',{name:'Home',exact:true}).click();await page.waitForTimeout(1250);
 for(const width of [1024,768,390,320]){await page.setViewportSize({width,height:1050});await page.waitForTimeout(600);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Overflow ${width}`);await page.screenshot({path:`polymer-studio/qa/width-${width}.png`,fullPage:true});}
 assert.deepEqual(errors,[]);console.log('PASS: rendering, explicit internal geometry, X-ray opacity, open covers, cover separation, labels, dimensions, kinematics, roll/gripper independence, clamping, payload torque, part dimensions, fastener detail, JSON download, cameras, motion/stop, responsive widths 320–1440.');await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});

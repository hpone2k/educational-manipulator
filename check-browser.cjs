const {chromium}=require('C:/Users/hpone/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 await page.goto('http://127.0.0.1:4173');await page.waitForFunction(()=>!!window.robotStudio);await page.waitForTimeout(1500);
 fs.mkdirSync('qa',{recursive:true});await page.screenshot({path:'qa/desktop.png',fullPage:true});
 const state=()=>page.evaluate(()=>window.robotStudio.getState());
 const initial=await state();
 function fk(a){const r=Math.PI/180;const p=a[1]*r,e=(a[1]+a[2])*r,w=(a[1]+a[2]+a[3])*r;const radius=180*Math.cos(p)+150*Math.cos(e)+125*Math.cos(w);return [radius*Math.cos(a[0]*r),radius*Math.sin(a[0]*r),90+180*Math.sin(p)+150*Math.sin(e)+125*Math.sin(w)];}
 function near(actual,expected){actual.forEach((v,i)=>assert(Math.abs(v-expected[i])<1e-6,`${v} != ${expected[i]}`));}
 near(initial.tool,fk(initial.angles));
 await page.getByRole('button',{name:'Select J3, Elbow',exact:true}).click();assert.equal((await state()).selected,2);
 const elbow=page.getByRole('slider',{name:'Elbow angle',exact:true});await elbow.fill('-45');await page.waitForTimeout(100);near((await state()).tool,fk((await state()).angles));assert.notDeepEqual((await state()).tool,initial.tool);
 const beforeRoll=(await state()).tool;await page.getByRole('slider',{name:'Wrist roll angle',exact:true}).fill('140');near((await state()).tool,beforeRoll);
 await page.getByRole('slider',{name:'Gripper opening',exact:true}).fill('60');near((await state()).tool,beforeRoll);
 const number=page.getByRole('spinbutton',{name:'Shoulder angle in degrees',exact:true});await number.fill('999');await number.press('Tab');assert.equal((await state()).angles[1],150);assert.equal(await number.inputValue(),'150');
 await page.getByRole('button',{name:'Labels',exact:true}).click();assert.equal((await state()).labels,false);await page.getByRole('button',{name:'Labels',exact:true}).click();
 await page.getByRole('button',{name:'Axes',exact:true}).click();assert.equal(await page.getByRole('button',{name:'Axes',exact:true}).getAttribute('aria-pressed'),'true');
 for(const name of ['Front','Side','Top','3D']){await page.getByRole('button',{name,exact:true}).click();await page.waitForTimeout(700);assert((await state()).camera.every(Number.isFinite));}
 await page.getByRole('button',{name:'Home',exact:true}).click();await page.waitForTimeout(1150);near((await state()).tool,initial.tool);
 await page.getByRole('button',{name:'Play demonstration',exact:false}).click();await page.waitForTimeout(500);assert.equal((await state()).playing,true);await page.getByRole('button',{name:'Stop demonstration',exact:false}).click();assert.equal((await state()).playing,false);
 await page.getByRole('button',{name:'Home',exact:true}).click();await page.waitForTimeout(1100);
 for(const width of [1024,768,390,320]){await page.setViewportSize({width,height:1000});await page.waitForTimeout(500);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`Overflow at ${width}`);await page.screenshot({path:`qa/width-${width}.png`,fullPage:true});}
 assert.deepEqual(errors,[]);console.log('PASS: WebGL, forward kinematics, joint selection, elbow motion, wrist-roll invariance, gripper independence, number clamping, label and axis toggles, camera views, home pose, demo start/stop, responsive overflow at 1440/1024/768/390/320.');
 await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});

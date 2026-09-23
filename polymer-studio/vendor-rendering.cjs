// Reproducible download of the add-ons matching the locally pinned Three.js r180.
const fs=require('node:fs/promises');
const path=require('node:path');
const target=path.resolve(__dirname,'../vendor/addons');
const seen=new Set();
async function fetchModule(relative){
 if(seen.has(relative))return;seen.add(relative);
 const response=await fetch('https://raw.githubusercontent.com/mrdoob/three.js/r180/examples/jsm/'+relative);
 if(!response.ok)throw Error(response.status+' '+relative);
 const source=await response.text(),file=path.resolve(target,relative);
 if(!file.startsWith(target+path.sep))throw Error('Unexpected module path');
 await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,source);
 for(const match of source.matchAll(/from\s+['"]([^'"]+)['"]/g))if(match[1].startsWith('.'))await fetchModule(path.posix.normalize(path.posix.join(path.posix.dirname(relative),match[1])));
 console.log(relative);
}
(async()=>{for(const entry of ['postprocessing/EffectComposer.js','postprocessing/RenderPass.js','postprocessing/SSAOPass.js','postprocessing/OutputPass.js'])await fetchModule(entry);})().catch(e=>{console.error(e);process.exit(1);});

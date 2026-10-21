import {DEFAULTS,format,csv,project,validateProject,download,powerAxis} from './utils.js';
import {heatmap,imagePreview,lineChart} from './charts.js';
import {saveRun,runs} from './storage.js';
import {setupBeamPreview} from './beam.js';
import {setupModeLab} from './modes.js';

const $=id=>document.getElementById(id);
const form=$('simulation-form'), expForm=$('experiment-form');
let worker, sequence=0, pending=new Map(), busy=false, taskClock;
let result=null, fieldView='intensity', resultSource='example', currentTab='simulation', showAll=false;
let simulatedInWorker=false, imageInWorker=false, currentImage=null, imageSource=null, imageBuffer=null, imageName='', imageMode='auto', experiment=null;
let previewError=false;
let drawBeam=()=>{};
const modeLab=setupModeLab({request,withTask,readForm});
function inspectMode(name,config){
  if(busy)return;
  const m=/^(HE|EH|TE|TM)_(\d+),(\d+)([cs]?)$/.exec(name);
  if(m)modeLab.open({family:m[1],n:Number(m[2]),m:Number(m[3]),orientation:m[4]||'c'},config);
}

function toast(text){$('toast-text').textContent=text;$('toast').hidden=false;}
$('close-toast').onclick=()=>$('toast').hidden=true;

function getWorker(){
  if(worker)return worker;
  worker=new Worker(new URL('./worker.js',import.meta.url),{type:'module'});
  worker.onmessage=({data})=>{
    if(data.type==='ready')return;
    const task=pending.get(data.id);if(!task)return;
    if(data.type==='progress'){
      $('task-message').textContent=data.message;
      $('task-progress').value=Math.min(1,Math.max(0,data.fraction));
    } else {
      pending.delete(data.id);
      if(data.type==='result')task.resolve(data.result);else task.reject(new Error(data.message));
    }
  };
  worker.onerror=e=>{
    for(const task of pending.values())task.reject(new Error(e.message||'The calculation engine could not start. Check your connection and reload the page.'));
    pending.clear();worker?.terminate();worker=null;simulatedInWorker=false;imageInWorker=false;
  };
  return worker;
}
function request(action,payload={},raw=null){
  return new Promise((resolve,reject)=>{
    const id=++sequence;pending.set(id,{resolve,reject});
    try{getWorker().postMessage({id,action,payload,raw});}catch(e){pending.delete(id);reject(e);}
  });
}
function setBusy(value){
  busy=value;document.body.classList.toggle('busy',value);$('task-panel').hidden=!value;
  for(const el of document.querySelectorAll('form input, form select, form button'))el.disabled=value;
  for(const el of document.querySelectorAll('.mixture-row input,.mixture-row button,#clear-mixture,#calculate-mixture,#open-mode-lab'))el.disabled=value;
  $('calculate-mixture').disabled=value||!$('mixture-list').children.length;
  for(const id of ['image-file','demo-image','example-button','reset-button','import-button','history-button','material'])$(id).disabled=value;
  $('analyse-button').disabled=value||!currentImage;$('refine-button').disabled=value||!currentImage;
  $('z-range').disabled=value||!simulatedInWorker||!result||fieldView==='input';
}
async function withTask(message,job){
  if(busy)return;
  $('toast').hidden=true;$('task-message').textContent=message;$('task-progress').value=0;
  $('task-elapsed').textContent='You can continue inspecting results';setBusy(true);
  const start=Date.now();taskClock=setInterval(()=>$('task-elapsed').textContent=`${format((Date.now()-start)/1000,0)} s · results remain available; Stop cancels the current calculation`,1000);
  try{await job();}catch(e){if(e.name!=='AbortError')toast(e.message||'The operation could not be completed.');}
  finally{clearInterval(taskClock);setBusy(false);}
}
$('stop-button').onclick=()=>{
  worker?.terminate();worker=null;simulatedInWorker=false;imageInWorker=false;
  const error=new DOMException('Calculation stopped','AbortError');
  for(const task of pending.values())task.reject(error);pending.clear();
  $('slice-help').textContent='Calculation stopped. Run the simulation again to inspect new sections.';
  toast('Stopped. Previously calculated results remain on screen.');
};

function setForm(values){
  for(const [key,value] of Object.entries(DEFAULTS)){
    const el=form.elements.namedItem(key);const v=values[key]??value;
    // Imported valid intermediate grids remain editable, without silently replacing them.
    if(el.tagName==='SELECT' && ![...el.options].some(o=>o.value===String(v))){
      const option=new Option(String(v),String(v));el.add(option);
    }
    el.value=String(v);
  }
  updateMaterialLabel();
  drawBeam();
}
function readForm(){
  const data={};for(const [key,value] of Object.entries(DEFAULTS)){
    const raw=form.elements.namedItem(key).value;
    data[key]=typeof value==='number'?Number(raw):raw;
  }return data;
}
function readExp(){
  const data={};for(const el of expForm.elements){if(!el.name)continue;data[el.name]=el.type==='checkbox'?el.checked:Number(el.value);}return data;
}
function updateMaterialLabel(){
  const v=readForm();let key='custom';
  for(const [name,w,er,ei] of [['ag800',800,-31.021,.40948],['ag1000',1000,-50.629,.56924],['ag1500',1500,-120.17,3.067]])
    if(v.wavelength_nm===w&&v.epsilon_real===er&&v.epsilon_imag===ei)key=name;
  $('material').value=key;
}
$('material').onchange=()=>{
  const values={ag800:[800,-31.021,.40948],ag1000:[1000,-50.629,.56924],ag1500:[1500,-120.17,3.067]}[$('material').value];
  if(values) ['wavelength_nm','epsilon_real','epsilon_imag'].forEach((k,i)=>form.elements.namedItem(k).value=values[i]);
  else $('material-details').open=true;
  markDirty();drawBeam();
};
function markDirty(){
  if(!result)return;
  const dirty=JSON.stringify(readForm())!==JSON.stringify(Object.fromEntries(Object.keys(DEFAULTS).map(k=>[k,result.config[k]])));
  $('result-notice').classList.toggle('stale',dirty);
  $('result-context').textContent=dirty?'Settings changed. The previous result is shown; run the simulation to update it.':
    resultSource==='example'?'Reference example · silver, 800 nm · run the simulation to explore sections':
    resultSource==='import'?'Saved calculation loaded · run again to inspect new sections':
    `Calculation complete · ${format(result.metrics.seconds,2)} s · ${result.config.samples} × ${result.config.samples}`;
}
form.addEventListener('input',()=>{updateMaterialLabel();markDirty();});
form.addEventListener('change',markDirty);
$('reset-button').onclick=()=>{setForm(DEFAULTS);markDirty();};
form.addEventListener('submit',e=>{e.preventDefault();if(!form.reportValidity())return;
  const config=readForm();
  withTask('Preparing simulation',async()=>{
    const next=await request('simulate',config);result=next;resultSource='calculated';simulatedInWorker=true;showAll=false;
    renderResult();
    try{await saveRun(result);}catch{toast('Calculation complete, but history could not be saved. Use Save calculation to download the result.');}
  });
});
function renderWarnings(){
  $('simulation-warnings').replaceChildren();
  for(const warning of result.warnings){const p=document.createElement('p');p.className='warning-message';p.textContent=warning;$('simulation-warnings').append(p);}
}
function renderResult(){
  if(!result)return;
  $('metric-coupled').textContent=format(result.metrics.coupled*100,2)+'%';
  $('metric-transmission').textContent=format(result.metrics.transmission*100,2)+'%';
  $('metric-residual').textContent=result.metrics.residual<.0001?'< 0.01%':format(result.metrics.residual*100,2)+'%';
  $('metric-modes').textContent=result.metrics.physical_modes;
  $('metric-profiles').textContent=`${result.metrics.profiles} profiles · rank ${result.metrics.rank}`;
  $('z-range').max=result.config.length_cm;$('z-range').value=result.field.z_cm??result.config.length_cm;
  $('z-value').textContent=format(Number($('z-range').value),1)+' cm';$('z-max').textContent=format(result.config.length_cm,1)+' cm';
  $('z-range').disabled=busy||!simulatedInWorker||fieldView==='input';
  $('slice-help').textContent=simulatedInWorker?'Move the slider and release it to calculate a new section.':
    'Run the simulation to inspect other longitudinal sections.';
  $('save-button').disabled=false;$('png-button').disabled=false;$('csv-button').disabled=false;
  renderWarnings();markDirty();renderField();renderPower();renderModes();
}
function renderField(){
  if(!result||currentTab!=='simulation')return;
  const field=fieldView==='input'?result.input:result.field,phase=fieldView==='phase';
  heatmap($('field-canvas'),phase?field.phase:field.intensity,field.size,{phase,radius:result.config.diameter_um/2});
  $('field-caption').textContent=phase?`Phase ${field.phase_component||'Ex'} · common carrier removed`:
    fieldView==='input'?'Calculated Gaussian input · intensity / maximum':'Intensity normalized to this section’s maximum';
  $('field-location').textContent=fieldView==='input'?'Input · z = 0':`z = ${format(result.field.z_cm??result.config.length_cm,1)} cm`;
  $('field-hover').textContent='';
}
function renderPower(){if(!result||currentTab!=='simulation')return;lineChart($('power-canvas'),[{x:result.power.z_cm,y:result.power.fraction}],{percent:true,xmax:result.config.length_cm,...powerAxis(result.power.fraction,$('power-scale').value==='detail')});}
$('power-scale').onchange=renderPower;
$('open-mode-lab').onclick=()=>{if(!busy)modeLab.open();};
function renderModes(){
  const rows=result.rows;const body=$('mode-rows');body.replaceChildren();
  for(const row of (showAll?rows:rows.slice(0,10))){
    const tr=document.createElement('tr');
    for(const text of [row.name,format(row.weight*100,3)+'%',format(row.angle_deg,4),format(row.neff,7),format(row.alpha_power_per_m,5)]){
      const td=document.createElement('td');
      if(tr.children.length===0){const button=document.createElement('button');button.className='mode-link';button.textContent=text;button.title='Inspect this mode';button.onclick=()=>inspectMode(row.name,result.config);td.append(button);}else td.textContent=text;
      tr.append(td);
    }
    const td=document.createElement('td'),tag=document.createElement('span');tag.className='tag'+(row.fallback?' warning':'');
    tag.textContent=row.fallback?'Approximation':'Converged';td.append(tag);tr.append(td);body.append(tr);
  }
  $('table-subtitle').textContent=`${rows.length} profiles · ${result.metrics.fallback_count} modes with approximate γ`;
  $('more-modes').hidden=rows.length<=10;$('more-modes').textContent=showAll?'Show fewer':`Show all ${rows.length} profiles`;
  $('dominant-modes').replaceChildren();
  for(const row of rows.slice(0,5)){
    const wrap=document.createElement('div');wrap.className='mode-bar';
    const name=document.createElement('button');name.className='mode-bar-label mode-link';name.textContent=row.name;name.onclick=()=>inspectMode(row.name,result.config);
    const track=document.createElement('div');track.className='bar-track';const bar=document.createElement('div');bar.className='bar-value';bar.style.width=Math.min(100,Math.max(0,row.weight*100))+'%';track.append(bar);
    const weight=document.createElement('span');weight.textContent=format(row.weight*100,1)+'%';wrap.append(name,track,weight);$('dominant-modes').append(wrap);
  }
}
$('more-modes').onclick=()=>{showAll=!showAll;renderModes();};
document.querySelectorAll('[data-view]').forEach(button=>button.onclick=()=>{
  fieldView=button.dataset.view;document.querySelectorAll('[data-view]').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',String(b===button));});
  $('z-range').disabled=busy||!simulatedInWorker||fieldView==='input';renderField();
});
$('z-range').addEventListener('input',()=>$('z-value').textContent=format(Number($('z-range').value),1)+' cm');
$('z-range').addEventListener('change',()=>{
  if(!simulatedInWorker||busy)return;const z=Number($('z-range').value);
  withTask('Calculating transverse section',async()=>{result.field=await request('slice',{z_cm:z});renderField();});
});
$('field-canvas').addEventListener('pointermove',e=>{
  const c=$('field-canvas'),m=c._map;if(!m)return;const r=c.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;
  const ix=Math.floor((x-m.x)/m.w*m.size),iy=m.size-1-Math.floor((y-m.y)/m.h*m.size);
  if(ix<0||iy<0||ix>=m.size||iy>=m.size){$('field-hover').textContent='';return;}
  const v=m.values[iy*m.size+ix];$('field-hover').textContent=v===null?'':
    `x ${format((ix/(m.size-1)*2-1)*m.radius,1)} · y ${format((iy/(m.size-1)*2-1)*m.radius,1)} µm   ${m.phase?'φ':'I / Imax'} ${format(v,4)}`;
});
$('field-canvas').addEventListener('pointerleave',()=>$('field-hover').textContent='');
const modeColumns=[['name','Mode'],['weight','Normalized coefficient weight'],['coefficient_real','Coefficient real'],['coefficient_imag','Coefficient imaginary'],['angle_deg','Angle (deg)'],['neff','Re neff'],['alpha_power_per_m','Power attenuation (1/m)'],['converged','Root converged'],['residual','Root residual'],['fallback','Marcatili fallback']];
$('csv-button').onclick=()=>result&&download('waveguide-modes.csv',csv(result.rows,modeColumns),'text/csv;charset=utf-8');
$('save-button').onclick=()=>result&&download('waveguide-project.json',JSON.stringify(project(result)));
$('png-button').onclick=()=>result&&$('field-canvas').toBlob(blob=>blob&&download(`waveguide-${fieldView}.png`,blob),'image/png');
$('import-button').onclick=()=>$('project-file').click();
$('project-file').onchange=async e=>{
  const file=e.target.files?.[0];if(!file)return;
  try{if(file.size>15*1024**2)throw new Error('Calculation file exceeds 15 MB.');
    const next=validateProject(JSON.parse(await file.text()));result=next;resultSource='import';simulatedInWorker=false;showAll=false;setForm(result.config);renderResult();
  }catch(err){toast(err.message);}finally{e.target.value='';}
};
async function example(){
  try{const r=await fetch('./assets/example.json');if(!r.ok)throw new Error();const next=await r.json();
    result=next;resultSource='example';simulatedInWorker=false;showAll=false;setForm(next.config);renderResult();
  }catch{toast('Could not load the example. Enter parameters and run the simulation.');}
}
$('example-button').onclick=example;

function changeTab(name){
  if(name==='modes'){if(!busy)modeLab.open();return;}
  if(!['simulation','experiment','method','about'].includes(name))return;
  currentTab=name;
  for(const page of document.querySelectorAll('.page')){const selected=page.id===name+'-page';page.hidden=!selected;page.classList.toggle('active',selected);}
  for(const button of document.querySelectorAll('.nav-button')){const selected=button.dataset.tab===name;button.classList.toggle('active',selected);if(selected)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');}
  if(name==='simulation'){renderField();renderPower();drawBeam();}
  if(name==='experiment'){renderImage();renderExperiment();}
}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>changeTab(b.dataset.tab));
$('history-button').onclick=async()=>{
  $('history-list').replaceChildren();$('history-dialog').showModal();
  try{const all=await runs();if(!all.length){const p=document.createElement('p');p.className='help';p.textContent='Your simulations will appear here. The reference example is not added to history.';$('history-list').append(p);}
    for(const run of all){const button=document.createElement('button');button.className='history-entry';
      const text=document.createElement('span');text.textContent=`${format(run.result.config.wavelength_nm,0)} nm · Ø ${format(run.result.config.diameter_um,0)} µm · ${format(run.result.config.theta_deg,2)}°`;
      const small=document.createElement('small');small.textContent=new Date(run.time).toLocaleString('en-US');text.append(small);const value=document.createElement('strong');value.textContent=format(run.result.metrics.transmission*100,2)+'%';button.append(text,value);
      button.onclick=()=>{try{result=validateProject({schema:'waveguide-lab/1',result:run.result});resultSource='import';simulatedInWorker=false;showAll=false;setForm(result.config);changeTab('simulation');renderResult();$('history-dialog').close();}catch(e){toast(e.message);}};$('history-list').append(button);
    }
  }catch{const p=document.createElement('p');p.textContent='Local storage is unavailable. Save calculations as JSON files.';$('history-list').append(p);}
};
$('close-history').onclick=()=>$('history-dialog').close();
$('history-dialog').addEventListener('click',e=>{if(e.target===$('history-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});

function applyImage(data){
  currentImage=data;imageInWorker=true;experiment=null;$('experiment-results').hidden=true;
  for(const [key,value] of Object.entries(data.roi))expForm.elements.namedItem(key).value=value.toFixed(2);
  $('image-name').textContent=data.meta.name+(data.meta.color_note?' · '+data.meta.color_note:'');
  $('image-dimensions').textContent=`${data.meta.width} × ${data.meta.height}`+(data.meta.scale<1?' · resized':'');
  $('image-empty').hidden=true;renderImage();updateScale();
}
function renderImage(){if(currentImage&&currentTab==='experiment')imagePreview($('image-canvas'),currentImage,readExp());}
function updateScale(){const data=readExp();$('pixel-scale').textContent=`Scale: ${format(data.radius_um/data.radius_px,3)} µm/px of the working image`;
  if(experiment){$('fit-note').textContent='ROI or settings changed. Run the analysis again to update the result.';}}
expForm.addEventListener('input',()=>{updateScale();renderImage();});
$('image-file').onchange=async e=>{
  const file=e.target.files?.[0];if(!file)return;
  if(file.size>32*1024**2){toast('File exceeds 32 MB. Reduce image size or frame count.');e.target.value='';return;}
  withTask('Opening image',async()=>{
    const buffer=await file.arrayBuffer();const mode=$('spe-mode').value;
    const data=await request('image',{name:file.name,spe_mode:mode},buffer);
    imageBuffer=buffer;imageName=file.name;imageMode=mode;imageSource='file';applyImage(data);
  });e.target.value='';
};
$('demo-image').onclick=()=>withTask('Preparing synthetic image',async()=>{
  const data=await request('demo_image');imageSource='demo';imageBuffer=null;applyImage(data);
});
async function ensureImage(){
  if(imageInWorker)return;
  if(imageSource==='demo')await request('demo_image');
  else if(imageBuffer)await request('image',{name:imageName,spe_mode:imageMode},imageBuffer);
  else throw new Error('Open the image again.');
  imageInWorker=true;
}
$('image-canvas').onclick=e=>{
  if(!currentImage||busy)return;const m=$('image-canvas')._map;if(!m)return;const r=e.currentTarget.getBoundingClientRect();
  const x=(e.clientX-r.left-m.x)/m.scale,y=(e.clientY-r.top-m.y)/m.scale;
  if(x<0||y<0||x>=m.sourceW||y>=m.sourceH)return;
  if(e.shiftKey){const data=readExp();expForm.elements.namedItem('radius_px').value=Math.max(5,Math.hypot(x-data.center_x,y-data.center_y)).toFixed(2);}
  else{expForm.elements.namedItem('center_x').value=x.toFixed(2);expForm.elements.namedItem('center_y').value=y.toFixed(2);}
  updateScale();renderImage();
};
$('image-canvas').onkeydown=e=>{
  if(!currentImage||busy||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();
  const key=['ArrowLeft','ArrowRight'].includes(e.key)?'center_x':'center_y';const sign=['ArrowLeft','ArrowUp'].includes(e.key)?-1:1;
  const el=expForm.elements.namedItem(key);el.value=Math.max(0,Math.min((key==='center_x'?currentImage.meta.width:currentImage.meta.height)-1,Number(el.value)+sign*(e.shiftKey?10:1))).toFixed(2);
  updateScale();renderImage();
};
$('refine-button').onclick=()=>{
  if(!expForm.reportValidity())return;const data=readExp();
  withTask('Fitting circular wall',async()=>{await ensureImage();const r=await request('refine',data);
    for(const [k,v]of Object.entries(r.roi))expForm.elements.namedItem(k).value=v.toFixed(2);updateScale();renderImage();
    toast(`Circle fitted. Boundary confidence: ${format(r.quality.confidence*100,0)}%. Check its position on the image.`);
  });
};
expForm.onsubmit=e=>{e.preventDefault();if(!expForm.reportValidity()||!currentImage)return;const config=readExp();
  withTask('Comparing image with modal profiles',async()=>{await ensureImage();experiment=await request('analyse',config);renderExperiment();});
};
function renderExperiment(){
  if(!experiment||currentTab!=='experiment')return;const ex=experiment;$('experiment-results').hidden=false;
  $('experiment-summary').textContent=`Visible: ${format(ex.coverage*100,1)}% ROI · ${ex.diagnostics.catalogue_modes} modes · ${format(ex.seconds,1)} s`;
  $('experiment-rows').replaceChildren();for(const row of ex.rows){const tr=document.createElement('tr');
    for(const v of [row.name,format(row.similarity_score,3),format(row.correlation_2d,3),format(row.modal_angle_deg,4),format(row.relative_l2_2d,3)]){const td=document.createElement('td');if(!tr.children.length){const button=document.createElement('button');button.className='mode-link';button.textContent=v;button.onclick=()=>inspectMode(row.name,{...readForm(),diameter_um:ex.config.radius_um*2,wavelength_nm:ex.config.wavelength_nm});td.append(button);}else td.textContent=v;tr.append(td);}$('experiment-rows').append(tr);}
  lineChart($('radial-canvas'),[{x:ex.radial.rho,y:ex.radial.observed},{x:ex.radial.rho,y:ex.radial.best_single,color:'#b66535',dash:true}],{xmax:1,height:240});
  const max=Math.max(1e-12,...ex.predicted.filter(Number.isFinite));
  heatmap($('fit-canvas'),ex.predicted.map(v=>v===null?null:v/max),ex.size,{radius:ex.config.radius_um});
  $('fit-note').textContent=ex.fit?`Coherent fit: relative error ${format(ex.fit.residual,4)}, correlation ${format(ex.fit.correlation,4)}. Residuals from three starts: ${ex.fit.restart_residuals.map(v=>format(v,4)).join(' / ')}. Phases are not uniquely determined.`:
    `Best single mode: ${ex.rows[0].name}. The map shows its intensity; radial profiles are normalized independently.`;
}
$('experiment-export').onclick=()=>experiment&&download('waveguide-experiment.json',JSON.stringify({schema:'waveguide-experiment/1',created_at:new Date().toISOString(),result:experiment}));

let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{renderField();renderPower();renderImage();renderExperiment();},120);});
window.addEventListener('error',e=>{if(!previewError){previewError=true;toast('Interface error: '+e.message+'. Reload the page; saved calculations remain in history.');}});
drawBeam=setupBeamPreview(form,readForm,markDirty);
setForm(DEFAULTS);setBusy(false);example();
fetch('./assets/references.json').then(r=>{if(!r.ok)throw new Error();return r.json();}).then(refs=>{
  for(const ref of refs){const item=document.createElement('li'),link=document.createElement('a'),meta=document.createElement('small'),note=document.createElement('p');link.textContent=ref.title;link.href=ref.url;link.target='_blank';link.rel='noopener';meta.textContent=ref.citation;note.textContent=ref.role;item.append(link,meta,note);$('reference-list').append(item);}
}).catch(()=>{$('reference-list').textContent='References are also listed in the full theory document.';});

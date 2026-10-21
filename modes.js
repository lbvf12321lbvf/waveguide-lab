import {heatmap} from './charts.js';
import {format,download} from './utils.js';

export function setupModeLab({request,withTask,readForm}){
  const dialog=document.createElement('dialog');dialog.id='mode-dialog';dialog.className='mode-dialog';
  dialog.setAttribute('aria-labelledby','mode-title');
  dialog.innerHTML=`<div class="card-heading"><div><h2 id="mode-title">Mode lab</h2><span class="small-muted">Inspect a single mode or build a coherent vector sum.</span></div><button id="close-mode-lab" class="icon-button" aria-label="Close mode lab">×</button></div>
  <div class="lab-layout"><div class="lab-controls"><form id="mode-form">
  <div class="mode-inputs"><label>Family<select name="family"><option>HE</option><option>EH</option><option>TE</option><option>TM</option></select></label><label>Index n<input name="n" type="number" min="1" max="30" step="1" value="1" required></label><label>Index m<input name="m" type="number" min="1" max="60" step="1" value="1" required></label><label>Orientation<select name="orientation"><option value="c">c</option><option value="s">s</option></select></label></div>
  <p class="help">n: azimuthal index; m: radial root. TE and TM use n = 0. c/s are the two vector orientations, not separate radial modes.</p>
  <div class="lab-buttons"><button class="button primary" type="submit">View mode</button><button id="add-mode" type="button" class="button secondary">Add to sum</button></div>
  <details class="advanced"><summary>Waveguide and resolution</summary><div class="fields-two"><label>Wavelength, nm<input name="wavelength_nm" type="number" min="350" max="2000" step="any" required></label><label>Diameter, µm<input name="diameter_um" type="number" min="10" max="1000" step="any" required></label><label>Re ε<input name="epsilon_real" type="number" min="-1000" max="-0.1" step="any" required></label><label>Im ε<input name="epsilon_imag" type="number" min="0.00001" max="1000" step="any" required></label></div><label>Grid<select name="samples"><option value="96">96 × 96</option><option value="128" selected>128 × 128</option><option value="192">192 × 192</option><option value="256">256 × 256</option></select></label><p class="help">Initialized from the simulation settings. Changing these fields only affects this window.</p></details>
  <label style="margin-top:14px">Propagation distance z, cm<input name="z_cm" type="number" min="0" max="200" step="any" value="0" required></label>
  </form><div class="card-heading" style="padding-left:0;padding-right:0"><h2>Coherent sum <span id="mixture-count">0 / 12</span></h2><button id="clear-mixture" class="text-button">Clear</button></div><p class="help">Each profile has unit power at z = 0. Set field amplitudes and relative phases; the vector fields are added before taking intensity.</p><div id="mixture-list" class="mode-mixture"></div><div class="lab-buttons"><button id="calculate-mixture" class="button primary" disabled>Build sum</button></div><p id="mode-status" class="lab-status" role="status"></p></div>
  <div class="lab-output"><div class="card-heading"><strong id="mode-output-title">Modal field</strong><div class="segmented" aria-label="Mode lab field view"><button data-lab-view="intensity" class="selected" aria-pressed="true">Intensity</button><button data-lab-view="phase" aria-pressed="false">Phase</button></div></div><div id="mode-empty" class="lab-empty">Enter mode indices and select View mode.</div><canvas id="mode-canvas" role="img" aria-label="Selected mode or coherent sum" hidden></canvas><div id="mode-readout" class="lab-readout"></div><p id="mode-normalization" class="help"></p><div class="lab-buttons" style="padding:0 12px"><button id="mode-png" class="button secondary" disabled>Download PNG</button><button id="mode-json" class="button secondary" disabled>Export JSON</button></div></div></div>`;
  document.body.append(dialog);
  const $=id=>document.getElementById(id),form=$('mode-form');
  let terms=[],output=null,view='intensity',lastPayload=null,lastTitle='';
  const value=name=>form.elements.namedItem(name).value;
  function geometry(){return Object.fromEntries(['wavelength_nm','diameter_um','epsilon_real','epsilon_imag','samples','z_cm'].map(k=>[k,Number(value(k))]));}
  function selected(){return {family:value('family'),n:Number(value('n')),m:Number(value('m')),orientation:['TE','TM'].includes(value('family'))?'':value('orientation'),amplitude:1,phase_deg:0};}
  const name=t=>`${t.family}_${t.n},${t.m}${t.orientation}`;
  function stale(){if(output)$('mode-status').textContent='Settings changed. Select View mode or Build sum to update the field.';}
  function family(){const pure=['TE','TM'].includes(value('family')),n=form.elements.namedItem('n');n.min=pure?'0':'1';n.max=pure?'0':'30';if(pure)n.value='0';else if(Number(n.value)===0)n.value='1';form.elements.namedItem('orientation').value=pure?'c':value('orientation');stale();}
  form.elements.namedItem('family').onchange=family;
  form.oninput=stale;
  function draw(){
    if(!output||!dialog.open)return;
    $('mode-canvas').hidden=false;$('mode-empty').hidden=true;
    heatmap($('mode-canvas'),view==='phase'?output.field.phase:output.field.intensity,output.field.size,{phase:view==='phase',radius:lastPayload.diameter_um/2});
    $('mode-normalization').textContent=output.cancelled?'The selected terms cancel at this section. Intensity is zero; phase is undefined.':view==='phase'?`Phase of ${output.field.phase_component}; common carrier removed.`:'Intensity is normalized to the maximum of this section. The readout below retains the integrated power.';
  }
  function renderTerms(){
    $('mixture-count').textContent=`${terms.length} / 12`;$('calculate-mixture').disabled=!terms.length;$('mixture-list').replaceChildren();
    terms.forEach((term,index)=>{
      const row=document.createElement('div');row.className='mixture-row';
      const label=document.createElement('strong');label.textContent=name(term);row.append(label);
      for(const [key,title,min,max] of [['amplitude','Amplitude',0,1000],['phase_deg','Phase, °',-36000,36000]]){
        const lab=document.createElement('label');lab.textContent=title;const input=document.createElement('input');input.type='number';input.min=min;input.max=max;input.step='any';input.required=true;input.value=term[key];input.setAttribute('aria-label',`${title} for term ${index+1} ${name(term)}`);
        input.oninput=()=>{term[key]=input.value===''?NaN:Number(input.value);stale();};lab.append(input);row.append(lab);
      }
      const remove=document.createElement('button');remove.className='icon-button';remove.textContent='×';remove.setAttribute('aria-label',`Remove term ${index+1} ${name(term)}`);remove.onclick=()=>{terms.splice(index,1);renderTerms();stale();};row.append(remove);$('mixture-list').append(row);
    });
  }
  async function calculate(items,title){
    if(!form.reportValidity())return;
    for(const input of $('mixture-list').querySelectorAll('input'))if(!input.reportValidity())return;
    const payload={...geometry(),terms:structuredClone(items)};
    await withTask('Building modal field',async()=>{
      const next=await request('mode_lab',payload);output=next;lastPayload=payload;lastTitle=title;
      $('mode-output-title').textContent=title;$('mode-png').disabled=false;$('mode-json').disabled=false;
      const lines=next.rows.map(r=>`${r.name}  u = ${format(r.u,5)}  Re n_eff = ${format(r.neff,7)}  α = ${format(r.alpha_power_per_m,5)} m⁻¹${r.fallback?' [approximation]':''}`);
      lines.push(`P(z) = ${format(next.power,6)} · P(0) = ${format(next.initial_power,6)} [relative units]`);
      if(next.power_ratio!==null)lines.push(`P(z) / P(0) = ${format(next.power_ratio*100,4)}%`);
      $('mode-readout').replaceChildren(...lines.map(t=>{const div=document.createElement('div');div.textContent=t;return div;}));
      $('mode-status').textContent=`${items.length} profile${items.length===1?'':'s'} · ${payload.wavelength_nm} nm · Ø ${payload.diameter_um} µm · z = ${payload.z_cm} cm`+(next.rows.some(r=>r.fallback)?' · Some roots use a Marcatili approximation.':'');
      draw();
    });
  }
  form.onsubmit=e=>{e.preventDefault();calculate([selected()],name(selected()));};
  $('add-mode').onclick=()=>{if(!form.reportValidity())return;if(terms.length>=12){$('mode-status').textContent='The mixture is limited to 12 profiles.';return;}terms.push(selected());renderTerms();stale();};
  $('calculate-mixture').onclick=()=>calculate(terms,`Coherent sum · ${terms.length} profiles`);
  $('clear-mixture').onclick=()=>{terms=[];renderTerms();stale();};
  $('close-mode-lab').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{document.body.append($('task-panel'),$('toast'));});
  dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
  dialog.querySelectorAll('[data-lab-view]').forEach(button=>button.onclick=()=>{view=button.dataset.labView;dialog.querySelectorAll('[data-lab-view]').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',String(b===button));});draw();});
  $('mode-png').onclick=()=>$('mode-canvas').toBlob(blob=>blob&&download('waveguide-mode.png',blob),'image/png');
  $('mode-json').onclick=()=>lastPayload&&download('waveguide-mixture.json',JSON.stringify({schema:'waveguide-mixture/1',title:lastTitle,config:lastPayload,result:output}));
  window.addEventListener('resize',draw);
  function open(profile=null,config=null){
    if(!dialog.open){const cfg=config||readForm();for(const key of ['wavelength_nm','diameter_um','epsilon_real','epsilon_imag'])form.elements.namedItem(key).value=cfg[key];dialog.append($('task-panel'),$('toast'));dialog.showModal();}
    if(profile){for(const key of ['family','n','m','orientation'])if(profile[key]!==undefined)form.elements.namedItem(key).value=profile[key]||'c';family();calculate([selected()],name(selected()));}
    else {draw();if(output&&Object.entries(geometry()).some(([k,v])=>v!==lastPayload[k]))stale();}
  }
  return {open};
}

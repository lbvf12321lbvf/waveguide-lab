import {PRESET_COLORS} from './palettes.js';
const FIGURE=['#ffffff','#ff0000','#ffff00','#00ff00','#0000ff'];
export function sourceColorAt(rgb,width,height,x,y){
  x=Math.round(x);y=Math.round(y);
  if(!rgb||x<0||y<0||x>=width||y>=height)return null;
  const i=(y*width+x)*3;
  return '#'+[rgb[i],rgb[i+1],rgb[i+2]].map(v=>v.toString(16).padStart(2,'0')).join('');
}
export function setupPaletteEditor({getImage,isBusy,onChange,onApply,onPickChange}){
  const $=id=>document.getElementById(id);
  let stops=FIGURE.map((color,i)=>({color,intensity:i/4})),picking=null,applied='';
  function read(){return {source_palette:$('source-palette').value,palette_reverse:$('palette-reverse').checked,
    palette_interpolation:$('palette-interpolation').value,palette_stops:stops.map(s=>({...s}))};}
  function preview(){
    const name=$('source-palette').value;
    let colors=name==='custom'?[...stops].sort((a,b)=>a.intensity-b.intensity).map(s=>s.color):
      name==='figure'?FIGURE:name==='four_color'?['#ffffff','#ffff00','#ff0000','#008000']:
      PRESET_COLORS[name]||['#000000','#ffffff'];
    if(name==='custom'){
      colors=stops.filter(s=>/^#[0-9a-fA-F]{6}$/.test(s.color)&&Number.isFinite(s.intensity))
        .map(s=>({color:s.color,intensity:$('palette-reverse').checked?1-s.intensity:s.intensity}))
        .sort((a,b)=>a.intensity-b.intensity).map(s=>s.color+' '+s.intensity*100+'%');
    }else if($('palette-reverse').checked)colors=[...colors].reverse();
    $('palette-preview').style.background='linear-gradient(to right,'+colors.join(',')+')';
  }
  function changed(){picking=null;update();onChange();onPickChange();}
  function render(){
    const container=$('palette-stops');container.replaceChildren();
    stops.forEach((s,i)=>{
      const row=document.createElement('div');row.className='palette-stop';
      const swatch=document.createElement('input');swatch.type='color';swatch.value=s.color;swatch.setAttribute('aria-label','Choose color '+(i+1));
      const hex=document.createElement('input');hex.type='text';hex.value=s.color;hex.pattern='#[0-9a-fA-F]{6}';hex.maxLength=7;hex.required=true;
      hex.setAttribute('aria-label','Color '+(i+1)+' hex');
      const level=document.createElement('input');level.type='number';level.min=0;level.max=1;level.step='any';level.value=s.intensity;level.required=true;
      level.setAttribute('aria-label','Color '+(i+1)+' intensity');
      const pick=document.createElement('button');pick.type='button';pick.className='text-button';pick.textContent='Pick';
      pick.setAttribute('aria-label','Pick color '+(i+1)+' from image');
      const remove=document.createElement('button');remove.type='button';remove.className='icon-button';remove.textContent='×';
      remove.setAttribute('aria-label','Remove color '+(i+1));
      swatch.oninput=()=>{s.color=swatch.value;hex.value=s.color;changed();};
      hex.oninput=()=>{s.color=hex.value;if(/^#[0-9a-fA-F]{6}$/.test(s.color))swatch.value=s.color;changed();};
      level.oninput=()=>{s.intensity=Number(level.value);changed();};
      pick.onclick=()=>{picking=i;$('image-view').value='source';update();onPickChange();$('image-canvas').scrollIntoView({block:'center',behavior:'smooth'});};
      remove.onclick=()=>{if(stops.length>2){stops.splice(i,1);render();changed();}};
      row.append(swatch,hex,level,pick,remove);container.append(row);
    });update();
  }
  function update(){
    const hasColor=!!getImage()?.meta.color_source,custom=$('source-palette').value==='custom';
    $('palette-custom').hidden=!custom;
    for(const el of $('palette-controls').querySelectorAll('input,select,button'))el.disabled=isBusy()||!hasColor;
    for(const el of $('palette-custom').querySelectorAll('input,select,button'))el.disabled=isBusy()||!hasColor||!custom;
    $('add-palette-stop').disabled=isBusy()||!hasColor||stops.length>=16;
    [...$('palette-stops').querySelectorAll('.icon-button')].forEach(b=>b.disabled=isBusy()||!hasColor||stops.length<=2);
    $('apply-palette').disabled=isBusy()||!hasColor;
    $('cancel-color-pick').hidden=picking===null;
    $('image-view').disabled=!hasColor;
    preview();
    const d=getImage()?.palette_diagnostics;
    $('palette-status').textContent=!getImage()?'Load an image to configure its source color scale.':!hasColor?
      'Native monochrome intensities are preserved; color decoding is unnecessary.':
      picking!==null?'Click the original image to sample color '+(picking+1)+'.':
      applied!==JSON.stringify(read())?'Scale changed. Apply it to update the intensity preview; analysis will apply it automatically.':
      $('source-palette').value==='luminance'?'RGB brightness makes white the maximum. For false-color images, choose their source scale.':
      ($('source-palette').value==='figure'&&!$('palette-reverse').checked?'Scale applied: white = 0.':'Source scale applied.')+
      (d?.p95_palette_distance!=null?' Full-image RGB mismatch p95: '+d.p95_palette_distance.toFixed(3)+'.':'');
  }
  for(const id of ['source-palette','palette-reverse','palette-interpolation'])$(id).onchange=changed;
  $('add-palette-stop').onclick=()=>{
    const levels=[...new Set([0,1,...stops.map(s=>s.intensity).filter(Number.isFinite)])].sort((a,b)=>a-b);
    let interval=0;for(let i=1;i<levels.length-1;i++)if(levels[i+1]-levels[i]>levels[interval+1]-levels[interval])interval=i;
    let rgb=0x808080;while(stops.some(s=>s.color==='#'+rgb.toString(16).padStart(6,'0')))rgb++;
    stops.push({color:'#'+rgb.toString(16).padStart(6,'0'),intensity:(levels[interval]+levels[interval+1])/2});render();changed();
  };
  $('apply-palette').onclick=()=>onApply();
  $('cancel-color-pick').onclick=()=>{picking=null;update();onPickChange();};
  $('image-canvas').addEventListener('keydown',e=>{if(e.key==='Escape'&&picking!==null){picking=null;update();onPickChange();}});
  $('image-view').onchange=()=>onPickChange();
  render();
  return {read,update,isPicking:()=>picking!==null,dirty:()=>applied!==JSON.stringify(read()),
    applied(){applied=JSON.stringify(read());picking=null;update();},
    resetView(){picking=null;$('image-view').value=getImage()?.meta.color_source?'source':'intensity';},
    pick(e,canvas){
      if(picking===null)return false;
      const data=getImage(),m=canvas._map,r=canvas.getBoundingClientRect();
      const color=sourceColorAt(data.rgb,data.meta.width,data.meta.height,(e.clientX-r.left-m.x)/m.scale,(e.clientY-r.top-m.y)/m.scale);
      if(color){stops[picking].color=color;picking=null;render();changed();}
      return true;
    }};
}

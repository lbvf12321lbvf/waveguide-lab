import {heatmap} from './charts.js';
import {format} from './utils.js';

export function setupBeamPreview(form,readForm,changed){
  const canvas=document.getElementById('beam-canvas');let dragging=false;
  function draw(){
    if(!canvas.clientWidth)return;
    const d=readForm(),a=d.diameter_um/2,w=d.waist_um;
    if(!Number.isFinite(a)||a<=0||!Number.isFinite(w)||w<=0)return;
    const angle=d.offset_azimuth_deg*Math.PI/180,cx=d.offset_um*Math.cos(angle),cy=d.offset_um*Math.sin(angle),size=96,values=[];
    for(let iy=0;iy<size;iy++)for(let ix=0;ix<size;ix++){
      const x=(ix/(size-1)*2-1)*a,y=(iy/(size-1)*2-1)*a;
      values.push(x*x+y*y>a*a?null:Math.exp(-2*((x-cx)**2+(y-cy)**2)/(w*w)));
    }
    heatmap(canvas,values,size,{radius:a,height:240});
    const map=canvas._map,ctx=canvas.getContext('2d'),x=map.x+(cx/a+1)*map.w/2,y=map.y+(1-cy/a)*map.h/2;
    ctx.strokeStyle='#f2f5fa';ctx.lineWidth=1;ctx.beginPath();ctx.arc(x,y,5,0,2*Math.PI);ctx.moveTo(x-9,y);ctx.lineTo(x+9,y);ctx.moveTo(x,y-9);ctx.lineTo(x,y+9);ctx.stroke();
    document.getElementById('beam-position').textContent=`x ${format(cx,1)}, y ${format(cy,1)} µm`;
  }
  function move(x,y){
    const d=readForm(),a=d.diameter_um/2,r=Math.hypot(x,y),limit=Math.min(a*.98,500);
    if(r>limit){x*=limit/r;y*=limit/r;}
    form.elements.namedItem('offset_um').value=Math.hypot(x,y).toFixed(3);
    form.elements.namedItem('offset_azimuth_deg').value=(Math.atan2(y,x)*180/Math.PI).toFixed(3);
    changed();draw();
  }
  function point(e){const map=canvas._map;if(!map)return;const rect=canvas.getBoundingClientRect();move(((e.clientX-rect.left-map.x)/map.w*2-1)*map.radius,(1-(e.clientY-rect.top-map.y)/map.h*2)*map.radius);}
  canvas.onpointerdown=e=>{if(e.button!==0||form.elements.namedItem('offset_um').disabled)return;e.preventDefault();dragging=true;canvas.setPointerCapture(e.pointerId);point(e);};
  canvas.onpointermove=e=>{if(dragging)point(e);};
  canvas.onpointerup=e=>{dragging=false;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);};
  canvas.onpointercancel=()=>dragging=false;
  canvas.onkeydown=e=>{
    if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)||form.elements.namedItem('offset_um').disabled)return;
    e.preventDefault();const d=readForm(),t=d.offset_azimuth_deg*Math.PI/180,step=e.shiftKey?10:1;
    move(d.offset_um*Math.cos(t)+(e.key==='ArrowRight'?step:e.key==='ArrowLeft'?-step:0),d.offset_um*Math.sin(t)+(e.key==='ArrowUp'?step:e.key==='ArrowDown'?-step:0));
  };
  form.addEventListener('input',draw);form.addEventListener('change',draw);
  window.addEventListener('resize',draw);
  return draw;
}

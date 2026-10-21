import {format} from './utils.js';
import {drawRegion} from './slit.js';
const stops = [[12,23,32],[36,52,110],[45,104,145],[48,160,151],[175,201,94],[250,231,88]];
function rgb(t, phase=false) {
  if (phase) {
    const h=((t%1)+1)%1*6, x=1-Math.abs(h%2-1);
    const a=h<1?[1,x,0]:h<2?[x,1,0]:h<3?[0,1,x]:h<4?[0,x,1]:h<5?[x,0,1]:[1,0,x];
    return a.map(v=>Math.round(52+v*176));
  }
  t=Math.min(1,Math.max(0,t))*(stops.length-1); const i=Math.min(stops.length-2,Math.floor(t)), f=t-i;
  return stops[i].map((v,j)=>Math.round(v*(1-f)+stops[i+1][j]*f));
}
function setup(canvas, height) {
  const width=canvas.clientWidth;
  if (!width) return null;
  const ratio=Math.min(devicePixelRatio||1,2);
  canvas.width=Math.round(width*ratio); canvas.height=Math.round(height*ratio); canvas.style.height=height+'px';
  const ctx=canvas.getContext('2d'); ctx.setTransform(ratio,0,0,ratio,0,0);
  ctx.font='11px system-ui';
  return {ctx,width,height};
}
function bitmap(values, width, height, {phase=false, range=1, invertY=true}={}) {
  const c=document.createElement('canvas');c.width=width;c.height=height;
  const ctx=c.getContext('2d');const img=ctx.createImageData(width,height);
  for(let y=0;y<height;y++) for(let x=0;x<width;x++) {
    const value=values[(invertY?height-1-y:y)*width+x]; const i=(y*width+x)*4;
    const color=value===null||!Number.isFinite(value)?[12,23,32]:rgb(phase?(value+Math.PI)/(2*Math.PI):value/range,phase);
    img.data[i]=color[0];img.data[i+1]=color[1];img.data[i+2]=color[2];img.data[i+3]=255;
  }
  ctx.putImageData(img,0,0);return c;
}
export function heatmap(canvas, values, size, options={}) {
  const height=options.height||Math.min(470, Math.max(290,canvas.clientWidth*.65));
  const s=setup(canvas,height); if(!s)return;
  const {ctx,width}=s; const side=Math.min(width-100,height-64), x=(width-side)/2-14, y=16;
  ctx.fillStyle='#0c1720';ctx.fillRect(0,0,width,height);
  ctx.imageSmoothingEnabled=false;
  ctx.drawImage(bitmap(values,size,size,options),x,y,side,side);
  ctx.strokeStyle='#527478';ctx.lineWidth=.8;ctx.beginPath();ctx.arc(x+side/2,y+side/2,side/2,0,2*Math.PI);ctx.stroke();
  ctx.strokeStyle='#c1d2d336';ctx.setLineDash([3,5]);
  ctx.beginPath();ctx.moveTo(x,y+side/2);ctx.lineTo(x+side,y+side/2);ctx.moveTo(x+side/2,y);ctx.lineTo(x+side/2,y+side);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle='#92aab0';ctx.textAlign='center';
  const radius=options.radius||1;
  for(const t of [-1,0,1]) {ctx.fillText(format(t*radius,0),x+(t+1)*side/2,y+side+20);}
  ctx.fillText('x, µm',x+side/2,y+side+35);
  ctx.textAlign='right';for(const t of [-1,0,1])ctx.fillText(format(t*radius,0),x-9,y+(1-t)*side/2+4);
  const bx=x+side+20;
  for(let i=0;i<120;i++){ctx.fillStyle=`rgb(${rgb(1-i/119,options.phase).join(',')})`;ctx.fillRect(bx,y+side/2-60+i,8,1.5);}
  ctx.textAlign='left';ctx.fillStyle='#b7cacb';ctx.fillText(options.phase?'π':'1',bx+13,y+side/2-53);
  ctx.fillText(options.phase?'−π':'0',bx+13,y+side/2+60);
  canvas._map={x,y,w:side,h:side,size,values,radius,phase:options.phase};
}
export function imagePreview(canvas, data, roi, options={}) {
  const s=setup(canvas,Math.min(490,Math.max(320,canvas.clientWidth*.72)));if(!s)return;
  const {ctx,width,height}=s; const sw=data.meta.width,sh=data.meta.height;
  const scale=Math.min((width-40)/sw,(height-40)/sh),w=sw*scale,h=sh*scale,x=(width-w)/2,y=(height-h)/2;
  ctx.fillStyle='#0c1720';ctx.fillRect(0,0,width,height);ctx.imageSmoothingEnabled=false;
  if(options.source&&data.rgb){
    const c=document.createElement('canvas');c.width=sw;c.height=sh;const cc=c.getContext('2d'),pixels=cc.createImageData(sw,sh);
    for(let i=0;i<sw*sh;i++){pixels.data[i*4]=data.rgb[i*3];pixels.data[i*4+1]=data.rgb[i*3+1];pixels.data[i*4+2]=data.rgb[i*3+2];pixels.data[i*4+3]=255;}
    cc.putImageData(pixels,0,0);ctx.drawImage(c,x,y,w,h);
  }else ctx.drawImage(bitmap(data.pixels,sw,sh,{invertY:false}),x,y,w,h);
  const map={x,y,w,h,sourceW:sw,sourceH:sh,scale};
  drawRegion(ctx,map,roi,options.editing);
  if(roi){ctx.strokeStyle='#e3ffb2';ctx.lineWidth=1.5;ctx.setLineDash([6,4]);ctx.beginPath();
    ctx.arc(x+roi.center_x*scale,y+roi.center_y*scale,roi.radius_px*scale,0,2*Math.PI);ctx.stroke();ctx.setLineDash([]);
    const cx=x+roi.center_x*scale,cy=y+roi.center_y*scale;ctx.beginPath();ctx.moveTo(cx-6,cy);ctx.lineTo(cx+6,cy);ctx.moveTo(cx,cy-6);ctx.lineTo(cx,cy+6);ctx.stroke();}
  canvas._map=map;
}
export function lineChart(canvas, series, options={}) {
  const s=setup(canvas,options.height||170);if(!s)return;
  const {ctx,width,height}=s;const left=options.digits>0?64:49,right=16,top=20,bottom=33,w=width-left-right,h=height-top-bottom;
  ctx.clearRect(0,0,width,height);
  const points=series.flatMap(s=>s.y).filter(Number.isFinite);
  const xmax=options.xmax||Math.max(1,...series.flatMap(s=>s.x));
  const min=options.ymin??0,max=options.ymax??Math.max(1,...points)*1.04;
  ctx.lineWidth=1;ctx.textAlign='right';ctx.fillStyle='#748583';
  const ticks=options.ticks||[min,min+(max-min)/3,min+2*(max-min)/3,max];
  for(const value of ticks){const y=top+h*(max-value)/(max-min);ctx.strokeStyle='#dde3e8';ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(width-right,y);ctx.stroke();
    ctx.fillText(format(value*(options.percent?100:1),options.digits??(options.percent?0:2))+(options.percent?'%':''),left-8,y+4);}
  ctx.textAlign='center';for(let i=0;i<5;i++)ctx.fillText(format(xmax*i/4,1),left+w*i/4,height-13);
  for(const s of series){ctx.strokeStyle=s.color||'#28659a';ctx.lineWidth=2;ctx.setLineDash(s.dash?[4,4]:[]);ctx.beginPath();let on=false;
    for(let i=0;i<s.x.length;i++){const v=s.y[i];if(v===null||!Number.isFinite(v)){on=false;continue;}
      const x=left+s.x[i]/xmax*w,y=top+(max-v)/(max-min)*h;if(on)ctx.lineTo(x,y);else ctx.moveTo(x,y);on=true;}
    ctx.stroke();ctx.setLineDash([]);}
}

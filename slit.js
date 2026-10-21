export function slitGeometry(roi){
  const angle=Number(roi.slit_angle)*Math.PI/180;
  return {x:Number(roi.slit_x),y:Number(roi.slit_y),width:Number(roi.slit_width),
    tx:Math.cos(angle),ty:Math.sin(angle),nx:-Math.sin(angle),ny:Math.cos(angle)};
}
export function insideSlit(x,y,roi){
  if(!roi.slit_enabled)return true;
  const g=slitGeometry(roi);
  return Math.abs((x-g.x)*g.nx+(y-g.y)*g.ny)<=g.width/2;
}
export function drawSlit(ctx,map,roi){
  if(!roi?.slit_enabled)return;
  const g=slitGeometry(roi),s=map.scale,cx=map.x+g.x*s,cy=map.y+g.y*s;
  if(![g.x,g.y,g.width,g.tx].every(Number.isFinite))return;
  const L=Math.hypot(map.w,map.h)*2,half=g.width*s/2;
  const point=(t,n)=>[cx+t*g.tx+n*g.nx,cy+t*g.ty+n*g.ny];
  ctx.save();ctx.beginPath();ctx.rect(map.x,map.y,map.w,map.h);ctx.clip();
  ctx.beginPath();ctx.rect(map.x,map.y,map.w,map.h);
  const corners=[point(-L,-half),point(L,-half),point(L,half),point(-L,half)];
  ctx.moveTo(...corners[0]);for(const p of corners.slice(1))ctx.lineTo(...p);ctx.closePath();
  ctx.fillStyle='#07111cba';ctx.fill('evenodd');
  ctx.strokeStyle='#f0b761';ctx.lineWidth=1.5;
  for(const n of [-half,half]){ctx.beginPath();ctx.moveTo(...point(-L,n));ctx.lineTo(...point(L,n));ctx.stroke();}
  ctx.setLineDash([4,5]);ctx.beginPath();ctx.moveTo(...point(-L,0));ctx.lineTo(...point(L,0));ctx.stroke();ctx.setLineDash([]);
  const arm=Math.max(25,Math.min(80,roi.radius_px*s*.7)),rotate=point(arm,0);
  for(const [kind,p] of [['move',[cx,cy]],['width1',point(0,half)],['width2',point(0,-half)],['rotate',rotate]]){
    ctx.beginPath();ctx.arc(...p,kind==='move'?6:5,0,2*Math.PI);ctx.fillStyle=kind==='rotate'?'#fff':'#f0b761';ctx.fill();ctx.strokeStyle='#2b3440';ctx.stroke();
  }
  ctx.restore();
  map.slit={center:[cx,cy],edges:[point(0,half),point(0,-half)],rotate};
}
export function setupSlitEditor({canvas,form,getImage,isBusy,onChange}){
  const $=id=>document.getElementById(id),field=name=>form.elements.namedItem(name);
  let active=false,drawing=false,drag=null;
  const value=name=>Number(field(name).value);
  function set(name,v){field(name).value=Number(v.toFixed(3));}
  function notify(){onChange();}
  function update(){
    const enabled=field('slit_enabled').checked;
    $('slit-controls').hidden=!enabled;
    for(const el of $('slit-controls').querySelectorAll('input,button'))el.disabled=isBusy()||!enabled;
    $('edit-slit').disabled=isBusy()||!enabled;
    if(!enabled)active=false;
    $('edit-slit').classList.toggle('selected',active);
    $('edit-roi').classList.toggle('selected',!active);
    $('draw-slit').classList.toggle('selected',drawing);
    canvas.style.cursor=enabled&&active?'crosshair':'default';
    $('image-edit-help').textContent=active?
      (drawing?'Drag along the slit to set its centre and angle.':'Drag the centre to move; edge handles change width; the white handle rotates. Arrow keys move the slit.'):
      'Click to set the waveguide centre. Shift + click sets the radius.';
  }
  field('slit_enabled').addEventListener('change',()=>{active=field('slit_enabled').checked;drawing=false;update();notify();});
  $('edit-roi').onclick=()=>{active=false;drawing=false;update();};
  $('edit-slit').onclick=()=>{active=true;drawing=false;update();};
  $('draw-slit').onclick=()=>{active=true;drawing=true;update();};
  for(const [id,angle] of [['slit-horizontal',0],['slit-vertical',90]]){
    $(id).onclick=()=>{set('slit_angle',angle);active=true;drawing=false;update();notify();};
  }
  $('slit-centre').onclick=()=>{set('slit_x',value('center_x'));set('slit_y',value('center_y'));notify();};
  function pixel(e){
    const m=canvas._map,r=canvas.getBoundingClientRect();
    if(!m)return null;
    return {x:(e.clientX-r.left-m.x)/m.scale,y:(e.clientY-r.top-m.y)/m.scale,
      sx:e.clientX-r.left,sy:e.clientY-r.top};
  }
  canvas.addEventListener('pointerdown',e=>{
    if(!active||isBusy()||!getImage()||!field('slit_enabled').checked)return;
    const p=pixel(e),m=canvas._map;
    if(!p||p.x<0||p.y<0||p.x>m.sourceW-1||p.y>m.sourceH-1)return;
    e.preventDefault();canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);
    const near=q=>q&&Math.hypot(q[0]-p.sx,q[1]-p.sy)<13;
    const mode=drawing?'draw':near(m.slit?.rotate)?'rotate':m.slit?.edges.some(near)?'width':'move';
    drag={mode,start:p,x:value('slit_x'),y:value('slit_y')};
    if(mode==='move'&&!near(m.slit?.center)){drag.x=p.x;drag.y=p.y;set('slit_x',p.x);set('slit_y',p.y);notify();}
  });
  canvas.addEventListener('pointermove',e=>{
    if(!drag)return;
    const p=pixel(e),m=canvas._map;if(!p)return;
    const clamp=(v,max)=>Math.max(0,Math.min(max-1,v));
    if(drag.mode==='draw'){
      const x=clamp(p.x,m.sourceW),y=clamp(p.y,m.sourceH);
      set('slit_x',(x+drag.start.x)/2);set('slit_y',(y+drag.start.y)/2);
      set('slit_angle',Math.atan2(y-drag.start.y,x-drag.start.x)*180/Math.PI);
    }else if(drag.mode==='move'){
      set('slit_x',clamp(drag.x+p.x-drag.start.x,m.sourceW));set('slit_y',clamp(drag.y+p.y-drag.start.y,m.sourceH));
    }else if(drag.mode==='rotate'){
      set('slit_angle',Math.atan2(p.y-value('slit_y'),p.x-value('slit_x'))*180/Math.PI);
    }else{
      const a=value('slit_angle')*Math.PI/180,d=-(p.x-value('slit_x'))*Math.sin(a)+(p.y-value('slit_y'))*Math.cos(a);
      set('slit_width',Math.min(Math.hypot(m.sourceW,m.sourceH),Math.max(1,2*Math.abs(d))));
    }
    notify();
  });
  for(const name of ['pointerup','pointercancel'])canvas.addEventListener(name,e=>{
    if(!drag)return;drag=null;drawing=false;if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);update();
  });
  canvas.addEventListener('keydown',e=>{
    if(!active||isBusy()||!getImage())return;
    const delta={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[e.key];
    if(!delta)return;e.preventDefault();const step=e.shiftKey?10:1,m=canvas._map;
    set('slit_x',Math.max(0,Math.min(m.sourceW-1,value('slit_x')+delta[0]*step)));
    set('slit_y',Math.max(0,Math.min(m.sourceH-1,value('slit_y')+delta[1]*step)));notify();
  });
  return {update,isActive:()=>active,reset(data){
    field('slit_enabled').checked=false;active=false;drawing=false;drag=null;
    set('slit_x',data.roi.center_x);set('slit_y',data.roi.center_y);set('slit_width',Math.max(5,data.roi.radius_px*.3));set('slit_angle',0);
    field('slit_x').max=data.meta.width-1;field('slit_y').max=data.meta.height-1;
    field('slit_width').max=Math.hypot(data.meta.width,data.meta.height);update();
  }};
}

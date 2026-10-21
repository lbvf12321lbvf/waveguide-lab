export function regionGeometry(roi){
  const a=Number(roi.region_angle)*Math.PI/180;
  return {x:Number(roi.region_x),y:Number(roi.region_y),w:Number(roi.region_width),h:Number(roi.region_height),
    tx:Math.cos(a),ty:Math.sin(a),nx:-Math.sin(a),ny:Math.cos(a)};
}
export function insideRegion(x,y,roi){
  if(!roi.region_enabled)return true;const g=regionGeometry(roi),dx=x-g.x,dy=y-g.y;
  return Math.abs(dx*g.tx+dy*g.ty)<=g.w/2+1e-9&&Math.abs(dx*g.nx+dy*g.ny)<=g.h/2+1e-9;
}
export function drawRegion(ctx,map,roi,editing=true){
  if(!roi?.region_enabled)return;const g=regionGeometry(roi),s=map.scale;
  if(![g.x,g.y,g.w,g.h,g.tx].every(Number.isFinite))return;
  const cx=map.x+g.x*s,cy=map.y+g.y*s;
  const point=(t,n)=>[cx+t*g.tx+n*g.nx,cy+t*g.ty+n*g.ny];
  const corners=[point(-g.w*s/2,-g.h*s/2),point(g.w*s/2,-g.h*s/2),point(g.w*s/2,g.h*s/2),point(-g.w*s/2,g.h*s/2)];
  ctx.save();ctx.beginPath();ctx.rect(map.x,map.y,map.w,map.h);ctx.clip();
  ctx.beginPath();ctx.rect(map.x,map.y,map.w,map.h);ctx.moveTo(...corners[0]);
  for(const p of corners.slice(1))ctx.lineTo(...p);ctx.closePath();
  ctx.fillStyle='#07111cb8';ctx.fill('evenodd');
  ctx.beginPath();ctx.moveTo(...corners[0]);for(const p of corners.slice(1))ctx.lineTo(...p);ctx.closePath();
  ctx.strokeStyle='#f0b761';ctx.lineWidth=1.5;ctx.stroke();
  const handles=[...corners.map(p=>({kind:'corner',p})),
    ...[-1,1].map(t=>({kind:'width',p:point(t*g.w*s/2,0)})),
    ...[-1,1].map(t=>({kind:'height',p:point(0,t*g.h*s/2)}))];
  const top=point(0,-g.h*s/2),rotate=point(0,-g.h*s/2-24);
  if(editing){
    ctx.beginPath();ctx.moveTo(...top);ctx.lineTo(...rotate);ctx.stroke();
    for(const {kind,p}of [...handles,{kind:'move',p:[cx,cy]},{kind:'rotate',p:rotate}]){
      ctx.beginPath();ctx.arc(...p,kind==='move'?6:4.5,0,2*Math.PI);
      ctx.fillStyle=kind==='rotate'?'#fff':'#f0b761';ctx.fill();ctx.strokeStyle='#2b3440';ctx.stroke();
    }
  }
  ctx.restore();map.region={center:[cx,cy],handles,rotate};
}
export function setupRegionEditor({canvas,form,getImage,isBusy,isPicking,onChange}){
  const $=id=>document.getElementById(id),field=name=>form.elements.namedItem(name);
  let active=false,drawing=false,drag=null;
  const value=name=>Number(field(name).value);
  function set(name,v){field(name).value=Number(v.toFixed(3));}
  function update(){
    const enabled=field('region_enabled').checked;
    $('region-controls').hidden=!enabled;
    for(const el of $('region-controls').querySelectorAll('input,button'))el.disabled=isBusy()||!enabled;
    $('edit-region').disabled=isBusy()||!enabled;
    $('draw-region-image').disabled=isBusy()||!getImage();
    if(!enabled)active=false;
    $('edit-region').classList.toggle('selected',active);$('edit-roi').classList.toggle('selected',!active);
    $('draw-region').classList.toggle('selected',drawing);
    canvas.style.cursor=isPicking()||drawing?'crosshair':enabled&&active?'move':'default';
    $('image-edit-help').textContent=isPicking()?'Click the source image to sample a color.':
      active?(drawing?'Drag between opposite corners to select a rectangle.':
      'Drag inside to move, edges or corners to resize, and the white handle to rotate.'):
      'Click to set the waveguide centre. Shift + click sets the radius.';
  }
  field('region_enabled').addEventListener('change',()=>{active=field('region_enabled').checked;drawing=false;update();onChange();});
  $('edit-roi').onclick=()=>{active=false;drawing=false;update();onChange();};
  $('edit-region').onclick=()=>{active=true;drawing=false;update();onChange();};
  for(const id of ['draw-region','draw-region-image'])$(id).onclick=()=>{
    field('region_enabled').checked=true;active=true;drawing=true;update();onChange();
    canvas.scrollIntoView({block:'center',behavior:'smooth'});
  };
  $('region-zero').onclick=()=>{set('region_angle',0);update();onChange();};
  $('region-centre').onclick=()=>{set('region_x',value('center_x'));set('region_y',value('center_y'));onChange();};
  function pixel(e){
    const m=canvas._map,r=canvas.getBoundingClientRect();if(!m)return null;
    return {x:(e.clientX-r.left-m.x)/m.scale,y:(e.clientY-r.top-m.y)/m.scale,sx:e.clientX-r.left,sy:e.clientY-r.top};
  }
  canvas.addEventListener('pointerdown',e=>{
    if(!active||isBusy()||isPicking()||!getImage()||!field('region_enabled').checked)return;
    const p=pixel(e),m=canvas._map;if(!p)return;
    const near=q=>q&&Math.hypot(q[0]-p.sx,q[1]-p.sy)<12;
    const handle=m.region?.handles.find(h=>near(h.p));
    const mode=drawing?'draw':near(m.region?.rotate)?'rotate':handle?.kind||'move';
    if(mode==='draw'&&(p.x<0||p.y<0||p.x>m.sourceW-1||p.y>m.sourceH-1))return;
    if(mode==='move'&&!insideRegion(p.x,p.y,Object.fromEntries(
      ['region_angle','region_x','region_y','region_width','region_height'].map(n=>[n,value(n)]).concat([['region_enabled',true]]))))return;
    e.preventDefault();canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);
    drag={mode,start:p,x:value('region_x'),y:value('region_y')};
  });
  function move(e){
    if(!drag)return;const p=pixel(e),m=canvas._map;if(!p)return;
    const clamp=(v,max)=>Math.max(0,Math.min(max-1,v)),maximum=Math.hypot(m.sourceW,m.sourceH);
    if(drag.mode==='draw'){
      const x=clamp(p.x,m.sourceW),y=clamp(p.y,m.sourceH);
      set('region_x',(x+drag.start.x)/2);set('region_y',(y+drag.start.y)/2);set('region_angle',0);
      set('region_width',Math.max(1,Math.abs(x-drag.start.x)));set('region_height',Math.max(1,Math.abs(y-drag.start.y)));
    }else if(drag.mode==='move'){
      set('region_x',clamp(drag.x+p.x-drag.start.x,m.sourceW));set('region_y',clamp(drag.y+p.y-drag.start.y,m.sourceH));
    }else if(drag.mode==='rotate'){
      let a=Math.atan2(p.y-value('region_y'),p.x-value('region_x'))*180/Math.PI+90;
      if(a>180)a-=360;set('region_angle',a);
    }else{
      const a=value('region_angle')*Math.PI/180,dx=p.x-value('region_x'),dy=p.y-value('region_y');
      if(drag.mode!=='height')set('region_width',Math.min(maximum,Math.max(1,2*Math.abs(dx*Math.cos(a)+dy*Math.sin(a)))));
      if(drag.mode!=='width')set('region_height',Math.min(maximum,Math.max(1,2*Math.abs(-dx*Math.sin(a)+dy*Math.cos(a)))));
    }
    onChange();
  }
  canvas.addEventListener('pointermove',move);
  for(const name of ['pointerup','pointercancel'])canvas.addEventListener(name,e=>{
    if(!drag)return;if(name==='pointerup')move(e);drag=null;drawing=false;
    if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);update();
  });
  canvas.addEventListener('keydown',e=>{
    if(!active||isBusy()||isPicking()||!getImage())return;
    const delta={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[e.key];
    if(!delta)return;e.preventDefault();const step=e.shiftKey?10:1,m=canvas._map;
    set('region_x',Math.max(0,Math.min(m.sourceW-1,value('region_x')+delta[0]*step)));
    set('region_y',Math.max(0,Math.min(m.sourceH-1,value('region_y')+delta[1]*step)));onChange();
  });
  return {update,isActive:()=>active,reset(data){
    field('region_enabled').checked=false;active=false;drawing=false;drag=null;
    set('region_x',data.roi.center_x);set('region_y',data.roi.center_y);
    set('region_width',Math.min(data.meta.width-1,2*data.roi.radius_px));
    set('region_height',Math.min(data.meta.height-1,2*data.roi.radius_px));set('region_angle',0);
    field('region_x').max=data.meta.width-1;field('region_y').max=data.meta.height-1;
    field('region_width').max=field('region_height').max=Math.hypot(data.meta.width,data.meta.height);update();
  }};
}

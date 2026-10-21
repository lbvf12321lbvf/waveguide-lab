import {test} from 'node:test';
import assert from 'node:assert/strict';
import {insideRegion} from '../slit.js';
import {sourceColorAt} from '../palette.js';
const roi={region_enabled:true,region_x:100,region_y:80,region_width:60,region_height:20,region_angle:0};
test('rectangle excludes both side boundaries and finite ends',()=>{
  assert.equal(insideRegion(100,80,roi),true);
  assert.equal(insideRegion(130,90,roi),true);
  assert.equal(insideRegion(131,80,roi),false);
  assert.equal(insideRegion(100,91,roi),false);
  assert.equal(insideRegion(70,70,roi),true);
});
test('rotating a rectangle rotates both pairs of boundaries',()=>{
  const turned={...roi,region_angle:90};
  assert.equal(insideRegion(100,109,turned),true);
  assert.equal(insideRegion(129,80,turned),false);
  const oblique={...roi,region_angle:45};
  assert.equal(insideRegion(120,100,oblique),true);
  assert.equal(insideRegion(125,105,oblique),false);
  assert.equal(insideRegion(120,60,oblique),false);
  assert.equal(insideRegion(0,0,{...roi,region_enabled:false}),true);
});
test('eyedropper reads original RGB pixels and rejects clicks outside the frame',()=>{
  const rgb=new Uint8Array([255,255,255,255,0,0,0,255,0,0,0,255]);
  assert.equal(sourceColorAt(rgb,2,2,0,0),'#ffffff');
  assert.equal(sourceColorAt(rgb,2,2,1,0),'#ff0000');
  assert.equal(sourceColorAt(rgb,2,2,0,1),'#00ff00');
  assert.equal(sourceColorAt(rgb,2,2,-1,0),null);
  assert.equal(sourceColorAt(rgb,2,2,2,0),null);
});

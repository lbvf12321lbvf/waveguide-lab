import {test} from 'node:test';
import assert from 'node:assert/strict';
import {insideSlit} from '../slit.js';
const roi={slit_enabled:true,slit_x:100,slit_y:80,slit_width:20,slit_angle:0};
test('slit retains only the horizontal or vertical band, including its boundary',()=>{
  for(const [x,y,expected] of [[0,80,true],[150,90,true],[100,91,false],[100,69,false]]){
    assert.equal(insideSlit(x,y,roi),expected);
  }
  assert.equal(insideSlit(109,0,{...roi,slit_angle:90}),true);
  assert.equal(insideSlit(111,80,{...roi,slit_angle:90}),false);
});
test('oblique slit follows its translated centre and angle in camera coordinates',()=>{
  const tilted={...roi,slit_angle:45};
  assert.equal(insideSlit(150,130,tilted),true);
  assert.equal(insideSlit(120,60,tilted),false);
  assert.equal(insideSlit(150,130,{...tilted,slit_x:130}),false);
  assert.equal(insideSlit(150,130,{...tilted,slit_angle:-135}),true);
  assert.equal(insideSlit(120,60,{...tilted,slit_enabled:false}),true);
});

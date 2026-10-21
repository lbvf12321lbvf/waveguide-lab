import test from 'node:test';
import assert from 'node:assert/strict';
import {powerAxis} from '../utils.js';
test('ordinary power uses 0 to 100 percent without artificial headroom',()=>{
  const axis=powerAxis([.99999,.9982]);assert.equal(axis.ymin,0);assert.equal(axis.ymax,1);assert.deepEqual(axis.ticks,[0,.2,.4,.6,.8,1]);
});
test('axis never hides computed excess power',()=>{
  for(const values of [[1.02,1.001],[1.5,.4],[2.1,1.1]]){
    const axis=powerAxis(values);assert.equal(axis.ymin,0);assert.ok(axis.ymax>=Math.max(...values));
  }
});
test('detail scale resolves small losses and constant curves',()=>{
  for(const values of [[1,.9982],[.50001,.5],[1,1],[0,0]]){
    const axis=powerAxis(values,true);assert.ok(axis.ymin<=Math.min(...values));assert.ok(axis.ymax>=Math.max(...values));assert.ok(axis.ymax>axis.ymin);assert.ok(axis.ticks.length>=2);
  }
});

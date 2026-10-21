import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {csv,project,validateProject} from '../utils.js';
const result=JSON.parse(await readFile(new URL('../assets/example.json',import.meta.url),'utf8'));
test('exported project round trips without losing numerical values',()=>{
  const restored=validateProject(JSON.parse(JSON.stringify(project(result))));
  assert.deepEqual(restored,result);
});
test('old calculation files retain their manually chosen mode limit',()=>{
  const p=structuredClone(project(result));delete p.result.config.mode_selection;
  p.result.config.max_modes=129;
  const restored=validateProject(p);
  assert.equal(restored.config.mode_selection,'manual');
  assert.equal(restored.config.max_modes,129);
  assert.equal(p.result.config.mode_selection,undefined);
});
test('malformed projects cannot supply HTML or unbounded arrays',()=>{
  for(const change of [p=>p.result.rows[0].name='<img onerror=alert(1)>',
    p=>p.result.field.size=100000, p=>p.result.config.length_cm=NaN,
    p=>p.result.power.fraction=['bad'], p=>p.result.field.intensity[5]='<script>']){
    const p=structuredClone(project(result));change(p);assert.throws(()=>validateProject(p));
  }
});
test('CSV preserves quotes, numbers and neutralizes spreadsheet formulas',()=>{
  const text=csv([{x:'=1+1',y:-1.23},{x:'a"b,c',y:0}],[['x','X'],['y','Y']]);
  assert.ok(text.includes('"\'=1+1"'));assert.ok(text.includes('"-1.23"'));assert.ok(text.includes('"a""b,c"'));
});
test('public entry uses relative assets suitable for a Pages project subpath',async()=>{
  const html=await readFile(new URL('../index.html',import.meta.url),'utf8');
  assert.equal(/(?:src|href)="\/(?!\/)/.test(html),false);
  assert.equal(html.includes('http://localhost'),false);
});

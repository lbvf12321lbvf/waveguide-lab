export const DEFAULTS = Object.freeze({wavelength_nm:800,diameter_um:300,waist_um:45,theta_deg:0,
  azimuth_deg:0,offset_um:0,offset_azimuth_deg:0,polarization:'x',epsilon_real:-31.021,epsilon_imag:.40948,
  mode_selection:'auto',max_modes:32,samples:96,length_cm:40,families:'all'});
export function format(value, digits=2) {
  return Number.isFinite(value) ? value.toLocaleString('en-US',{maximumFractionDigits:digits}) : '—';
}
export function powerAxis(values, detail=false) {
  const finite=values.filter(Number.isFinite), lo=Math.min(0,...finite), hi=Math.max(1,...finite);
  let min=detail&&finite.length?Math.min(...finite):lo;
  let max=detail&&finite.length?Math.max(...finite):hi;
  if(!detail&&min===0&&max<=1)return {ymin:0,ymax:1,ticks:[0,.2,.4,.6,.8,1],digits:0};
  const span=Math.max(max-min,detail?.001:1), target=span/4, exponent=10**Math.floor(Math.log10(target));
  const step=([1,2,2.5,5,10].find(v=>v*exponent>=target)||10)*exponent;
  min=Math.floor((min-span*.05)/step)*step;max=Math.ceil((max+span*.05)/step)*step;
  if(!detail)min=lo<0?Math.min(0,min):0;else min=Math.max(0,min);
  // A curve ending exactly at 100% does not need an artificial 102% label.
  if(hi<=1&&max>1&&min<1)max=1;
  if(max<=min)max=min+step;
  const ticks=[];for(let v=min;v<=max+step*1e-6;v+=step)ticks.push(Number(v.toPrecision(12)));
  if(Math.abs(ticks.at(-1)-max)>step*1e-5)ticks.push(max);
  return {ymin:min,ymax:max,ticks,digits:Math.max(0,-Math.floor(Math.log10(step*100)))};
}
export function csv(rows, columns) {
  const escape = value => {
    let v = value == null ? '' : String(value);
    if (/^[=+@\t\r]/.test(v) || (/^-/.test(v) && !Number.isFinite(Number(v)))) v = "'"+v;
    return '"'+v.replaceAll('"','""')+'"';
  };
  return '\uFEFF'+[columns.map(c=>escape(c[1])).join(','), ...rows.map(row=>columns.map(c=>escape(row[c[0]])).join(','))].join('\r\n');
}
export function fieldShape(field) {
  return field && Number.isInteger(field.size) && field.size >= 16 && field.size <= 256 &&
    ['intensity','phase'].every(key => Array.isArray(field[key]) && field[key].length===field.size**2 &&
      field[key].every(v=>v===null || (typeof v==='number' && Number.isFinite(v))));
}
export function validateProject(p) {
  if (p?.schema !== 'waveguide-lab/1' || !p.result || !p.result.config || !fieldShape(p.result.field) ||
      !fieldShape(p.result.input) || !Array.isArray(p.result.rows) || p.result.rows.length>12000 ||
      !p.result.rows.every(r=>/^(HE|EH|TE|TM)_\d+,\d+[cs]?$/.test(r.name) && typeof r.weight==='number' && Number.isFinite(r.weight)) ||
      !p.result.metrics || !Array.isArray(p.result.warnings) || !p.result.warnings.every(w=>typeof w==='string') ||
      !Array.isArray(p.result.power?.z_cm) || p.result.power.z_cm.length>500 ||
      p.result.power.z_cm.length !== p.result.power.fraction?.length ||
      !p.result.power.z_cm.every(Number.isFinite) || !p.result.power.fraction.every(Number.isFinite)) {
    throw new Error('This is not a valid Waveguide Lab calculation file.');
  }
  const config={...p.result.config,mode_selection:p.result.config.mode_selection??'manual'};
  for (const [key,value] of Object.entries(DEFAULTS)) {
    const v = config[key];
    if (typeof value==='number' ? !Number.isFinite(v) : typeof v!=='string') throw new Error('Invalid calculation parameters.');
  }
  for (const key of ['coupled','transmission','residual','physical_modes','profiles','rank','fallback_count','seconds']) {
    if (!Number.isFinite(p.result.metrics[key]) || p.result.metrics[key]<0) throw new Error('Invalid result metrics.');
  }
  if (!Number.isFinite(p.result.field.z_cm) || p.result.field.z_cm<0 || p.result.field.z_cm>200) throw new Error('Invalid section position.');
  for (const row of p.result.rows) {
    if (['angle_deg','neff','alpha_power_per_m','coefficient_real','coefficient_imag'].some(k=>!Number.isFinite(row[k]))) throw new Error('Invalid modal coefficients.');
  }
  if (p.result.config.length_cm<=0 || p.result.config.length_cm>200) throw new Error('Invalid waveguide length.');
  if(!['auto','manual'].includes(config.mode_selection)||!Number.isInteger(config.max_modes)||config.max_modes<1||config.max_modes>6000)throw new Error('Invalid mode selection settings.');
  return {...p.result,config};
}
export function project(result) { return {schema:'waveguide-lab/1',created_at:new Date().toISOString(),result}; }
export function download(name, data, type='application/json') {
  const blob = data instanceof Blob ? data : new Blob([data],{type});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=name; a.click();
  setTimeout(()=>URL.revokeObjectURL(url), 15000);
}

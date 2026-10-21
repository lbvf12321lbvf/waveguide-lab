export function setupFitBasis({form,isBusy,onChange,onError}){
  const $=id=>document.getElementById(id);let terms=[];
  const method=()=>form.elements.namedItem('fit_mode').value;
  function render(){
    $('fit-basis-list').replaceChildren();
    for(const [index,t] of terms.entries()){
      const row=document.createElement('div');row.className='fit-basis-row';
      const name=document.createElement('span');name.textContent=`${t.family}_${t.n},${t.m} · ${['TE','TM'].includes(t.family)?'single profile':t.orientation==='both'?'c + s':t.orientation}`;
      const button=document.createElement('button');button.type='button';button.className='icon-button';button.textContent='×';
      button.setAttribute('aria-label','Remove '+t.family+'_'+t.n+','+t.m);button.disabled=isBusy();
      button.onclick=()=>{terms.splice(index,1);render();onChange();};
      row.append(name,button);$('fit-basis-list').append(row);
    }
    $('fit-basis-empty').hidden=terms.length>0;
    update();
  }
  function add(term){
    if(terms.length>=6){onError('Use up to 6 physical modes in a selected-mode fit.');return;}
    if(terms.some(t=>t.family===term.family&&t.n===term.n&&t.m===term.m)){onError('That mode is already selected.');return;}
    terms.push({...term});form.elements.namedItem('fit_mode').value='selected';render();onChange();
  }
  function update(){
    const selected=method()==='selected';
    $('fit-basis-controls').hidden=!selected;
    for(const id of ['max_angle','catalogue']){
      form.elements.namedItem(id).disabled=isBusy()||selected;
    }
    form.elements.namedItem('require_center').disabled=isBusy()||selected;
    for(const el of $('fit-basis-controls').querySelectorAll('input,select,button'))el.disabled=isBusy()||!selected;
    const axial=['TE','TM'].includes($('fit-family').value);
    $('fit-n').disabled=isBusy()||!selected||axial;$('fit-n').min=axial?0:1;
    if(axial)$('fit-n').value=0;else if(Number($('fit-n').value)<1)$('fit-n').value=1;
    $('fit-orientation').disabled=isBusy()||!selected||axial;
    $('fit-method-help').textContent=selected?'Fit only the listed modes. No additional modes will be inserted.':
      method()==='auto'?'Fit a coherent mixture of up to four candidate modes.':'Rank individual modes by ring spacing, radial profile and image similarity.';
  }
  $('fit-family').onchange=update;
  $('add-fit-mode').onclick=()=>{
    for(const id of ['fit-n','fit-m'])if(!$(id).reportValidity())return;
    add({family:$('fit-family').value,n:Number($('fit-n').value),m:Number($('fit-m').value),orientation:$('fit-orientation').value});
  };
  form.elements.namedItem('fit_mode').addEventListener('change',()=>{update();onChange();});
  render();
  return {update,terms:()=>terms.map(t=>({...t})),addName(name){
    const m=/^(HE|EH|TE|TM)_(\d+),(\d+)$/.exec(name);
    if(m)add({family:m[1],n:Number(m[2]),m:Number(m[3]),orientation:'both'});
  }};
}

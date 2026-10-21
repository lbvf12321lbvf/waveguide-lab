const chapters=[...document.querySelectorAll('.chapter')],status=document.getElementById('math-status');
if(new URLSearchParams(location.search).has('embedded'))document.body.classList.add('embedded');
let queue=Promise.resolve(),ready;
window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']],displayMath:[['$$','$$']],processEscapes:true,tags:'none'},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']},startup:{typeset:false}};
const script=document.createElement('script');script.src='https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js';script.async=true;
ready=new Promise((resolve,reject)=>{script.onload=()=>window.MathJax.startup.promise.then(resolve,reject);script.onerror=()=>reject(new Error('Formula renderer could not load'));});document.head.append(script);
function typeset(element){queue=queue.then(async()=>{if(element.dataset.math==='done')return;await ready;await window.MathJax.typesetPromise([element]);element.dataset.math='done';status.textContent='';}).catch(()=>{status.textContent='Не удалось загрузить формулы. Проверьте соединение; исходный TeX доступен для скачивания.';});return queue;}
chapters.forEach(chapter=>chapter.addEventListener('toggle',()=>{if(chapter.open)typeset(chapter);}));
function reveal(){const target=document.getElementById(location.hash.slice(1));if(target?.classList.contains('chapter')){target.hidden=false;target.open=true;typeset(target);}}
window.addEventListener('hashchange',reveal);
document.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',()=>{const target=document.getElementById(a.hash.slice(1));target.hidden=false;target.open=true;typeset(target);}));
document.getElementById('expand-all').onclick=()=>{chapters.forEach(c=>{c.hidden=false;c.open=true;typeset(c);});};
document.getElementById('collapse-all').onclick=()=>chapters.forEach(c=>c.open=false);
document.getElementById('chapter-search').oninput=e=>{const query=e.target.value.trim().toLocaleLowerCase();document.querySelectorAll('nav a').forEach(a=>a.hidden=!a.textContent.toLocaleLowerCase().includes(query));};
document.getElementById('print-theory').onclick=async()=>{chapters.forEach(c=>{c.hidden=false;c.open=true;typeset(c);});await queue;window.print();};
ready.then(()=>{chapters.forEach(c=>typeset(c.querySelector('summary')));chapters.filter(c=>c.open).forEach(typeset);}).catch(()=>{status.textContent='Формулы недоступны: проверьте соединение или скачайте исходник.';});
reveal();

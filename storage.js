let database;
function db() {
  if (!database) database = new Promise((resolve,reject)=>{
    const r=indexedDB.open('waveguide-lab',1);
    r.onupgradeneeded=()=>r.result.createObjectStore('runs',{keyPath:'id'});
    r.onsuccess=()=>resolve(r.result); r.onerror=()=>reject(r.error);
  });
  return database;
}
async function transaction(mode, action) {
  const d=await db();
  return new Promise((resolve,reject)=>{
    const t=d.transaction('runs',mode); const request=action(t.objectStore('runs'));
    t.oncomplete=()=>resolve(request?.result); t.onerror=()=>reject(t.error); t.onabort=()=>reject(t.error);
  });
}
export async function runs() {return (await transaction('readonly',s=>s.getAll())).sort((a,b)=>b.time-a.time);}
export async function saveRun(result) {
  const id=crypto.randomUUID();
  await transaction('readwrite',s=>s.put({id,time:Date.now(),result}));
  const all=await runs();
  for (const old of all.slice(12)) await transaction('readwrite',s=>s.delete(old.id));
  return id;
}

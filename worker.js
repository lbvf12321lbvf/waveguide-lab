// A module worker keeps Python / BLAS off the UI thread. Stop terminates it.
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
let runtime;
let loading;
let activeId = null;
let busy = false;
self.report_progress = (fraction, message) => self.postMessage({id:activeId, type:'progress', fraction, message});
async function boot() {
  if (runtime) return runtime;
  if (!loading) loading = (async () => {
    self.report_progress(0, 'Loading calculation engine · first launch may take a minute');
    const {loadPyodide} = await import(PYODIDE + 'pyodide.mjs');
    const py = await loadPyodide({indexURL:PYODIDE, stdout:()=>{}, stderr:()=>{}});
    self.report_progress(.03, 'Loading NumPy, SciPy and image support');
    await py.loadPackage(['numpy', 'scipy', 'pillow']);
    const response = await fetch(new URL('./python-manifest.json', import.meta.url));
    if (!response.ok) throw new Error('Calculation engine manifest not found. Reload the page.');
    const manifest = await response.json();
    await Promise.all(manifest.map(async path => {
      if (!/^python\/[a-z_\/]+\.py$/.test(path)) throw new Error('Invalid module path.');
      const r = await fetch(new URL(path, import.meta.url));
      if (!r.ok) throw new Error('Could not load ' + path);
      const destination = '/app/' + path.slice(7);
      py.FS.mkdirTree(destination.slice(0, destination.lastIndexOf('/')));
      py.FS.writeFile(destination, await r.text());
    }));
    py.runPython('import sys\nsys.path.insert(0, "/app")\nimport json\nimport web_engine\nfrom js import report_progress');
    runtime = py;
    self.postMessage({type:'ready'});
    return py;
  })();
  try {return await loading;} catch(e) {loading = null; throw e;}
}
self.onmessage = async ({data:{id, action, payload, raw}}) => {
  if (busy) {self.postMessage({id, type:'error', message:'A calculation is already running.'}); return;}
  busy = true;
  activeId = id;
  try {
    const py = await boot();
    if (action === 'boot') { self.postMessage({id, type:'result', result:null}); return; }
    py.globals.set('_action', action);
    py.globals.set('_payload', JSON.stringify(payload || {}));
    if (raw) py.FS.writeFile('/input.bin', new Uint8Array(raw));
    py.globals.set('_has_raw', Boolean(raw));
    const result = await py.runPythonAsync(`
_raw = open('/input.bin', 'rb').read() if _has_raw else None
web_engine.dispatch(_action, json.loads(_payload), _raw, report_progress)
`);
    self.postMessage({id, type:'result', result:JSON.parse(result)});
  } catch(e) {
    const text = String(e.message || e);
    const line = text.split('\n').filter(Boolean).at(-1) || text;
    self.postMessage({id, type:'error', message:line.replace(/^(ValueError|RuntimeError|OSError):\s*/, ''), detail:text});
  } finally {
    if (runtime) {
      try {runtime.FS.unlink('/input.bin');} catch {}
      runtime.runPython('_raw = None');
    }
    busy = false; activeId = null;
  }
};

import {mkdir, readdir, copyFile, writeFile, readFile} from 'node:fs/promises';
import {resolve, join, relative} from 'node:path';
import {fileURLToPath} from 'node:url';
const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const out = join(root, 'dist');
await mkdir(out, {recursive: true});
// Explicit publish allowlist: no scientific source data, reports, credentials or history.
const files = ['index.html', 'styles.css', 'app.js', 'worker.js', 'utils.js', 'charts.js', 'storage.js',
               'beam.js','modes.js','theory.html','theory.css','theory.js','assets/theory-original.md',
               'assets/references.json','assets/icon.svg', 'assets/example.json'];
const python = [];
async function walk(dir) {
  for (const e of await readdir(dir, {withFileTypes: true})) {
    if (e.isDirectory() && e.name !== '__pycache__') await walk(join(dir, e.name));
    if (e.isFile() && e.name.endsWith('.py')) python.push(relative(root, join(dir, e.name)).replaceAll('\\', '/'));
  }
}
await walk(join(root, 'python'));
for (const file of [...files, ...python]) {
  const dest = join(out, file);
  await mkdir(resolve(dest, '..'), {recursive: true});
  await copyFile(join(root, file), dest);
}
await writeFile(join(out, 'python-manifest.json'), JSON.stringify(python));
await writeFile(join(out, '.nojekyll'), '');
await writeFile(join(root, 'python-manifest.json'), JSON.stringify(python));
console.log(`Built ${files.length + python.length + 2} public files into ${out}`);

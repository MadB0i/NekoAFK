import { readdir, stat, mkdir, rename, writeFile } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const archive = path.join(root, 'archive');
await mkdir(archive, { recursive: true });
const entries = [];
async function inventory(dir) {
  for (const e of await readdir(dir, { withFileTypes: true })) {
    if (['node_modules', '__pycache__'].includes(e.name)) continue;
    const file = path.join(dir, e.name);
    if (e.isDirectory()) await inventory(file);
    else if (e.isFile()) {
      const hash = createHash('sha256');
      for await (const chunk of createReadStream(file)) hash.update(chunk);
      entries.push({ path: path.relative(root, file).replaceAll('\\', '/'), bytes: (await stat(file)).size, sha256: hash.digest('hex') });
    }
  }
}
for (const [source, target] of [['assets/character', 'character'], ['prototype', 'prototype']]) {
  const from = path.resolve(root, source), to = path.resolve(archive, target);
  if (!from.startsWith(root + path.sep) || !to.startsWith(archive + path.sep)) throw Error('Archive path outside workspace');
  try { await stat(to); console.log(`${target} already archived`); continue; } catch (e) { if (e.code !== 'ENOENT') throw e; }
  await inventory(from);
  await rename(from, to);
}
if (entries.length) await writeFile(path.join(archive, 'inventory.json'), JSON.stringify({ archivedAt: new Date().toISOString(), entries }, null, 2));
console.log(`Safely archived ${entries.length} original files`);

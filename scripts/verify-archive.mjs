import { readFile, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
const root = path.resolve(import.meta.dirname,'..');
const inventory = JSON.parse(await readFile(path.join(root,'archive/inventory.json'),'utf8'));
let checked = 0;
for (const entry of inventory.entries) {
  const relative = entry.path.startsWith('assets/character/') ? 'archive/character/' + entry.path.slice('assets/character/'.length) : entry.path.startsWith('prototype/') ? 'archive/' + entry.path : null;
  if (!relative) throw Error('Unexpected archive inventory path');
  const file = path.resolve(root,relative);
  if (!file.startsWith(path.join(root,'archive')+path.sep)) throw Error('Invalid archive path');
  if ((await stat(file)).size !== entry.bytes) throw Error(`Archive size mismatch: ${relative}`);
  const hash = createHash('sha256'); for await (const chunk of createReadStream(file)) hash.update(chunk);
  if (hash.digest('hex') !== entry.sha256) throw Error(`Archive hash mismatch: ${relative}`);
  checked++;
}
console.log(`${checked} archived source and asset files match their original SHA-256 hashes`);

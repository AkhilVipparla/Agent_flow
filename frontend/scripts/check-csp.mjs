// Fails the build if an inline <script> in the built index.html isn't allowed by the
// Content-Security-Policy in vercel.json. The theme script is inlined (so the page never
// flashes the wrong theme) and allowed by hash; editing it without updating the hash would
// silently break theming in production.
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../dist/index.html', import.meta.url), 'utf8');
const config = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf8'));
const csp = config.headers
  .flatMap((h) => h.headers)
  .find((h) => h.key === 'Content-Security-Policy')?.value ?? '';

const inline = [...html.matchAll(/<script(?![^>]*\ssrc=)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
let failed = false;
for (const body of inline) {
  const hash = `'sha256-${createHash('sha256').update(body).digest('base64')}'`;
  if (!csp.includes(hash)) {
    console.error(`CSP is missing the hash for an inline script. Add this to script-src in vercel.json:\n  ${hash}`);
    failed = true;
  }
}
if (failed) process.exit(1);
console.log(`CSP check: ${inline.length} inline script(s) allowed by hash.`);

import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';

const config=JSON.parse(readFileSync(new URL('../vercel.json',import.meta.url)));
test('API rewrite preserves paths; SPA cannot turn failed API calls into index HTML',()=>{
 const api=config.rewrites[0];assert.equal(api.source,'/api/:path*');
 const upstream=new URL(api.destination.replace(':path*','auth/session'));
 assert.equal(upstream.protocol,'https:');assert.equal(upstream.pathname,'/api/auth/session');
 // An intentionally non-resolving placeholder is allowed before the Render URL exists.
 assert.ok(upstream.hostname.endsWith('.onrender.com')||upstream.hostname.endsWith('.invalid'));
 const spa=new RegExp('^'+config.rewrites[1].source+'$');
 assert.equal(spa.test('/api/auth/login'),false);assert.equal(spa.test('/api'),false);assert.equal(spa.test('/scenario'),true);
 assert.equal(existsSync(new URL('../api/[...path].js',import.meta.url)),false,'No competing serverless API handler');
});
test('Rewritten personal/auth responses disable both browser and CDN caching',()=>{
 const headers=Object.fromEntries(config.headers.find(h=>h.source==='/api/:path*').headers.map(h=>[h.key.toLowerCase(),h.value]));
 assert.match(headers['cache-control'],/no-store/);assert.equal(headers['cdn-cache-control'],'no-store');
 assert.equal(headers['vercel-cdn-cache-control'],'no-store');assert.equal(headers['x-vercel-enable-rewrite-caching'],'0');
 assert.equal(config.outputDirectory,'dist');assert.equal(config.buildCommand,'npm run build');
 const source=readFileSync(new URL('../src/api.ts',import.meta.url),'utf8');
 assert.match(source,/import\.meta\.env\.PROD\s*\?\s*''/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import handler from '../api/[...path].js';

function response(){return {headers:{},code:0,body:null,setHeader(k,v){this.headers[k.toLowerCase()]=v},status(c){this.code=c;return this},json(v){this.body=v;return this},send(v){this.body=v;return this}}}
test('Same-origin proxy forwards session/CSRF, preserves cookie flags and prohibits caching',async()=>{
 const original=global.fetch,backend=process.env.BACKEND_ORIGIN;
 try{
  process.env.BACKEND_ORIGIN='https://test-backend.invalid';let sent;
  global.fetch=async(url,options)=>{sent={url,options};return new Response('{"ok":true}',{status:200,headers:{'content-type':'application/json','set-cookie':'portfolio25_session=opaque; HttpOnly; Secure; SameSite=Lax; Path=/'}})};
  const res=response();await handler({url:'/api/campus?project_id=project-123456abcdef',method:'POST',headers:{cookie:'portfolio25_session=old',origin:'https://frontend.invalid','x-csrf-token':'csrf','authorization':'must-not-forward'},body:{revision:1}},res);
  assert.equal(sent.url,'https://test-backend.invalid/api/campus?project_id=project-123456abcdef');assert.equal(sent.options.headers.cookie,'portfolio25_session=old');assert.equal(sent.options.headers['x-csrf-token'],'csrf');assert.equal(sent.options.headers.authorization,undefined);
  assert.equal(res.headers['cache-control'],'private, no-store');assert.match(res.headers['set-cookie'][0],/HttpOnly; Secure/);assert.equal(res.code,200);
 }finally{global.fetch=original;if(backend===undefined)delete process.env.BACKEND_ORIGIN;else process.env.BACKEND_ORIGIN=backend}
});
test('Proxy refuses missing backend and oversized requests without external calls',async()=>{
 const original=global.fetch,backend=process.env.BACKEND_ORIGIN;let called=false;
 try{global.fetch=async()=>{called=true;throw Error('not expected')};delete process.env.BACKEND_ORIGIN;let res=response();await handler({url:'/api/auth/session',method:'GET',headers:{}},res);assert.equal(res.code,503);
 process.env.BACKEND_ORIGIN='https://test-backend.invalid';res=response();await handler({url:'/api/campus',method:'PUT',headers:{},body:'x'.repeat(2000001)},res);assert.equal(res.code,413);assert.equal(called,false);
 }finally{global.fetch=original;if(backend===undefined)delete process.env.BACKEND_ORIGIN;else process.env.BACKEND_ORIGIN=backend}
});

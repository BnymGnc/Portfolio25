import test from 'node:test';
import assert from 'node:assert/strict';
import {requestAuth} from '../src/authClient.ts';
import {readJsonObject,ServiceError} from '../src/http.ts';
import {PRODUCTION_ORIGIN,requiresProductionOrigin,OriginRejectedError} from '../src/deployment.ts';

const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json'}});

test('Only other Vercel deployment origins require the fixed production URL; Origin failure is distinct from CSRF',async()=>{
 assert.equal(requiresProductionOrigin(PRODUCTION_ORIGIN),false);
 assert.equal(requiresProductionOrigin('http://127.0.0.1:5173'),false);
 assert.equal(requiresProductionOrigin('http://localhost:5173'),false);
 assert.equal(requiresProductionOrigin('https://frontend-8ptsie61m-bunyamins-projects-1705a228.vercel.app'),true);
 assert.equal(requiresProductionOrigin('https://buildingportfolio25.vercel.app.evil.test'),false);
 await assert.rejects(requestAuth('','login',{},'x',async()=>json({detail:'İstek kaynağı izinli değil.'},403)),OriginRejectedError);
 await assert.rejects(requestAuth('','login',{},'x',async()=>json({detail:'Oturum doğrulaması yenilenmeli'},403)),error=>!(error instanceof OriginRejectedError));
});

test('Gateway text, HTML, malformed JSON and misleading success never leak parser or proxy text',async()=>{
 for(const response of [new Response('An error occurred',{status:502}),new Response('<html>Starting</html>',{status:200,headers:{'Content-Type':'text/html'}}),new Response('An error occurred',{status:502,headers:{'Content-Type':'application/json'}}),json({csrf:'x'}),json({user:null,csrf:'x'})]){
  let calls=0;
  await assert.rejects(requestAuth('','register',{email:'qa@example.test'},'x',async()=>{calls++;return response}),error=>{
   assert.ok(error instanceof ServiceError);assert.doesNotMatch(error.message,/Unexpected|An error|<html>|Starting/);return true;
  });
  assert.equal(calls,1,'Uncertain registration must never automatically repeat');
 }
});

test('A failed bootstrap can be explicitly retried and secure auth transport preserves method/CSRF/cookies',async()=>{
 let calls=0;
 const fetcher=async(url,options)=>{
  calls++;assert.equal(url,'/api/auth/session');assert.equal(options.method,'GET');assert.equal(options.credentials,'include');assert.ok(options.signal);
  return calls===1?new Response('An error occurred',{status:503}):json({user:null,csrf:'new-session'});
 };
 await assert.rejects(requestAuth('','session',undefined,'',fetcher),ServiceError);
 assert.equal((await requestAuth('','session',undefined,'',fetcher)).csrf,'new-session');assert.equal(calls,2);
 const user={id:'test-only',email:'qa@example.test',onboarding_version:1};
 const reply=await requestAuth('','login',{email:user.email,password:'test-only'},'new-session',async(url,options)=>{
  assert.equal(url,'/api/auth/login');assert.equal(options.method,'POST');assert.equal(options.headers['X-CSRF-Token'],'new-session');assert.equal(options.credentials,'include');
  return json({user,csrf:'rotated'});
 });
 assert.equal(reply.user.id,user.id);assert.equal(reply.csrf,'rotated');
});

test('JSON validation errors stay useful; failed transport does not retry writes; arrays/null are not sessions',async()=>{
 await assert.rejects(requestAuth('','login',{},'x',async()=>json({detail:'E-posta veya parola geçerli değil.'},401)),/E-posta veya parola/);
 for(const path of ['register','login']){
  let calls=0;
  await assert.rejects(requestAuth('',path,{},'x',async()=>{calls++;throw new TypeError('private transport detail')}),/sonucu doğrulanamadı/);assert.equal(calls,1);
 }
 for(const value of [null,[],{}])await assert.rejects(requestAuth('','session',undefined,'',async()=>json(value)),ServiceError);
 await assert.rejects(readJsonObject(new Response('upstream secret text',{status:200})),error=>!error.message.includes('secret'));
});

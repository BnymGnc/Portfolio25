import test from 'node:test';
import assert from 'node:assert/strict';
import {applyPreferences,readPreferences,getLanguage} from '../src/preferences.ts';
import {t} from '../src/i18n.ts';
import {n,planName} from '../src/format.ts';

test('Language and motion preferences persist without changing project data or names',()=>{
 const saved=new Map([['portfolio25-draft:user:project:scenario','private draft'],['portfolio25-project:user','project-123']]);
 globalThis.localStorage={getItem:key=>saved.get(key)??null,setItem:(key,value)=>saved.set(key,value)};
 globalThis.document={documentElement:{lang:'tr',dataset:{}}};
 applyPreferences({language:'en',reduceMotion:true});
 assert.deepEqual(readPreferences(),{language:'en',reduceMotion:true});
 assert.equal(document.documentElement.lang,'en');assert.equal(document.documentElement.dataset.reduceMotion,'true');
 assert.equal(t('Ayarlar'),'Settings');assert.equal(t('Girdiler değişti; yeniden hesaplayın.'),'Inputs changed; recalculate.');
 assert.equal(t('Kullanıcının özel bina adı'),'Kullanıcının özel bina adı');
 assert.equal(planName({package:'heat_pump',interventions:[]}), 'Heat pump');
 assert.equal(n(1234.5),'1,234.5');
 assert.equal(saved.get('portfolio25-draft:user:project:scenario'),'private draft');
 assert.equal(saved.get('portfolio25-project:user'),'project-123');
 applyPreferences({language:'tr',reduceMotion:false});assert.equal(getLanguage(),'tr');assert.equal(t('Ayarlar'),'Ayarlar');assert.equal(n(1234.5),'1.234,5');
 saved.set('portfolio25-preferences','invalid');assert.equal(readPreferences().language,'tr');
});

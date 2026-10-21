import test from 'node:test';
import assert from 'node:assert/strict';
import {planName} from '../src/format.ts';

test('Investment labels show selected work, existing work and legacy floor interventions distinctly',()=>{
 assert.equal(planName({package:'none',spatial_interventions:['lighting']}),'Aydınlatma');
 assert.equal(planName({package:'none',spatial_interventions:[]}),'Müdahale yok');
 assert.equal(planName({package:'heat_pump',interventions:[{kind:'roof',state:'applied'},{kind:'lighting',state:'excluded'},{kind:'heat_pump',state:'candidate'}]}),'Çatı (mevcut) + Isı pompası');
 assert.equal(planName({package:'none',interventions:[{kind:'lighting',state:'excluded'}]}),'Yeni müdahale yok');
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {isListResponse} from '../src/http.ts';

test('Collection GETs accept arrays while creates, updates and publish require object contracts',()=>{
 for(const path of ['/api/intakes','/api/scenarios/saved','/api/buildings/B01/catalog']){
  assert.equal(isListResponse(path),true);assert.equal(isListResponse(path,'GET'),true);
  for(const method of ['POST','PUT','DELETE'])assert.equal(isListResponse(path,method),false);
 }
 for(const path of ['/api/intakes/options','/api/intakes/csv/preview','/api/intakes/intake-0123456789ab/publish','/api/campus/snapshot','/api/auth/session'])assert.equal(isListResponse(path),false);
});

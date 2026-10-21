import test from 'node:test';
import assert from 'node:assert/strict';
import {noticeVisible,predictionDifference} from '../src/viewState.ts';

test('Saved-input notice disappears for a new calculation, another revision or project',()=>{
 const notice={message:'saved',kind:'saved',projectId:'office',revision:2,calculationId:null};
 assert.equal(noticeVisible(notice,'office',2,null),true);
 assert.equal(noticeVisible(notice,'office',2,'new-calculation'),false);
 assert.equal(noticeVisible(notice,'housing',2,null),false);
 assert.equal(noticeVisible(notice,'office',3,null),false);
 const exported={...notice,kind:'export',calculationId:'calc-a'};
 assert.equal(noticeVisible(exported,'office',2,'calc-a'),true);
 assert.equal(noticeVisible(exported,'office',2,'calc-b'),false);
});
test('ML differences retain large and negative errors without near-zero division',()=>{
 const gas=predictionDifference(118155,47888);
 assert.equal(gas.absolute,70267);assert.ok(gas.relative>146&&gas.relative<147);
 assert.deepEqual(predictionDifference(12,0),{absolute:12,relative:null});
 assert.deepEqual(predictionDifference(12,.5),{absolute:11.5,relative:null});
 assert.deepEqual(predictionDifference(50,100),{absolute:-50,relative:-50});
 assert.deepEqual(predictionDifference(Infinity,100),{absolute:null,relative:null});
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {aiServiceFailure} from '../src/aiPresentation.ts';

test('AI failures preserve quota and validation meaning without exposing raw provider or proxy payloads',()=>{
 assert.match(aiServiceFailure({detail:'LLM kota/kredi sınırına ulaştı.'}),/kullanım limiti/);
 assert.match(aiServiceFailure({detail:'LLM açıklamasındaki kaynak alanı veya sayısal iddia doğrulanamadı; gösterilmedi.'}),/doğrulanamadığı/);
 for(const body of [{detail:'<html>secret upstream failure</html>'},{detail:{token:'private'}},{detail:'Arbitrary proxy response'},{detail:'LLM '+ 'x'.repeat(1200)},{}]){
   const value=aiServiceFailure(body);assert.match(value,/yanıt alınamadı/);assert.doesNotMatch(value,/secret|private|Arbitrary|xxx/);
 }
});

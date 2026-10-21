export interface Notice {message:string;projectId:string;revision:number;calculationId:string|null;kind:'saved'|'export'}
export function noticeVisible(notice:Notice|null,projectId:string|undefined,revision:number|undefined,calculationId:string|null|undefined){
 if(!notice||notice.projectId!==projectId||notice.revision!==revision)return false;
 return notice.kind==='saved'?!calculationId:notice.calculationId===(calculationId??null);
}
// Less than one annual kWh is too small a reference for a useful percentage.
export function predictionDifference(predicted:number,reference:number){
 if(!Number.isFinite(predicted)||!Number.isFinite(reference))return {absolute:null,relative:null};
 return {absolute:predicted-reference,relative:Math.abs(reference)<1?null:100*(predicted-reference)/Math.abs(reference)};
}

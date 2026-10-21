export type Language = 'tr' | 'en';
const key = 'portfolio25-preferences';
export interface Preferences {language:Language;reduceMotion:boolean}
const defaults:Preferences={language:'tr',reduceMotion:false};
export function readPreferences():Preferences{
 try{const value=JSON.parse(localStorage.getItem(key)??'{}');return {language:value.language==='en'?'en':'tr',reduceMotion:value.reduceMotion===true}}catch{return {...defaults}}
}
let current=readPreferences();
export function getLanguage(){return current.language}
export function applyPreferences(value:Preferences){
 current=value;
 if(typeof document!=='undefined'){
  document.documentElement.lang=value.language;
  document.documentElement.dataset.reduceMotion=String(value.reduceMotion);
 }
 try{localStorage.setItem(key,JSON.stringify(value))}catch{/* Preference applies for this session. */}
}

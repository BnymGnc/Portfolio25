import {useEffect,useState,type Dispatch,type SetStateAction} from 'react';
import {getActiveProject,getUserScope} from './api';

const prefix='portfolio25-draft:';
export function draftKey(kind:string){return prefix+getUserScope()+':'+getActiveProject()+':'+kind;}
export function readDraft<T>(kind:string,fallback:T):T{
  try{return JSON.parse(localStorage.getItem(draftKey(kind))??'null')??fallback;}catch{return fallback;}
}
export function storeDraft(kind:string,value:unknown){localStorage.setItem(draftKey(kind),JSON.stringify(value));}
export function clearDraft(kind:string){localStorage.removeItem(draftKey(kind));}
export function clearProjectDrafts(){const projectPrefix=prefix+getUserScope()+':'+getActiveProject()+':';Object.keys(localStorage).filter(k=>k.startsWith(projectPrefix)).forEach(k=>localStorage.removeItem(k));}
export function hasDrafts(){return Object.keys(localStorage).some(k=>k.startsWith(prefix+getUserScope()+':'));}
export function useDraft<T>(kind:string,initial:T):[T,Dispatch<SetStateAction<T>>]{
  const [value,setValue]=useState<T>(()=>readDraft(kind,initial));
  useEffect(()=>{if(JSON.stringify(value)===JSON.stringify(initial))clearDraft(kind);else storeDraft(kind,value)},[value,initial,kind]);
  return [value,setValue];
}

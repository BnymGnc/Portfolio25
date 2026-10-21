import {getLanguage} from './preferences.ts';
import {english} from './locales/en.ts';

// Application-owned interface copy only. User/project names and API source
// narratives are deliberately retained; no network or DOM text rewriting.
export function t(source:string):string{
 return getLanguage()==='en'?(english[source]??source):source;
}
export function tr(en:string,tr:string){return getLanguage()==='en'?en:tr}

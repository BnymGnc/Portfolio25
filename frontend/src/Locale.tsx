import {createContext,useContext,useState,type ReactNode} from 'react';
import {applyPreferences,readPreferences,type Preferences,type Language} from './preferences';

const LocaleContext=createContext<{preferences:Preferences;setPreferences:(value:Preferences)=>void}>({preferences:readPreferences(),setPreferences:()=>{}});
export function LocaleProvider({children}:{children:ReactNode}){
 const [preferences,setValue]=useState(readPreferences);
 function setPreferences(value:Preferences){applyPreferences(value);setValue(value)}
 return <LocaleContext.Provider value={{preferences,setPreferences}}>{children}</LocaleContext.Provider>;
}
export function useLocale(){return useContext(LocaleContext)}
export function LanguageSelect(){
 const {preferences,setPreferences}=useLocale();
 return <label className="language-control"><span>{preferences.language==='tr'?'Dil':'Language'}</span><select aria-label="TR / EN" value={preferences.language} onChange={e=>setPreferences({...preferences,language:e.target.value as Language})}><option value="tr">TR</option><option value="en">EN</option></select></label>;
}

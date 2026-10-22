import {useEffect,useRef} from 'react';
import {themes,type Theme} from './theme';
import {LanguageSelect} from './Locale';
import {t} from './i18n';
import type {Preferences} from './preferences';
import {Icon} from './visuals';

export default function Settings({theme,onTheme,preferences,onPreferences,onClose,onProjectSettings,onSources,onAbout}:{
 theme:Theme;onTheme:(value:Theme)=>void;preferences:Preferences;onPreferences:(value:Preferences)=>void;
 onClose:()=>void;onProjectSettings?:()=>void;onSources?:()=>void;onAbout?:()=>void;
}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{ref.current?.showModal()},[]);
 return <dialog ref={ref} className="settings-dialog" onCancel={onClose} aria-labelledby="settings-title">
  <div className="dialog-top"><h2 id="settings-title">{t('Ayarlar')}</h2><button className="icon-button" aria-label={t('Pencereyi kapat')} onClick={onClose}><Icon name="close"/></button></div>
  <section className="settings-group"><h3>{t('Görünüm ve dil')}</h3><div className="settings-fields"><label>{t('Tema')}<select aria-label={t('Ayarlar teması')} value={theme} onChange={e=>onTheme(e.target.value as Theme)}>{themes.map(theme=><option key={theme.id} value={theme.id}>{t(theme.label)}</option>)}</select></label><LanguageSelect/></div><label className="project-checkbox"><input type="checkbox" checked={preferences.reduceMotion} onChange={e=>onPreferences({...preferences,reduceMotion:e.target.checked})}/>{t('Hareket ve animasyonları azalt')}</label><p>{t('Tercihler bu tarayıcıda otomatik saklanır. Proje girdilerini veya hesabınızı değiştirmez.')}</p></section>
  {onProjectSettings&&<section className="settings-group"><h3>{t('Proje ve hesap varsayımları')}</h3><p>{t('Bütçe, tarifeler, bağlantı grupları ve duyarlılıklar senaryo ekranından yönetilir. Değişiklikler kayıt ve yeniden hesaplama gerektirir.')}</p><div className="settings-links"><button className="button secondary" onClick={onProjectSettings}>{t('Proje ayarlarına git')}<Icon name="arrow" size={16}/></button>{onSources&&<button className="text-button" onClick={onSources}>{t('Kaynak ve varsayımlar')}</button>}</div></section>}
  <p className="settings-note">{t('Arayüz dili değişir; kullanıcı adları, kaynak metinleri ve motorun özgün teknik açıklamaları çevrilmeden korunur. İndirilen karar özeti bu sürümde Türkçedir.')}</p>
  {onAbout&&<button className="text-button" onClick={onAbout}>{t('Uygulama hakkında')}</button>}
  <div className="dialog-actions"><button className="button primary" onClick={onClose}>{t('Tamam')}</button></div>
 </dialog>;
}

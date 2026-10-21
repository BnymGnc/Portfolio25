import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import AuthGate from './AuthGate';
import './styles.css';
import './themes.css';
import './layout.css';
import './account.css';
import {applyTheme, readTheme} from './theme';
import {LocaleProvider} from './Locale';
import {applyPreferences,readPreferences} from './preferences';

applyTheme(readTheme());
applyPreferences(readPreferences());
createRoot(document.getElementById('root')!).render(<StrictMode><LocaleProvider><AuthGate /></LocaleProvider></StrictMode>);

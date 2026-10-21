import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import AuthGate from './AuthGate';
import './styles.css';
import './themes.css';
import './layout.css';
import './account.css';
import {applyTheme, readTheme} from './theme';

applyTheme(readTheme());
createRoot(document.getElementById('root')!).render(<StrictMode><AuthGate /></StrictMode>);

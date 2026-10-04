import React from 'react';
import {createRoot} from 'react-dom/client';
import App from './App';
import {PagesEntry} from './PagesEntry';
import {AuthGate} from './AuthGate';
import './styles.css';
createRoot(document.getElementById('root')!).render(<React.StrictMode>{import.meta.env.MODE==='pages'?<PagesEntry/>:<AuthGate>{hosted=><App hosted={hosted}/>}</AuthGate>}</React.StrictMode>);

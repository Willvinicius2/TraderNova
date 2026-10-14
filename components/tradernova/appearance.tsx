'use client';

import {createContext, useContext, useEffect, useSyncExternalStore} from 'react';
import {ThemeProvider, useTheme} from 'next-themes';
import {Check, Monitor, Moon, Palette, Sun, Zap} from 'lucide-react';
import {Toaster} from 'sonner';
import {RadioGroup, RadioGroupItem} from '@/components/ui/radio-group';
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue} from '@/components/ui/select';
import {DropdownMenu, DropdownMenuContent, DropdownMenuLabel, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuTrigger} from '@/components/ui/dropdown-menu';
import './appearance.css';

type Density = 'comfortable' | 'compact';
const DensityContext = createContext<{density: Density; setDensity: (value: Density) => void}>({density: 'comfortable', setDensity: () => {}});
const densityKey = 'tradernova-density-v1';
const densityListeners = new Set<() => void>();
let densityMemory: Density | null = null;
function readDensity(): Density {
  if (densityMemory) return densityMemory;
  try {return localStorage.getItem(densityKey) === 'compact' ? 'compact' : 'comfortable';} catch { /* Default spacing remains usable if browser storage is unavailable. */ return 'comfortable';}
}
function subscribeDensity(listener: () => void) {
  densityListeners.add(listener);
  window.addEventListener('storage', listener);
  return () => {densityListeners.delete(listener); window.removeEventListener('storage', listener);};
}
const subscribeNothing = () => () => {};
// Browser-only flag: false on the server and during hydration, true afterwards (avoids theme mismatches).
function useMounted() {return useSyncExternalStore(subscribeNothing, () => true, () => false);}
export function AppearanceProvider({children}: {children: React.ReactNode}) {
  const density = useSyncExternalStore(subscribeDensity, readDensity, () => 'comfortable' as Density);
  useEffect(() => {if (density === 'compact') document.documentElement.dataset.density = density;}, [density]);
  function setDensity(value: Density) {
    densityMemory = value;
    document.documentElement.dataset.density = value;
    try {localStorage.setItem(densityKey, value);} catch { /* Keep the session preference. */ }
    densityListeners.forEach(listener => listener());
  }
  return <ThemeProvider attribute="class" defaultTheme="dark" themes={['essential', 'dark', 'light']} enableSystem storageKey="tradernova-theme-v1" disableTransitionOnChange>
    <DensityContext.Provider value={{density, setDensity}}>{children}<ThemeChrome/></DensityContext.Provider>
  </ThemeProvider>;
}
function ThemeChrome() {
  const {resolvedTheme} = useTheme();
  useEffect(() => {
    // Read the same token used by the page; keep browser chrome in sync.
    const color = getComputedStyle(document.documentElement).getPropertyValue('--background').trim();
    document.querySelectorAll('meta[name="theme-color"]').forEach(meta => meta.setAttribute('content', color));
  }, [resolvedTheme]);
  return <Toaster theme={resolvedTheme === 'light' ? 'light' : 'dark'} position="top-right" richColors closeButton/>;
}
const themes = [
  {value: 'essential', title: 'Essencial Dark', description: 'Escuro e verde-esmeralda', Icon: Zap},
  {value: 'dark', title: 'Nova Lab', description: 'Grafite e roxo', Icon: Moon},
  {value: 'light', title: 'Claro & Direto', description: 'Branco e azul', Icon: Sun},
] as const;
export function ThemeToggle() {
  const {theme, setTheme} = useTheme();
  const mounted = useMounted();
  const current = mounted ? themes.find(item => item.value === theme)?.title ?? 'Acompanhar o dispositivo' : '';
  return <DropdownMenu><DropdownMenuTrigger asChild>
    <button className="icon-button theme-toggle" aria-label="Escolher tema" title={current ? `Tema: ${current}` : 'Escolher tema'} disabled={!mounted}><Palette size={19}/></button>
  </DropdownMenuTrigger><DropdownMenuContent align="end" className="theme-menu">
    <DropdownMenuLabel>Aparência</DropdownMenuLabel>
    <DropdownMenuRadioGroup value={mounted ? theme : undefined} onValueChange={setTheme}>
      {themes.map(({value, title, description, Icon}) => <DropdownMenuRadioItem key={value} value={value}><Icon size={17}/><span>{title}<small>{description}</small></span></DropdownMenuRadioItem>)}
      <DropdownMenuSeparator/>
      <DropdownMenuRadioItem value="system"><Monitor size={17}/><span>Acompanhar o dispositivo<small>Claro & Direto ou Nova Lab</small></span></DropdownMenuRadioItem>
    </DropdownMenuRadioGroup>
  </DropdownMenuContent></DropdownMenu>;
}
export function AppearanceSettings() {
  const {theme, setTheme} = useTheme();
  const {density, setDensity} = useContext(DensityContext);
  const mounted = useMounted();
  return <section className="panel padded appearance-panel" aria-labelledby="appearance-title">
    <div className="appearance-heading"><span className="appearance-icon"><Palette size={21}/></span><div><h2 id="appearance-title">Do seu jeito</h2><p>Escolha a aparência do seu TraderNova.</p></div></div>
    <RadioGroup className="theme-options" aria-label="Tema do aplicativo" value={mounted ? theme : undefined} onValueChange={setTheme} disabled={!mounted}>
      {themes.map(({value, title, description, Icon}) => <label key={value} className={`theme-choice ${mounted && theme === value ? 'is-selected' : ''}`}>
        <div className={`theme-sample ${value}`} aria-hidden="true"><div className="sample-top"><span className="sample-brand">N</span><span/><Icon size={13}/></div><div className="sample-content"><span className="sample-line"/><strong>Seu mercado.</strong><div className="sample-cards"><span/><span/></div><div className="sample-action"/></div><div className="sample-nav"><span/><span/><span/><span/></div></div>
        <div className="theme-choice-label"><span><strong>{title}</strong><small>{description}</small></span><RadioGroupItem value={value} aria-label={title}/></div>
      </label>)}
      <label className={`system-choice ${mounted && theme === 'system' ? 'is-selected' : ''}`}><Monitor size={20}/><span><strong>Acompanhar o dispositivo</strong><small>Claro & Direto ou Nova Lab, conforme o dispositivo.</small></span><RadioGroupItem value="system" aria-label="Acompanhar o dispositivo"/></label>
    </RadioGroup>
    <div className="settings-row density-row"><div><h3>Espaçamento</h3><p>Mais respiro ou mais informação na tela.</p></div><Select value={density} onValueChange={value => {if(value === 'comfortable' || value === 'compact') setDensity(value);}}><SelectTrigger className="density-select" aria-label="Espaçamento da interface"><SelectValue/></SelectTrigger><SelectContent><SelectItem value="comfortable">Confortável</SelectItem><SelectItem value="compact">Compacto</SelectItem></SelectContent></Select></div>
    <p className="appearance-saved"><Check size={14}/>Preferências salvas neste navegador.</p>
  </section>;
}

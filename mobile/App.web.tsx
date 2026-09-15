import { useEffect } from 'react';
import { SITE_URL } from './src/site';
export default function App() {
  useEffect(() => { window.location.replace(SITE_URL); }, []);
  return <main><a href={SITE_URL}>Abrir TraderNova</a></main>;
}

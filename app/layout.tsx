import type { Metadata, Viewport } from 'next';
import './globals.css';
export const metadata:Metadata={title:'TraderNova · Seu laboratório de mercado',description:'Mercado, sinais para revisão manual e laboratório de estratégias.',manifest:'/manifest.webmanifest',icons:{icon:'/favicon.svg',shortcut:'/favicon.svg',apple:'/icon-192.png'},appleWebApp:{capable:true,title:'TraderNova',statusBarStyle:'black-translucent'}};
export const viewport:Viewport={width:'device-width',initialScale:1,themeColor:'#0b1014'};
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="pt-BR" className="dark"><body>{children}</body></html>;}

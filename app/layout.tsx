import type { Metadata, Viewport } from 'next';
import './globals.css';
import {AppearanceProvider} from '@/components/tradernova/appearance';
export const metadata:Metadata={title:'TraderNova · Seu laboratório de mercado',description:'Mercado, sinais para revisão manual e laboratório de estratégias.',manifest:'/manifest.webmanifest',icons:{icon:'/favicon.svg',shortcut:'/favicon.svg',apple:'/icon-192.png'},appleWebApp:{capable:true,title:'TraderNova',statusBarStyle:'black-translucent'}};
export const viewport:Viewport={width:'device-width',initialScale:1,viewportFit:'cover',themeColor:'#111117'};
export default function RootLayout({children}:Readonly<{children:React.ReactNode}>){return <html lang="pt-BR" suppressHydrationWarning><body><AppearanceProvider>{children}</AppearanceProvider></body></html>;}

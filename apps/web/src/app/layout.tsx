import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BerryBrain",
  description: "Segundo cerebro local para estudos com IA local.",
  icons: {
    icon: "/berrylogo.png",
  },
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("bb_theme")||"light";var p={light:{bg:"#F7F1E8",fg:"#3E3024",mu:"#7A6A5C",pn:"#FFF9EF",bd:"#E6D8C6"},dark:{bg:"#1a1816",fg:"#e8e4df",mu:"#8b8580",pn:"#252320",bd:"#35312c"},oled:{bg:"#000000",fg:"#d4d4d4",mu:"#555555",pn:"#0a0a0a",bd:"#1a1a1a"},sepia:{bg:"#f8f1e4",fg:"#4a3b2c",mu:"#8b7765",pn:"#fef9f0",bd:"#d6c8b8"},rose:{bg:"#fdf2f3",fg:"#3d2123",mu:"#a07a7d",pn:"#fff8f9",bd:"#eed5d8"},sky:{bg:"#f0f5fb",fg:"#1e3349",mu:"#6a8aa3",pn:"#f8fbfe",bd:"#d4e2f2"},mint:{bg:"#f0f9f3",fg:"#1a3d28",mu:"#5c8a6a",pn:"#f6fcf8",bd:"#c8e6d3"},graphite:{bg:"#f4f4f5",fg:"#1f1f21",mu:"#6b6b6e",pn:"#fafafa",bd:"#e4e4e7"}}[t]||p.light;var a=localStorage.getItem("bb_accent")||"#D98A00";var fs=localStorage.getItem("bb_font_size")||"15";var ef=localStorage.getItem("bb_editor_font_size")||"15";var uf=localStorage.getItem("bb_ui_font")||"inter";var edf=localStorage.getItem("bb_editor_font")||"mono";var ufm={inter:'"Inter",ui-sans-serif,system-ui,sans-serif',system:'ui-sans-serif,system-ui,-apple-system,sans-serif',serif:'"Georgia","Times New Roman",serif',roboto:'"Roboto",ui-sans-serif,system-ui,sans-serif'};var efm={mono:'"JetBrains Mono","Fira Code",ui-monospace,monospace',sans:'ui-sans-serif,system-ui,sans-serif',serif:'"Georgia","Times New Roman",serif'};var r=document.documentElement.style;r.setProperty("--color-background",p.bg);r.setProperty("--color-foreground",p.fg);r.setProperty("--color-muted",p.mu);r.setProperty("--color-panel",p.pn);r.setProperty("--color-border",p.bd);r.setProperty("--color-accent",a);r.setProperty("--font-ui",ufm[uf]||ufm.inter);r.setProperty("--font-editor",efm[edf]||efm.mono);document.body.style.fontSize=fs+"px";document.body.style.fontFamily="var(--font-ui)";}catch(e){}})();`,
          }}
        />
      </head>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}

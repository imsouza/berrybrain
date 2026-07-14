import type { Metadata, Viewport } from "next";
import { DonateLink } from "@/components/donate-link";
import { PwaRegister } from "@/components/pwa-register";
import berrylogo from "../../public/berrylogo.png";
import "./globals.css";

const publicBase = process.env.NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX || "";

export const metadata: Metadata = {
  title: "BerryBrain",
  description: "Local second brain for AI-assisted study.",
  applicationName: "BerryBrain",
  manifest: `${publicBase}/manifest.webmanifest`,
  icons: {
    icon: berrylogo.src,
    apple: `${publicBase}/apple-touch-icon.png`,
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "BerryBrain",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#9EBF61",
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{function c(n){var m=document.cookie.match(new RegExp("(?:^|;\\\\s*)"+n+"=([^;]+)"));return m?decodeURIComponent(m[1]):""}var of=window.fetch;window.fetch=function(i,init){init=init||{};if(init.credentials===undefined)init.credentials="include";var method=(init.method||"GET").toUpperCase();if(method!=="GET"&&method!=="HEAD"&&method!=="OPTIONS"){var token=c("bb_csrf");if(token){var h=new Headers(init.headers||{});if(!h.has("X-CSRF-Token"))h.set("X-CSRF-Token",token);init.headers=h;}}return of(i,init);};}catch(e){}})();`,
          }}
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("bb_theme")||"light";var p={light:{bg:"#F7F6F3",fg:"#1A1A1A",mu:"#6B6B6B",pn:"#FFFFFF",bd:"#E0E0E0"},dark:{bg:"#121212",fg:"#E8E8E8",mu:"#9A9A9A",pn:"#1E1E1E",bd:"#333333"}}[t]||p.light;var fs=localStorage.getItem("bb_font_size")||"15";var uf=localStorage.getItem("bb_ui_font")||"inter";var edf=localStorage.getItem("bb_editor_font")||"mono";var ufm={inter:'"Inter",ui-sans-serif,system-ui,sans-serif',system:'ui-sans-serif,system-ui,-apple-system,sans-serif'};var efm={mono:'"JetBrains Mono","Fira Code",ui-monospace,monospace',sans:'ui-sans-serif,system-ui,sans-serif'};var root=document.documentElement;var r=root.style;root.setAttribute("data-theme",t);root.lang="en";r.setProperty("--color-background",p.bg);r.setProperty("--color-foreground",p.fg);r.setProperty("--color-muted",p.mu);r.setProperty("--color-panel",p.pn);r.setProperty("--color-border",p.bd);r.setProperty("--color-accent","#96B55C");r.setProperty("--color-brand-green","#96B55C");r.setProperty("--color-brand-red","#CC4168");r.setProperty("--color-danger","#CC4168");r.setProperty("--font-ui",ufm[uf]||ufm.inter);r.setProperty("--font-editor",efm[edf]||efm.mono);if(document.body){document.body.style.fontSize=fs+"px";document.body.style.fontFamily="var(--font-ui)";}}catch(e){}})();`,
          }}
        />
      </head>
      <body suppressHydrationWarning>
        <PwaRegister />
        {children}
        <DonateLink />
      </body>
    </html>
  );
}

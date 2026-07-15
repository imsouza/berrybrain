import { NextRequest, NextResponse } from "next/server";

const BERRYBRAIN_PREFIX = "/berrybrain";
const LANDING_ONLY = process.env.NEXT_PUBLIC_BERRYBRAIN_LANDING_ONLY === "true";

function landingRedirect(request: NextRequest, anchor?: string) {
  const url = request.nextUrl.clone();
  url.pathname = "/";
  url.search = "";
  url.hash = anchor ? `#${anchor}` : "";
  return NextResponse.redirect(url, 307);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith(`${BERRYBRAIN_PREFIX}/_next/`)) {
    return NextResponse.next();
  }

  if (pathname === BERRYBRAIN_PREFIX || pathname.startsWith(`${BERRYBRAIN_PREFIX}/`)) {
    const url = request.nextUrl.clone();
    url.pathname = pathname.slice(BERRYBRAIN_PREFIX.length) || "/";
    if (LANDING_ONLY && url.pathname.startsWith("/api/browser-ai/")) {
      return NextResponse.json(
        { error: "The hosted workspace is not available." },
        { status: 404 },
      );
    }
    if (LANDING_ONLY && url.pathname !== "/") {
      return landingRedirect(request, url.pathname === "/brain" ? "download" : undefined);
    }
    return NextResponse.rewrite(url);
  }

  if (LANDING_ONLY && pathname.startsWith("/api/browser-ai/")) {
    return NextResponse.json(
      { error: "The hosted workspace is not available." },
      { status: 404 },
    );
  }

  if (LANDING_ONLY && pathname !== "/") {
    return landingRedirect(request, pathname === "/brain" ? "download" : undefined);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/berrybrain",
    "/berrybrain/:path*",
    "/((?!_next/static|_next/image|favicon.ico|favicon.svg|apple-touch-icon.png|berrylogo.png|berrybrain-print1.png|berrybrain-print2.jpeg|berrybrain-print3.png|sw.js|manifest.webmanifest|offline.html).*)",
  ],
};

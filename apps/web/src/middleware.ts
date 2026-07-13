import { NextRequest, NextResponse } from "next/server";

const BERRYBRAIN_PREFIX = "/berrybrain";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith(`${BERRYBRAIN_PREFIX}/_next/`)) {
    return NextResponse.next();
  }

  if (pathname === BERRYBRAIN_PREFIX || pathname.startsWith(`${BERRYBRAIN_PREFIX}/`)) {
    const url = request.nextUrl.clone();
    url.pathname = pathname.slice(BERRYBRAIN_PREFIX.length) || "/";
    return NextResponse.rewrite(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/berrybrain", "/berrybrain/:path*"],
};

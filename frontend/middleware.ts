import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  // Ambil URL backend dari env var runtime (default: http://localhost:8000)
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

  if (request.nextUrl.pathname.startsWith('/api/')) {
    // Bangun URL baru untuk dituju ke backend
    // Contoh: /api/patients -> BACKEND_URL/api/patients
    const newUrl = new URL(request.nextUrl.pathname, backendUrl)
    newUrl.search = request.nextUrl.search

    return NextResponse.rewrite(newUrl)
  }
}

// Hanya jalankan middleware ini untuk path /api/*
export const config = {
  matcher: ['/api/:path*'],
}

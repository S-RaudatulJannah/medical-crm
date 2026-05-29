/** @type {import('next').NextConfig} */

/**
 * Next.js 15 Configuration - Medical CRM Frontend
 *
 * Fitur Utama:
 * 1. output: 'standalone' → Docker/Kubernetes optimized output
 * 2. rewrites → Proxy /api/* ke backend FastAPI service
 *    BACKEND_URL = server-side env var → bisa diset via Kubernetes ConfigMap
 *
 * Alur Request:
 *   Browser → /api/* → Next.js Server → [BACKEND_URL]/api/* → FastAPI
 */
const nextConfig = {
  output: 'standalone',

  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig

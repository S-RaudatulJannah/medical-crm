import type { Metadata, Viewport } from 'next'
import './globals.css'
import Sidebar from '@/components/Sidebar'

export const metadata: Metadata = {
  title: 'MediCRM | Platform Manajemen Pasien & Rumah Sakit',
  description:
    'Sistem CRM Medis berbasis Kubernetes Microservices untuk manajemen pasien dan rumah sakit. ' +
    'Mendukung SDGs Goal 3: Good Health and Well-being.',
  keywords: [
    'CRM medis', 'manajemen pasien', 'rumah sakit', 'triase otomatis',
    'kubernetes', 'microservices', 'healthcare', 'SDGs Goal 3',
  ],
  authors: [{ name: 'Medical CRM Team' }],
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body className="bg-[#F4F7F5] antialiased">
        <div className="flex min-h-screen">
          {/* Sidebar - Fixed left navigation */}
          <Sidebar />

          {/* Main content area - offset by sidebar width */}
          <main className="flex-1 ml-64 min-h-screen overflow-auto">
            <div className="p-8 max-w-[1400px] mx-auto">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  )
}

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  HeartPulse,
  Building2,
  UserPlus,
  Activity,
  LogIn,
} from 'lucide-react'

const NAV_ITEMS = [
  {
    href: '/hospital',
    label: 'Dashboard RS',
    sublabel: 'Analitik & Statistik',
    Icon: Building2,
  },
  {
    href: '/patient',
    label: 'Daftarkan Pasien',
    sublabel: 'Registrasi Darurat',
    Icon: UserPlus,
  },
  {
    href: '/login',
    label: 'Login Admin',
    sublabel: 'Otentikasi & Token',
    Icon: LogIn,
  },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside
      className="fixed left-0 top-0 h-full w-64 flex flex-col shadow-xl z-20"
      style={{ backgroundColor: '#62796A' }}
    >
      {/* ── Brand / Logo ── */}
      <div className="px-5 py-5 border-b border-white/20">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-white rounded-2xl flex items-center justify-center shadow-lg shrink-0">
            <HeartPulse className="w-6 h-6" style={{ color: '#62796A' }} />
          </div>
          <div className="min-w-0">
            <h1 className="text-[18px] font-bold text-white leading-tight tracking-tight">
              MediCRM
            </h1>
            <p className="text-white/55 text-[11px] mt-0.5">Platform CRM Medis</p>
          </div>
        </div>
      </div>

      {/* ── SDGs Badge ── */}
      <div className="mx-4 mt-4">
        <div className="bg-white/10 border border-white/20 rounded-xl px-3.5 py-2.5">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-3.5 h-3.5 text-green-300 shrink-0" />
            <span className="text-[11px] font-bold text-white tracking-wide uppercase">
              SDGs Goal 3
            </span>
          </div>
          <p className="text-[11px] text-white/60 leading-snug">
            Good Health &amp; Well-being
          </p>
        </div>
      </div>

      {/* ── Navigation ── */}
      <nav className="flex-1 px-3 pt-5 pb-3 overflow-y-auto">
        <p className="text-white/35 text-[10px] uppercase tracking-widest font-semibold mb-2 px-2">
          Menu Utama
        </p>

        <ul className="space-y-1">
          {NAV_ITEMS.map(({ href, label, sublabel, Icon }) => {
            const isActive =
              pathname === href || pathname.startsWith(href + '/')

            return (
              <li key={href}>
                <Link
                  href={href}
                  className={[
                    'group flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200',
                    isActive
                      ? 'bg-white shadow-md'
                      : 'hover:bg-white/15 active:bg-white/20',
                  ].join(' ')}
                >
                  {/* Icon wrapper */}
                  <div
                    className={[
                      'w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-all duration-200',
                      isActive
                        ? 'shadow-sm'
                        : 'bg-white/15 group-hover:bg-white/25',
                    ].join(' ')}
                    style={isActive ? { backgroundColor: '#62796A' } : {}}
                  >
                    <Icon className="w-[18px] h-[18px] text-white" />
                  </div>

                  {/* Label */}
                  <div className="min-w-0">
                    <p
                      className={[
                        'text-[13px] font-semibold leading-tight truncate',
                        isActive ? '' : 'text-white',
                      ].join(' ')}
                      style={isActive ? { color: '#62796A' } : {}}
                    >
                      {label}
                    </p>
                    <p
                      className={[
                        'text-[11px] leading-tight mt-0.5 truncate',
                        isActive ? '' : 'text-white/50',
                      ].join(' ')}
                      style={isActive ? { color: 'rgba(98,121,106,0.6)' } : {}}
                    >
                      {sublabel}
                    </p>
                  </div>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* ── Footer ── */}
      <div className="px-4 py-4 border-t border-white/20">
        <p className="text-white/25 text-[10px]">RSUD Harapan Sehat</p>
      </div>
    </aside>
  )
}

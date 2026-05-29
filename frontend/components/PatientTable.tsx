'use client'

import { Patient } from '@/lib/api'
import { useState, useMemo } from 'react'
import { Search, ChevronUp, ChevronDown, Users } from 'lucide-react'

// ── Types ─────────────────────────────────────────────────────────

interface PatientTableProps {
  patients: Patient[]
}

type SortField = 'id' | 'name' | 'age' | 'pain_level' | 'triage_status'
type SortDir   = 'asc' | 'desc'

// ── Triage Styling Config ─────────────────────────────────────────

const TRIAGE_STYLE: Record<string, { badge: string; dot: string; rowAccent: string }> = {
  Kritis: {
    badge:     'badge-critical',
    dot:       'bg-red-500',
    rowAccent: '',
  },
  Sedang: {
    badge:     'badge-moderate',
    dot:       'bg-amber-500',
    rowAccent: '',
  },
  Ringan: {
    badge:     'badge-mild',
    dot:       'bg-emerald-500',
    rowAccent: '',
  },
}

const PAIN_COLOR = (level: number): string => {
  if (level >= 8) return '#ef4444'
  if (level >= 5) return '#f59e0b'
  return '#10b981'
}

// ── Sort Icon ─────────────────────────────────────────────────────

function SortIcon({ field, active, dir }: { field: SortField; active: boolean; dir: SortDir }) {
  return (
    <span className="inline-flex flex-col ml-1 opacity-70">
      <ChevronUp
        className={`w-3 h-3 -mb-1 transition-opacity ${active && dir === 'asc' ? 'opacity-100 text-white' : 'opacity-30 text-white'}`}
      />
      <ChevronDown
        className={`w-3 h-3 transition-opacity ${active && dir === 'desc' ? 'opacity-100 text-white' : 'opacity-30 text-white'}`}
      />
    </span>
  )
}

// ── Component ─────────────────────────────────────────────────────

export default function PatientTable({ patients }: PatientTableProps) {
  const [search,   setSearch]   = useState('')
  const [sortField, setSortField] = useState<SortField>('id')
  const [sortDir,   setSortDir]   = useState<SortDir>('desc')

  // Toggle sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }

  // Filter + Sort (memoized for performance)
  const processedPatients = useMemo(() => {
    const term = search.toLowerCase().trim()
    const filtered = term
      ? patients.filter(
          p =>
            p.name.toLowerCase().includes(term) ||
            p.chief_complaint.toLowerCase().includes(term) ||
            p.triage_status.toLowerCase().includes(term),
        )
      : patients

    return [...filtered].sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      switch (sortField) {
        case 'id':           return (a.id           - b.id)           * dir
        case 'age':          return (a.age           - b.age)          * dir
        case 'pain_level':   return (a.pain_level    - b.pain_level)   * dir
        case 'name':         return a.name.localeCompare(b.name)       * dir
        case 'triage_status': return a.triage_status.localeCompare(b.triage_status) * dir
        default:             return 0
      }
    })
  }, [patients, search, sortField, sortDir])

  const ThButton = ({
    field,
    children,
    className = '',
  }: {
    field: SortField
    children: React.ReactNode
    className?: string
  }) => (
    <th
      className={[
        'px-5 py-3.5 text-left text-[11px] font-semibold text-white uppercase tracking-wider',
        'cursor-pointer select-none hover:bg-[#4f6356] transition-colors duration-150',
        className,
      ].join(' ')}
      onClick={() => handleSort(field)}
    >
      <span className="inline-flex items-center">
        {children}
        <SortIcon field={field} active={sortField === field} dir={sortDir} />
      </span>
    </th>
  )

  return (
    <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden animate-slide-up">

      {/* ── Table Toolbar ── */}
      <div className="px-6 py-4 border-b border-gray-100 flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center shadow-sm"
               style={{ backgroundColor: '#62796A' }}>
            <Users className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="font-bold text-gray-800 text-[15px]">Daftar Pasien Terdaftar</h2>
            <p className="text-[11px] text-gray-400 mt-0.5">
              Menampilkan{' '}
              <span className="font-semibold text-gray-600">{processedPatients.length}</span>{' '}
              dari{' '}
              <span className="font-semibold text-gray-600">{patients.length}</span>{' '}
              pasien
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Cari nama / keluhan / status..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 text-[13px] border border-gray-200 rounded-xl
                       focus:outline-none focus:ring-2 focus:ring-[#62796A]/30 focus:border-[#62796A]
                       bg-gray-50 hover:bg-white w-64 transition-all duration-200"
          />
        </div>
      </div>

      {/* ── Table ── */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr style={{ backgroundColor: '#62796A' }}>
              <ThButton field="id" className="w-20">ID</ThButton>
              <ThButton field="name">Nama Pasien</ThButton>
              <ThButton field="age" className="w-24">Usia</ThButton>
              <th className="px-5 py-3.5 text-left text-[11px] font-semibold text-white uppercase tracking-wider">
                Keluhan Utama
              </th>
              <ThButton field="pain_level" className="w-24">Nyeri</ThButton>
              <ThButton field="triage_status" className="w-36">Status Triase</ThButton>
              <th className="px-5 py-3.5 text-left text-[11px] font-semibold text-white uppercase tracking-wider w-40">
                Waktu Daftar
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-50">
            {processedPatients.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-5 py-16 text-center">
                  <div className="flex flex-col items-center gap-2 text-gray-400">
                    <Search className="w-8 h-8 opacity-30" />
                    <p className="text-sm font-medium">Tidak ada pasien yang cocok</p>
                    <p className="text-xs">Coba kata kunci lain</p>
                  </div>
                </td>
              </tr>
            ) : (
              processedPatients.map(patient => {
                const triageStyle = TRIAGE_STYLE[patient.triage_status] ?? TRIAGE_STYLE['Ringan']
                const painColor   = PAIN_COLOR(patient.pain_level)

                return (
                  <tr key={patient.id} className="tr-hover">
                    {/* ID */}
                    <td className="px-5 py-4">
                      <span className="text-[12px] font-mono text-gray-400">
                        #{String(patient.id).padStart(3, '0')}
                      </span>
                    </td>

                    {/* Nama */}
                    <td className="px-5 py-4">
                      <p className="text-[13px] font-semibold text-gray-800 whitespace-nowrap">
                        {patient.name}
                      </p>
                    </td>

                    {/* Usia */}
                    <td className="px-5 py-4">
                      <span className="text-[13px] text-gray-600">{patient.age} thn</span>
                    </td>

                    {/* Keluhan */}
                    <td className="px-5 py-4 max-w-[240px]">
                      <p
                        className="text-[13px] text-gray-600 truncate"
                        title={patient.chief_complaint}
                      >
                        {patient.chief_complaint}
                      </p>
                    </td>

                    {/* Tingkat Nyeri */}
                    <td className="px-5 py-4">
                      <div
                        className="w-7 h-7 rounded-full flex items-center justify-center
                                   text-[11px] font-bold text-white shadow-sm"
                        style={{ backgroundColor: painColor }}
                      >
                        {patient.pain_level}
                      </div>
                    </td>

                    {/* Status Triase */}
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full shrink-0 ${triageStyle.dot}`} />
                        <span className={triageStyle.badge}>
                          {patient.triage_status}
                        </span>
                      </div>
                    </td>

                    {/* Waktu */}
                    <td className="px-5 py-4">
                      <span className="text-[12px] text-gray-400">
                        {new Date(patient.registered_at).toLocaleString('id-ID', {
                          day:    '2-digit',
                          month:  'short',
                          hour:   '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* ── Table Footer ── */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-100 flex items-center gap-4">
        {(['Kritis', 'Sedang', 'Ringan'] as const).map(status => {
          const count = patients.filter(p => p.triage_status === status).length
          const s = TRIAGE_STYLE[status]
          return (
            <div key={status} className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${s.dot}`} />
              <span className="text-[11px] text-gray-500">
                {status}: <strong className="text-gray-700">{count}</strong>
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

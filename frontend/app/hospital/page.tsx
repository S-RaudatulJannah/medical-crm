'use client'

import { useEffect, useState, useCallback } from 'react'
import { apiClient, HospitalStats } from '@/lib/api'
import MetricCard from '@/components/MetricCard'
import PatientTable from '@/components/PatientTable'
import {
  RefreshCw,
  Building2,
  AlertCircle,
  Wifi,
  WifiOff,
  MapPin,
  Phone,
} from 'lucide-react'

// ── Loading Skeleton ──────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
      <div className="h-0.5 bg-gray-100" />
      <div className="p-5 space-y-3">
        <div className="flex justify-between items-start">
          <div className="h-3 w-24 bg-gray-100 rounded animate-pulse" />
          <div className="w-9 h-9 bg-gray-100 rounded-xl animate-pulse" />
        </div>
        <div className="h-9 w-16 bg-gray-100 rounded animate-pulse" />
        <div className="h-3 w-20 bg-gray-100 rounded animate-pulse" />
        <div className="h-6 w-28 bg-gray-100 rounded-full animate-pulse" />
      </div>
    </div>
  )
}

// ── Page Component ────────────────────────────────────────────────

export default function HospitalPage() {
  const [stats,       setStats]       = useState<HospitalStats | null>(null)
  const [loading,     setLoading]     = useState(true)
  const [refreshing,  setRefreshing]  = useState(false)
  const [error,       setError]       = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string>('')
  const [isOnline,    setIsOnline]    = useState(true)

  // Fetch data
  const fetchStats = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true)
    try {
      setError(null)
      const data = await apiClient.getHospitalStats()
      setStats(data)
      setLastUpdated(
        new Date().toLocaleTimeString('id-ID', {
          hour: '2-digit', minute: '2-digit', second: '2-digit',
        }),
      )
      setIsOnline(true)
    } catch {
      setError(
        'Gagal terhubung ke backend. Pastikan service backend berjalan di port 8000.',
      )
      setIsOnline(false)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  // Initial load + auto-refresh every 30s
  useEffect(() => {
    fetchStats()
    const iv = setInterval(() => fetchStats(), 30_000)
    return () => clearInterval(iv)
  }, [fetchStats])

  const todayLabel = new Date().toLocaleDateString('id-ID', {
    weekday: 'long',
    year:    'numeric',
    month:   'long',
    day:     'numeric',
  })

  return (
    <div className="animate-fade-in space-y-6">

      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shadow-md"
              style={{ backgroundColor: '#62796A' }}
            >
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-800 leading-tight">
                {stats?.hospital_name ?? 'Dashboard Rumah Sakit'}
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">{todayLabel}</p>
            </div>
          </div>

          {/* Hospital info row */}
          {stats && (
            <div className="flex flex-wrap gap-4 mt-3 ml-1">
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <MapPin className="w-3.5 h-3.5 text-gray-400" />
                {stats.address}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <Phone className="w-3.5 h-3.5 text-gray-400" />
                {stats.phone}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 shrink-0">
          {/* Connection Status */}
          <div
            className={[
              'flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-full border font-medium',
              isOnline
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-red-50 border-red-200 text-red-700',
            ].join(' ')}
          >
            {isOnline
              ? <Wifi className="w-3.5 h-3.5" />
              : <WifiOff className="w-3.5 h-3.5" />}
            {isOnline ? 'Backend Terhubung' : 'Terputus'}
          </div>

          {lastUpdated && (
            <span className="text-xs text-gray-400 hidden md:block">
              Update: {lastUpdated}
            </span>
          )}

          <button
            id="refresh-stats-btn"
            onClick={() => fetchStats(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white
                       rounded-xl hover:opacity-90 active:scale-95 transition-all
                       shadow-md disabled:opacity-60 disabled:cursor-not-allowed"
            style={{ backgroundColor: '#62796A' }}
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Memperbarui...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* ── Error Banner ── */}
      {error && (
        <div className="flex items-start gap-3 px-5 py-4 bg-red-50 border border-red-200 rounded-2xl animate-slide-up">
          <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-700">Koneksi Gagal</p>
            <p className="text-xs text-red-600 mt-0.5">{error}</p>
            <p className="text-xs text-red-500 mt-1">
              Jalankan backend dengan: <code className="font-mono bg-red-100 px-1 rounded">uvicorn app.main:app --reload</code>
            </p>
          </div>
        </div>
      )}

      {/* ── Metric Cards ── */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : stats ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <MetricCard
              title="Total Pasien Hari Ini"
              value={stats.total_patients_today}
              subtitle="pasien terdaftar hari ini"
              variant="primary"
              icon="users"
              trend={`${stats.total_patients} total semua waktu`}
            />
            <MetricCard
              title="Kapasitas Tempat Tidur"
              value={stats.bed_capacity}
              subtitle="total kapasitas RS"
              variant="blue"
              icon="bed"
              trend="Kapasitas penuh rumah sakit"
            />
            <MetricCard
              title="Tempat Tidur Terisi"
              value={stats.beds_occupied}
              subtitle="saat ini digunakan"
              variant="amber"
              icon="activity"
              trend={`${stats.occupancy_rate_percent}% tingkat hunian`}
            />
            <MetricCard
              title="Tempat Tidur Tersedia"
              value={stats.beds_available}
              subtitle="siap digunakan"
              variant="green"
              icon="check"
              trend={`${(100 - stats.occupancy_rate_percent).toFixed(1)}% kapasitas tersisa`}
            />
          </div>

          {/* ── Triage Distribution ── */}
          <div className="bg-white rounded-2xl p-6 shadow-card border border-gray-100 animate-slide-up">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="font-bold text-gray-800 text-[15px]">
                  Distribusi Status Triase
                </h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  Berdasarkan {stats.total_patients} pasien terdaftar
                </p>
              </div>
              <span
                className="text-xs font-semibold px-3 py-1.5 rounded-full text-white"
                style={{ backgroundColor: '#62796A' }}
              >
                Live Data
              </span>
            </div>

            {/* Triage Pills */}
            <div className="flex flex-wrap gap-3 mb-5">
              {[
                {
                  label:    'Kritis',
                  count:     stats.triage_distribution.critical,
                  dot:      'bg-red-500',
                  pill:     'bg-red-50 border-red-200 text-red-700',
                  countCls: 'text-red-600',
                },
                {
                  label:    'Sedang',
                  count:     stats.triage_distribution.moderate,
                  dot:      'bg-amber-500',
                  pill:     'bg-amber-50 border-amber-200 text-amber-700',
                  countCls: 'text-amber-600',
                },
                {
                  label:    'Ringan',
                  count:     stats.triage_distribution.mild,
                  dot:      'bg-emerald-500',
                  pill:     'bg-emerald-50 border-emerald-200 text-emerald-700',
                  countCls: 'text-emerald-600',
                },
              ].map(item => (
                <div
                  key={item.label}
                  className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl border ${item.pill}`}
                >
                  <span className={`w-2.5 h-2.5 rounded-full ${item.dot}`} />
                  <span className={`text-2xl font-bold ${item.countCls}`}>{item.count}</span>
                  <span className="text-sm font-medium">{item.label}</span>
                  {stats.total_patients > 0 && (
                    <span className="text-xs opacity-60">
                      ({Math.round((item.count / stats.total_patients) * 100)}%)
                    </span>
                  )}
                </div>
              ))}
            </div>

            {/* Progress Bar */}
            {stats.total_patients > 0 ? (
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden flex">
                {stats.triage_distribution.critical > 0 && (
                  <div
                    className="bg-red-500 transition-all duration-700 ease-out"
                    style={{
                      width: `${(stats.triage_distribution.critical / stats.total_patients) * 100}%`,
                    }}
                  />
                )}
                {stats.triage_distribution.moderate > 0 && (
                  <div
                    className="bg-amber-500 transition-all duration-700 ease-out"
                    style={{
                      width: `${(stats.triage_distribution.moderate / stats.total_patients) * 100}%`,
                    }}
                  />
                )}
                {stats.triage_distribution.mild > 0 && (
                  <div
                    className="bg-emerald-500 transition-all duration-700 ease-out"
                    style={{
                      width: `${(stats.triage_distribution.mild / stats.total_patients) * 100}%`,
                    }}
                  />
                )}
              </div>
            ) : (
              <div className="h-3 bg-gray-100 rounded-full" />
            )}
          </div>

          {/* ── Patient Table ── */}
          <PatientTable patients={stats.patients} />
        </>
      ) : null}
    </div>
  )
}

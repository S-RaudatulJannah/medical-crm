'use client'

import { useState } from 'react'
import { apiClient, PatientInput, RegisterResponse } from '@/lib/api'
import {
  UserPlus,
  AlertCircle,
  CheckCircle2,
  Loader2,
  HeartPulse,
  ChevronRight,
  Cpu,
  RotateCcw,
} from 'lucide-react'

// ── Constants ─────────────────────────────────────────────────────

const PAIN_DESCRIPTIONS: Record<number, { label: string; color: string }> = {
  1:  { label: 'Tidak ada nyeri',            color: '#10b981' },
  2:  { label: 'Nyeri sangat ringan',         color: '#34d399' },
  3:  { label: 'Nyeri ringan',                color: '#84cc16' },
  4:  { label: 'Nyeri cukup ringan',          color: '#eab308' },
  5:  { label: 'Nyeri sedang',                color: '#f59e0b' },
  6:  { label: 'Nyeri cukup berat',           color: '#f97316' },
  7:  { label: 'Nyeri berat',                 color: '#ef4444' },
  8:  { label: 'Nyeri sangat berat',          color: '#dc2626' },
  9:  { label: 'Nyeri hampir tak tertahankan', color: '#b91c1c' },
  10: { label: 'Nyeri tak tertahankan',       color: '#7f1d1d' },
}

const TRIAGE_CONFIG: Record<string, {
  icon: string; bg: string; border: string; titleColor: string; descColor: string; desc: string
}> = {
  Kritis: {
    icon:       '🔴',
    bg:         'bg-red-50',
    border:     'border-red-300',
    titleColor: 'text-red-700',
    descColor:  'text-red-600',
    desc: 'Pasien membutuhkan penanganan SEGERA. Segera bawa ke ruang tindakan darurat!',
  },
  Sedang: {
    icon:       '🟡',
    bg:         'bg-amber-50',
    border:     'border-amber-300',
    titleColor: 'text-amber-700',
    descColor:  'text-amber-600',
    desc: 'Pasien perlu penanganan CEPAT. Masukkan ke antrian prioritas.',
  },
  Ringan: {
    icon:       '🟢',
    bg:         'bg-emerald-50',
    border:     'border-emerald-300',
    titleColor: 'text-emerald-700',
    descColor:  'text-emerald-600',
    desc: 'Pasien dapat menunggu giliran di ruang tunggu umum.',
  },
}

const COMPLAINT_SUGGESTIONS = [
  'Nyeri dada dan sesak napas',
  'Demam tinggi disertai mual',
  'Pusing berat dan migrain',
  'Luka gores / luka ringan',
  'Batuk dan pilek',
  'Nyeri perut mendadak',
]

// ── Initial form state ────────────────────────────────────────────

const INITIAL_FORM: PatientInput = {
  name:             '',
  age:              0,
  chief_complaint:  '',
  pain_level:       5,
}

// ── Page Component ────────────────────────────────────────────────

export default function PatientPage() {
  const [form,        setForm]        = useState<PatientInput>(INITIAL_FORM)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [result,      setResult]      = useState<RegisterResponse | null>(null)
  const [error,       setError]       = useState<string | null>(null)

  const currentPain = PAIN_DESCRIPTIONS[form.pain_level]

  // Dynamic slider background gradient
  const sliderPercent = ((form.pain_level - 1) / 9) * 100
  const sliderColor   = currentPain?.color ?? '#62796A'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) {
      setError('Nama pasien wajib diisi.')
      return
    }
    if (!form.age || form.age <= 0) {
      setError('Usia pasien tidak valid.')
      return
    }
    if (!form.chief_complaint.trim()) {
      setError('Keluhan utama wajib diisi.')
      return
    }

    setIsSubmitting(true)
    setError(null)
    setResult(null)

    try {
      const response = await apiClient.registerPatient(form)
      setResult(response)
      setForm(INITIAL_FORM) // Reset form setelah sukses
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Terjadi kesalahan. Silakan coba kembali.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
    setForm(INITIAL_FORM)
  }

  return (
    <div className="animate-fade-in">

      {/* ── Page Header ── */}
      <div className="flex items-center gap-3 mb-7">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shadow-md"
          style={{ backgroundColor: '#62796A' }}
        >
          <UserPlus className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Pendaftaran Pasien Darurat</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Isi formulir di bawah untuk mendaftarkan pasien baru dan menjalankan triase otomatis
          </p>
        </div>
      </div>

      {/* ── Two-column layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">

        {/* ═════════════════════════════
            LEFT: Main Form (2/3)
            ═════════════════════════════ */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden">

            {/* Form Header */}
            <div
              className="px-6 py-5 flex items-center gap-3"
              style={{ backgroundColor: '#62796A' }}
            >
              <HeartPulse className="w-5 h-5 text-white" />
              <div>
                <h2 className="text-white font-bold text-[15px]">Formulir Registrasi Pasien</h2>
                <p className="text-white/60 text-[11px] mt-0.5">
                  * Semua bidang wajib diisi dengan lengkap dan akurat
                </p>
              </div>
            </div>

            {/* Form Body */}
            <form onSubmit={handleSubmit} className="p-6 space-y-5">

              {/* ── Field: Nama ── */}
              <div>
                <label htmlFor="patient-name" className="block text-[13px] font-semibold text-gray-700 mb-1.5">
                  Nama Lengkap Pasien <span className="text-red-500">*</span>
                </label>
                <input
                  id="patient-name"
                  type="text"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="Contoh: Budi Santoso"
                  required
                  disabled={isSubmitting}
                  className="form-input disabled:opacity-60"
                />
              </div>

              {/* ── Field: Usia ── */}
              <div>
                <label htmlFor="patient-age" className="block text-[13px] font-semibold text-gray-700 mb-1.5">
                  Usia (Tahun) <span className="text-red-500">*</span>
                </label>
                <input
                  id="patient-age"
                  type="number"
                  value={form.age || ''}
                  onChange={e =>
                    setForm({ ...form, age: parseInt(e.target.value) || 0 })
                  }
                  placeholder="Contoh: 35"
                  min={1}
                  max={150}
                  required
                  disabled={isSubmitting}
                  className="form-input disabled:opacity-60 w-40"
                />
              </div>

              {/* ── Field: Keluhan Utama ── */}
              <div>
                <label htmlFor="chief-complaint" className="block text-[13px] font-semibold text-gray-700 mb-1.5">
                  Keluhan Utama <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="chief-complaint"
                  value={form.chief_complaint}
                  onChange={e => setForm({ ...form, chief_complaint: e.target.value })}
                  placeholder="Deskripsikan keluhan utama secara singkat dan jelas..."
                  required
                  rows={3}
                  disabled={isSubmitting}
                  className="form-input resize-none disabled:opacity-60"
                />

                {/* Complaint quick-select suggestions */}
                <div className="flex flex-wrap gap-2 mt-2">
                  {COMPLAINT_SUGGESTIONS.map(s => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setForm({ ...form, chief_complaint: s })}
                      disabled={isSubmitting}
                      className="text-[11px] px-2.5 py-1 rounded-full border border-gray-200
                                 bg-gray-50 text-gray-500 hover:border-[#62796A] hover:text-[#62796A]
                                 hover:bg-[#62796A]/5 transition-all duration-150 disabled:opacity-40"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* ── Field: Tingkat Nyeri ── */}
              <div>
                <label className="block text-[13px] font-semibold text-gray-700 mb-1.5">
                  Tingkat Nyeri{' '}
                  <span className="text-red-500">*</span>
                  <span className="text-gray-400 font-normal ml-1">(Skala 1–10)</span>
                </label>

                <div className="bg-gray-50 rounded-xl p-5 border border-gray-100">
                  {/* Current value display */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-baseline gap-2">
                      <span
                        className="text-5xl font-black tabular-nums transition-all duration-150"
                        style={{ color: sliderColor }}
                      >
                        {form.pain_level}
                      </span>
                      <span className="text-sm text-gray-500">/ 10</span>
                    </div>
                    <div
                      className="px-3 py-1.5 rounded-full text-sm font-semibold text-white transition-all duration-200"
                      style={{ backgroundColor: sliderColor }}
                    >
                      {currentPain?.label}
                    </div>
                  </div>

                  {/* Range slider */}
                  <input
                    id="pain-level-slider"
                    type="range"
                    min={1}
                    max={10}
                    step={1}
                    value={form.pain_level}
                    onChange={e =>
                      setForm({ ...form, pain_level: parseInt(e.target.value) })
                    }
                    disabled={isSubmitting}
                    className="w-full disabled:opacity-60"
                    style={{
                      background: `linear-gradient(to right, ${sliderColor} 0%, ${sliderColor} ${sliderPercent}%, #e5e7eb ${sliderPercent}%, #e5e7eb 100%)`,
                    }}
                  />

                  {/* Scale labels */}
                  <div className="flex justify-between text-[10px] text-gray-400 mt-2 px-0.5">
                    <span>1 — Tidak Nyeri</span>
                    <span>5 — Sedang</span>
                    <span>10 — Ekstrem</span>
                  </div>

                  {/* Quick-select dots */}
                  <div className="flex gap-1.5 mt-4 justify-center">
                    {Array.from({ length: 10 }, (_, i) => i + 1).map(n => {
                      const isSelected = form.pain_level === n
                      const dotColor   = PAIN_DESCRIPTIONS[n]?.color ?? '#62796A'
                      return (
                        <button
                          key={n}
                          type="button"
                          onClick={() => setForm({ ...form, pain_level: n })}
                          disabled={isSubmitting}
                          className={[
                            'w-7 h-7 rounded-full text-[11px] font-bold transition-all duration-150',
                            'disabled:opacity-40',
                            isSelected
                              ? 'text-white scale-125 shadow-lg'
                              : 'bg-gray-200 text-gray-500 hover:scale-110',
                          ].join(' ')}
                          style={isSelected ? { backgroundColor: dotColor } : {}}
                        >
                          {n}
                        </button>
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* ── Error Message ── */}
              {error && (
                <div className="flex items-start gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded-xl animate-slide-up">
                  <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              {/* ── Submit Button ── */}
              <button
                type="submit"
                id="submit-patient-btn"
                disabled={isSubmitting}
                className="btn-primary w-full py-4 text-[15px] rounded-xl"
                style={!isSubmitting ? { backgroundColor: '#62796A' } : {}}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Memproses Triase... (CPU-Intensive berjalan)
                  </>
                ) : (
                  <>
                    <UserPlus className="w-5 h-5" />
                    Daftarkan Pasien &amp; Jalankan Triase Otomatis
                    <ChevronRight className="w-4 h-4 ml-auto" />
                  </>
                )}
              </button>

              {isSubmitting && (
                <p className="text-center text-xs text-gray-400 animate-pulse-soft">
                  ⚙️ Algoritma triase CPU-intensive sedang berjalan...
                  Ini adalah fitur demonstrasi Kubernetes HPA.
                </p>
              )}
            </form>
          </div>
        </div>

        {/* ═════════════════════════════
            RIGHT: Info Sidebar (1/3)
            ═════════════════════════════ */}
        <div className="space-y-4">

          {/* ── Success / Triage Result ── */}
          {result && (
            <div
              className={[
                'rounded-2xl p-5 border-2 animate-slide-up',
                TRIAGE_CONFIG[result.triage_status]?.bg    ?? 'bg-gray-50',
                TRIAGE_CONFIG[result.triage_status]?.border ?? 'border-gray-200',
              ].join(' ')}
            >
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <h3 className="font-bold text-gray-800">Triase Selesai!</h3>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-[11px] text-gray-500 mb-0.5">Nama Pasien</p>
                  <p className="font-bold text-gray-800 text-[15px]">{result.patient.name}</p>
                </div>
                <div>
                  <p className="text-[11px] text-gray-500 mb-1">Status Triase</p>
                  <div className="flex items-center gap-2.5">
                    <span className="text-3xl">{TRIAGE_CONFIG[result.triage_status]?.icon}</span>
                    <span
                      className={`text-2xl font-black ${TRIAGE_CONFIG[result.triage_status]?.titleColor}`}
                    >
                      {result.triage_status}
                    </span>
                  </div>
                </div>
                <p className={`text-[12px] leading-relaxed ${TRIAGE_CONFIG[result.triage_status]?.descColor}`}>
                  {TRIAGE_CONFIG[result.triage_status]?.desc}
                </p>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-[10px] text-gray-400 leading-relaxed">
                  {result.computation_info}
                </p>
              </div>

              <button
                type="button"
                onClick={handleReset}
                className="mt-4 w-full flex items-center justify-center gap-2 py-2 px-4
                           text-sm font-medium rounded-xl border border-gray-300
                           bg-white text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                Daftarkan Pasien Lain
              </button>
            </div>
          )}

          {/* ── Triage Guide ── */}
          <div className="bg-white rounded-2xl p-5 shadow-card border border-gray-100">
            <h3 className="font-bold text-gray-700 mb-4 text-[13px] uppercase tracking-wide">
              Panduan Status Triase
            </h3>
            <div className="space-y-3">
              {[
                {
                  icon: '🔴',
                  label: 'Kritis',
                  desc:  'Nyeri ≥ 8 atau gejala mengancam jiwa (dada, napas, kejang)',
                  bg:    'bg-red-50 border-red-100',
                },
                {
                  icon: '🟡',
                  label: 'Sedang',
                  desc:  'Nyeri 5–7 atau gejala sistemik (demam, mual, pusing)',
                  bg:    'bg-amber-50 border-amber-100',
                },
                {
                  icon: '🟢',
                  label: 'Ringan',
                  desc:  'Nyeri ≤ 4 dan tidak ada gejala mengancam jiwa',
                  bg:    'bg-emerald-50 border-emerald-100',
                },
              ].map(item => (
                <div
                  key={item.label}
                  className={`flex items-start gap-3 p-3 rounded-xl border ${item.bg}`}
                >
                  <span className="text-base mt-0.5">{item.icon}</span>
                  <div>
                    <p className="text-[13px] font-bold text-gray-700">{item.label}</p>
                    <p className="text-[11px] text-gray-500 mt-0.5 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── HPA Demo Info ── */}
          <div
            className="rounded-2xl p-5 border"
            style={{
              backgroundColor: 'rgba(98,121,106,0.08)',
              borderColor:     'rgba(98,121,106,0.2)',
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <Cpu className="w-4 h-4" style={{ color: '#62796A' }} />
              <h3 className="font-bold text-[13px]" style={{ color: '#62796A' }}>
                ⚡ Demonstrasi HPA
              </h3>
            </div>
            <p className="text-[12px] text-gray-600 leading-relaxed">
              Setiap submit menjalankan kalkulasi{' '}
              <strong>bilangan prima hingga 300.000</strong> secara sinkron di backend.
              Saat load test (50+ request bersamaan), CPU pod akan{' '}
              <strong>melonjak mendekati 100%</strong> dan memicu{' '}
              <strong>Kubernetes HPA</strong> untuk menambah pod otomatis.
            </p>
            <div className="mt-3 p-2 bg-white/60 rounded-lg">
              <p className="text-[10px] font-mono text-gray-500 break-all">
                $ kubectl get hpa -w
              </p>
              <p className="text-[10px] font-mono text-gray-500 break-all mt-1">
                $ hey -n 200 -c 50 -m POST http://backend/api/patients
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

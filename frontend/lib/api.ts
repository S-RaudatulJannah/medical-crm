/**
 * API Client - Medical CRM Frontend
 *
 * Semua request menggunakan path relatif /api/* yang di-proxy oleh Next.js
 * ke backend FastAPI melalui konfigurasi rewrites di next.config.js.
 *
 * Alur di Kubernetes:
 *   Browser → [/api/patients] → Next.js → [BACKEND_URL/api/patients] → FastAPI
 *
 * Keuntungan:
 * - Backend URL dikonfigurasi sebagai server-side env var (BACKEND_URL)
 * - Tidak perlu rebuild image saat ganti URL backend
 * - Bisa dikonfigurasi via Kubernetes ConfigMap
 */

// ─── Type Definitions ────────────────────────────────────────────

/** Data input dari form pendaftaran pasien */
export interface PatientInput {
  name: string
  age: number
  chief_complaint: string
  pain_level: number
}

/** Record pasien yang tersimpan di backend */
export interface Patient {
  id: number
  name: string
  age: number
  chief_complaint: string
  pain_level: number
  triage_status: 'Kritis' | 'Sedang' | 'Ringan'
  registered_at: string
  hospital_id: number
}

/** Response setelah registrasi pasien */
export interface RegisterResponse {
  message: string
  patient: Patient
  triage_status: string
  computation_info: string
}

/** Statistik rumah sakit dari /api/hospitals/stats */
export interface HospitalStats {
  hospital_id: number
  hospital_name: string
  address: string
  phone: string
  email: string
  total_patients_today: number
  total_patients: number
  bed_capacity: number
  beds_occupied: number
  beds_available: number
  occupancy_rate_percent: number
  triage_distribution: {
    critical: number
    moderate: number
    mild: number
  }
  patients: Patient[]
  last_updated: string
}

// ─── Base Fetch Helper ────────────────────────────────────────────

/**
 * Helper fetch dengan error handling terpusat.
 * Semua request diarahkan ke /api/* yang di-proxy ke backend.
 */
async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `/api${path}`

  const response = await fetch(url, {
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    // Coba parse error message dari backend
    const errorData = await response
      .json()
      .catch(() => ({ detail: `Request gagal dengan status ${response.status}` }))
    throw new Error(
      typeof errorData.detail === 'string'
        ? errorData.detail
        : JSON.stringify(errorData.detail),
    )
  }

  return response.json() as Promise<T>
}

// ─── API Client Methods ───────────────────────────────────────────

export const apiClient = {
  /**
   * GET /api/hospitals/stats
   * Mengambil statistik real-time rumah sakit termasuk daftar pasien.
   */
  getHospitalStats: (): Promise<HospitalStats> =>
    apiFetch<HospitalStats>('/hospitals/stats'),

  /**
   * GET /api/patients
   * Mengambil daftar semua pasien yang terdaftar.
   */
  getPatients: (): Promise<{ patients: Patient[]; total: number }> =>
    apiFetch<{ patients: Patient[]; total: number }>('/patients'),

  /**
   * POST /api/patients
   * Mendaftarkan pasien baru. Akan menjalankan CPU-intensive computation
   * (pencarian bilangan prima) sebelum mengembalikan respons.
   * Dirancang untuk memicu Kubernetes HPA saat load testing.
   */
  registerPatient: (data: PatientInput): Promise<RegisterResponse> =>
    apiFetch<RegisterResponse>('/patients', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}

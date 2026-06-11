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
 *
 * [FIX-11] Token storage dimigrasi dari localStorage ke sessionStorage.
 *
 * Mengapa sessionStorage lebih aman?
 * - localStorage: Data PERMANEN, bertahan bahkan setelah browser ditutup.
 *   Jika ada celah XSS, attacker bisa menjalankan:
 *   localStorage.getItem('MEDICRM_ACCESS_TOKEN') → TOKEN DICURI!
 *   Dan token itu akan tetap tersedia bahkan keesokan harinya.
 *
 * - sessionStorage: Data SEMENTARA, dihapus saat tab ditutup.
 *   Selain itu, data diisolasi per-tab (tab A tidak bisa baca data tab B).
 *   Ini memperkecil jendela waktu eksploitasi XSS secara signifikan.
 *
 * Fallback token juga dikosongkan — tidak lagi ada hardcoded demo secret.
 * User WAJIB login terlebih dahulu untuk mendapatkan token valid.
 */
const API_FALLBACK_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN ?? ''
const CSRF_FALLBACK_TOKEN = process.env.NEXT_PUBLIC_CSRF_TOKEN ?? ''
const AUTH_TOKEN_KEY = 'MEDICRM_ACCESS_TOKEN'
const CSRF_TOKEN_KEY = 'MEDICRM_CSRF_TOKEN'
const AUTH_ROLE_KEY = 'MEDICRM_ROLE'

export interface AuthResponse {
  access_token: string
  token_type: 'bearer'
  role: string
  csrf_token: string
}

export interface UploadResponse {
  message: string
  patient_id: number
  file_name: string
  content_type: string
  size_bytes: number
}

function getStoredToken(): string {
  if (typeof window === 'undefined') return API_FALLBACK_TOKEN
  return window.sessionStorage.getItem(AUTH_TOKEN_KEY) ?? API_FALLBACK_TOKEN
}

function getStoredCsrfToken(): string {
  if (typeof window === 'undefined') return CSRF_FALLBACK_TOKEN
  return window.sessionStorage.getItem(CSRF_TOKEN_KEY) ?? CSRF_FALLBACK_TOKEN
}

export function storeAuthTokens(token: string, csrf: string, role: string) {
  if (typeof window === 'undefined') return
  window.sessionStorage.setItem(AUTH_TOKEN_KEY, token)
  window.sessionStorage.setItem(CSRF_TOKEN_KEY, csrf)
  window.sessionStorage.setItem(AUTH_ROLE_KEY, role)
}

export function clearAuthTokens() {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(AUTH_TOKEN_KEY)
  window.sessionStorage.removeItem(CSRF_TOKEN_KEY)
  window.sessionStorage.removeItem(AUTH_ROLE_KEY)
}

export function getStoredAuthState() {
  if (typeof window === 'undefined') return null
  const token = window.sessionStorage.getItem(AUTH_TOKEN_KEY)
  const csrf = window.sessionStorage.getItem(CSRF_TOKEN_KEY)
  const role = window.sessionStorage.getItem(AUTH_ROLE_KEY)
  return token && csrf && role ? { token, csrf, role } : null
}

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `/api${path}`

  const defaultHeaders: Record<string, string> = {
    Authorization: `Bearer ${getStoredToken()}`,
    'X-CSRF-Token': getStoredCsrfToken(),
  }

  if (!(options?.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json'
  }

  const response = await fetch(url, {
    cache: 'no-store',
    headers: {
      ...defaultHeaders,
      ...(options?.headers ?? {}),
    },
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

  /**
   * POST /api/auth/login
   * Melakukan login admin dan menerima access token + CSRF token.
   */
  login: (username: string, password: string): Promise<AuthResponse> =>
    apiFetch<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  /**
   * POST /api/patients/{id}/upload
   * Upload dokumen pasien dengan FormData.
   */
  uploadPatientDocument: (
    patientId: number,
    file: File,
  ): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    return apiFetch<UploadResponse>(`/patients/${patientId}/upload`, {
      method: 'POST',
      body: formData,
    })
  },
}

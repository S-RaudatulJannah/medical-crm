'use client'

import { useState } from 'react'
import Link from 'next/link'
import { apiClient, storeAuthTokens } from '@/lib/api'
import { Lock, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsLoading(true)
    setError(null)
    setMessage(null)

    try {
      const response = await apiClient.login(username.trim(), password.trim())
      storeAuthTokens(response.access_token, response.csrf_token, response.role)
      setMessage(
        `Login berhasil. Role Anda: ${response.role}. Token tersimpan di browser.`,
      )
      setPassword('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Gagal login. Periksa kredensial.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="animate-fade-in max-w-3xl mx-auto space-y-6">
      <div className="bg-white rounded-3xl shadow-card border border-gray-100 p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 rounded-3xl bg-[#62796A] flex items-center justify-center text-white shadow-md">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Admin Login</h1>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="login-username" className="block text-sm font-semibold text-gray-700 mb-2">
              Username
            </label>
            <input
              id="login-username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="form-input w-full"
              placeholder="admin"
              required
              disabled={isLoading}
            />
          </div>

          <div>
            <label htmlFor="login-password" className="block text-sm font-semibold text-gray-700 mb-2">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="form-input w-full"
              placeholder="••••••••"
              required
              minLength={8}
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5" />
                <span>{error}</span>
              </div>
            </div>
          )}

          {message && (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 mt-0.5" />
                <span>{message}</span>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full py-3 rounded-2xl text-sm font-semibold text-white bg-[#62796A] hover:bg-[#556d5b] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Memproses login...' : 'Masuk dan Simpan Token'}
          </button>
        </form>
      </div>

      <div className="flex items-center justify-between gap-4 rounded-3xl border border-gray-100 bg-white p-5 shadow-sm">
        <div>
          <p className="text-sm font-semibold text-gray-800">Lanjutkan ke fitur</p>
          <p className="text-xs text-gray-500">Dashboard RS atau pendaftaran pasien.</p>
        </div>
        <Link href="/patient" className="inline-flex items-center gap-2 text-sm font-semibold text-[#62796A] hover:underline">
          Buka Form Pasien <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  )
}

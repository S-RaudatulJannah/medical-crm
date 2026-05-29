import { redirect } from 'next/navigation'

/**
 * Root page - Redirect ke Dashboard Rumah Sakit
 * Halaman utama langsung diarahkan ke /hospital
 */
export default function Home() {
  redirect('/hospital')
}

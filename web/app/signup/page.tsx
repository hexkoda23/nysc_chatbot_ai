"use client"
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthed, signInOrUp } from '../../lib/auth'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'

export default function SignupPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { t } = useI18n()

  useEffect(() => {
    if (isAuthed()) router.replace('/welcome')
  }, [router])

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      if (!name || !email || !password) throw new Error('Please fill in all fields.')
      signInOrUp({ name, email })
      router.replace('/welcome')
    } catch (err: any) {
      setError(err?.message || 'Signup failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main
      className="min-h-[100dvh] relative flex flex-col items-center justify-between"
      style={{
        backgroundImage: "url('/NYSC-ORIENTATION-CAMPS-IN-NIGERIA-1-1024x531.jpg')",
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/40 z-0" />

      {/* Top Logo */}
      <div className="relative z-10 flex flex-col items-center pt-8 pb-4">
        <div className="flex items-center gap-3">
          <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" width={64} height={64} className="rounded-full" />
          <div className="text-white text-center">
            <div className="text-lg font-bold tracking-widest leading-tight">NATIONAL YOUTH SERVICE CORPS</div>
            <div className="text-xs tracking-[0.25em] text-green-300">• SERVICE AND HUMILITY •</div>
          </div>
        </div>
      </div>

      {/* Signup Card */}
      <div className="relative z-10 w-full max-w-sm mx-auto px-4 flex-1 flex items-center justify-center">
        <div className="bg-white/95 backdrop-blur rounded-2xl shadow-2xl w-full overflow-hidden">
          {/* Card Header */}
          <div className="bg-green-600 px-6 py-3 text-white font-semibold text-center text-base tracking-wide">
            New User Registration
          </div>

          <form onSubmit={onSubmit} className="px-6 py-5 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                👤 Full Name:
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Babatunde Tinubu"
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-blue-50"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ✉ Email Address:
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@gmail.com"
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-blue-50"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                🔒 Password:
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-blue-50"
                required
              />
            </div>

            {error && <div className="text-sm text-red-600 text-center">{error}</div>}

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold px-6 py-2 rounded transition-colors duration-150 disabled:opacity-60"
              >
                {loading ? 'Creating Account…' : 'Register'}
              </button>
            </div>

            <div className="text-center pt-1">
              <div className="text-xs text-gray-500">
                Already have an account?{' '}
                <a href="/login" className="text-green-700 underline">Login here</a>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Bottom Banner Text */}
      <div className="relative z-10 text-white text-left px-8 pb-8 w-full">
        <div className="text-4xl font-black tracking-tight leading-tight opacity-70">
          SERVICE<br /><span className="text-2xl font-semibold">AND</span> HUMILITY
        </div>
      </div>

      {/* Footer */}
      <div className="absolute bottom-2 w-full text-center z-10">
        <p className="text-white/50 text-[10px]">
          Copyright © 2026 National Youth Service Corps. All rights reserved.
        </p>
      </div>
    </main>
  )
}

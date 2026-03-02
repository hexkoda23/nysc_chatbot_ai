"use client"
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthed, signInOrUp } from '../../lib/auth'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'

export default function LoginPage() {
  const router = useRouter()
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
      if (!email || !password) throw new Error('Please fill in all fields.')
      signInOrUp({ name: email.split('@')[0], email })
      router.replace('/welcome')
    } catch (err: any) {
      setError(err?.message || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main
      className="min-h-[100dvh] relative flex flex-col items-center justify-between"
      style={{
        backgroundImage: "url('/NYSC.jpg')",
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

      {/* Login Card */}
      <div className="relative z-10 w-full max-w-sm mx-auto px-4 flex-1 flex items-center justify-center">
        <div className="bg-white/95 backdrop-blur rounded-2xl shadow-2xl w-full overflow-hidden">
          {/* Card Header */}
          <div className="bg-green-600 px-6 py-3 text-white font-semibold text-center text-base tracking-wide">
            Existing User Login
          </div>

          <form onSubmit={onSubmit} className="px-6 py-5 space-y-4">
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
                {loading ? 'Logging in…' : 'Login'}
              </button>
            </div>

            <div className="text-center space-y-1 pt-1">
              <a href="/signup" className="text-xs text-green-700 hover:underline block">
                Forgot Password or E-mail?
              </a>
              <div className="text-xs text-gray-500">
                Don't have an account?{' '}
                <a href="/signup" className="text-green-700 underline">Create Account</a>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Bottom Banner Text */}
      <div className="relative z-10 text-white text-left px-8 pb-8 w-full">
        <div className="text-4xl font-black tracking-tight leading-tight opacity-70">
          NYSC<br />CHATBOT<br />SYSTEM
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

"use client"
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthed, signInOrUp } from '../../lib/auth'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'
import { motion } from 'framer-motion'
import { Globe, ChevronDown, Mail, Lock, LogIn, Eye, EyeOff, ArrowRight } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showLang, setShowLang] = useState(false)
  const { t, lang, setLang } = useI18n()

  useEffect(() => { if (isAuthed()) router.replace('/welcome') }, [router])

  const languages = [
    { code: 'en', label: 'English' },
    { code: 'yo', label: 'Yorùbá' },
    { code: 'ha', label: 'Hausa' },
    { code: 'ig', label: 'Igbo' },
  ]

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
    <main className="min-h-screen relative flex flex-col items-center justify-center overflow-hidden bg-green-950">
      {/* Background */}
      <div className="absolute inset-0 bg-cover bg-center opacity-30 scale-110" style={{ backgroundImage: "url('/NYSC.jpg')" }} />
      <div className="absolute inset-0 bg-gradient-to-br from-[#040D06]/95 via-green-950/80 to-[#0B7A33]/30" />

      {/* Language selector — top right */}
      <div className="absolute top-5 right-5 z-30">
        <div className="relative">
          <button
            onClick={() => setShowLang(!showLang)}
            className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-3 py-2 rounded-full border border-white/15 backdrop-blur-md transition-all text-xs font-semibold"
          >
            <Globe className="w-3.5 h-3.5" />
            {languages.find(l => l.code === lang)?.label}
            <ChevronDown className={`w-3 h-3 transition-transform ${showLang ? 'rotate-180' : ''}`} />
          </button>
          {showLang && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowLang(false)} />
              <div className="absolute right-0 mt-2 w-40 bg-white/10 backdrop-blur-xl rounded-xl shadow-2xl border border-white/15 overflow-hidden z-20">
                {languages.map(l => (
                  <button
                    key={l.code}
                    onClick={() => { setLang(l.code as any); setShowLang(false) }}
                    className={`w-full px-4 py-2.5 text-left text-xs transition-colors ${lang === l.code ? 'bg-white/20 text-white font-semibold' : 'text-white/70 hover:bg-white/10'}`}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Glass Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.97, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-20 w-full max-w-md mx-5"
      >
        {/* Card container */}
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl overflow-hidden">
          {/* Logo + heading */}
          <div className="flex flex-col items-center pt-10 pb-6 px-8 border-b border-white/10">
            <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC" width={56} height={56} className="rounded-full bg-white/10 p-1 shadow-xl mb-5" />
            <h1 className="font-display text-3xl text-white text-center">{t('auth_login_title')}</h1>
            <p className="text-white/50 text-sm mt-1 text-center">Access your intelligent NYSC assistant.</p>
          </div>

          {/* Form */}
          <form onSubmit={onSubmit} className="p-8 space-y-5">
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-white/50 uppercase tracking-widest">{t('auth_email_label')}</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full bg-white border border-gray-200 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[var(--accent-end)] focus:border-transparent transition-all"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-white/50 uppercase tracking-widest">{t('auth_password_label')}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-white border border-gray-200 rounded-xl pl-10 pr-12 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[var(--accent-end)] focus:border-transparent transition-all"
                  required
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition-colors">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && <div className="text-xs text-red-300 bg-red-900/30 border border-red-500/30 p-3 rounded-xl text-center">{error}</div>}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)] hover:opacity-90 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 shadow-lg shadow-green-900/30"
            >
              {loading ? 'Signing in…' : (<><LogIn className="w-4 h-4" /> {t('auth_login_submit')}</>)}
            </button>

            <div className="text-center space-y-2 pt-2">
              <p className="text-xs text-white/40">
                {t('auth_no_account')}{' '}
                <a href="/signup" className="text-[var(--accent-end)] hover:underline font-semibold">{t('auth_signup_link')}</a>
              </p>
            </div>
          </form>
        </div>
      </motion.div>

      {/* Bottom watermark */}
      <p className="absolute bottom-6 text-white/15 text-[10px] uppercase tracking-[0.3em]">Service and Humility • © 2026 NYSC</p>
    </main>
  )
}

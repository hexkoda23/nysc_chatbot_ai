"use client"
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthed, signInOrUp } from '@/lib/auth'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'
import { motion } from 'framer-motion'
import { Globe, ChevronDown, User, Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react'

export default function SignupPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
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
    if (password !== confirmPassword) { setError(t('auth_error_pass_mismatch')); return }
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

  const inputClass = "w-full bg-white border border-gray-200 rounded-xl py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[var(--accent-end)] focus:border-transparent transition-all"

  return (
    <main className="min-h-screen relative flex flex-col items-center justify-center overflow-hidden bg-green-950">
      <div className="absolute inset-0 bg-cover bg-center opacity-30 scale-105" style={{ backgroundImage: "url('/NYSC-ORIENTATION-CAMPS-IN-NIGERIA-1-1024x531.jpg')" }} />
      <div className="absolute inset-0 bg-gradient-to-br from-[#040D06]/95 via-green-950/80 to-[#0B7A33]/30" />

      {/* Language selector */}
      <div className="absolute top-5 right-5 z-30">
        <div className="relative">
          <button onClick={() => setShowLang(!showLang)} className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-3 py-2 rounded-full border border-white/15 backdrop-blur-md transition-all text-xs font-semibold">
            <Globe className="w-3.5 h-3.5" />
            {languages.find(l => l.code === lang)?.label}
            <ChevronDown className={`w-3 h-3 transition-transform ${showLang ? 'rotate-180' : ''}`} />
          </button>
          {showLang && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowLang(false)} />
              <div className="absolute right-0 mt-2 w-40 bg-white/10 backdrop-blur-xl rounded-xl shadow-2xl border border-white/15 overflow-hidden z-20">
                {languages.map(l => (
                  <button key={l.code} onClick={() => { setLang(l.code as any); setShowLang(false) }} className={`w-full px-4 py-2.5 text-left text-xs transition-colors ${lang === l.code ? 'bg-white/20 text-white font-semibold' : 'text-white/70 hover:bg-white/10'}`}>
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
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex flex-col items-center pt-10 pb-6 px-8 border-b border-white/10">
            <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC" width={52} height={52} className="rounded-full bg-white/10 p-1 shadow-xl mb-4" />
            <h1 className="font-display text-3xl text-white text-center">{t('auth_signup_title')}</h1>
            <p className="text-white/50 text-sm mt-1 text-center">Join the intelligent community of Corps Members.</p>
          </div>

          <form onSubmit={onSubmit} className="p-8 space-y-4">
            {/* Name */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-white/50 uppercase tracking-widest">{t('auth_name_label')}</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Adekunle Gold" className={`${inputClass} pl-9`} required />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-white/50 uppercase tracking-widest">{t('auth_email_label')}</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="corp-member@example.com" className={`${inputClass} pl-9`} required />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-white/50 uppercase tracking-widest">{t('auth_password_label')}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" className={`${inputClass} pl-9 pr-10`} required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition-colors">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-semibold text-white/50 uppercase tracking-widest">{t('auth_confirm_password_label')}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input type={showConfirmPassword ? 'text' : 'password'} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="••••••••" className={`${inputClass} pl-9 pr-10`} required />
                <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition-colors">
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && <div className="text-xs text-red-300 bg-red-900/30 border border-red-500/30 p-3 rounded-xl text-center">{error}</div>}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)] hover:opacity-90 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 shadow-lg shadow-green-900/30 mt-2"
            >
              {loading ? 'Processing…' : (<>{t('auth_signup_submit')} <ArrowRight className="w-4 h-4" /></>)}
            </button>

            <p className="text-center text-xs text-white/40 pt-1">
              {t('auth_have_account')}{' '}
              <a href="/login" className="text-[var(--accent-end)] hover:underline font-semibold">{t('auth_login_link')}</a>
            </p>
          </form>
        </div>
      </motion.div>

      <p className="absolute bottom-6 text-white/15 text-[10px] uppercase tracking-[0.3em]">Service and Humility • © 2026 NYSC</p>
    </main>
  )
}

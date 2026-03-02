"use client"
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthed, signInOrUp } from '@/lib/auth'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'
import { Globe, ChevronDown, Mail, Lock, LogIn, ArrowRight } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showLang, setShowLang] = useState(false)
  const { t, lang, setLang } = useI18n()

  useEffect(() => {
    if (isAuthed()) router.replace('/welcome')
  }, [router])

  const languages = [
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'yo', label: 'Yorùbá', flag: '🇳🇬' },
    { code: 'ha', label: 'Hausa', flag: '🇳🇬' },
    { code: 'ig', label: 'Igbo', flag: '🇳🇬' },
  ]

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      if (!email || !password) throw new Error('Please fill in all fields.')
      // Simple logic: name is part of email for logging in
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
      className="min-h-screen relative flex flex-col items-center overflow-hidden bg-green-950"
    >
      {/* Background Image with Overlay */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-40 scale-110"
        style={{ backgroundImage: "url('/NYSC.jpg')" }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-green-950/90 via-green-900/60 to-green-950" />

      {/* Header */}
      <header className="relative z-20 w-full px-4 md:px-6 py-4 md:py-6 flex items-center justify-between max-w-7xl">
        <div className="flex items-center gap-2 md:gap-3 cursor-pointer" onClick={() => router.push('/')}>
          <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" width={36} height={36} className="md:w-12 md:h-12 rounded-full bg-white p-0.5 shadow-xl" />
          <div className="hidden xs:block text-white">
            <div className="text-[10px] md:text-xs font-black tracking-tighter leading-none uppercase">National Youth</div>
            <div className="text-[8px] md:text-[10px] font-bold text-green-400 uppercase">Service Corps</div>
          </div>
        </div>

        {/* Global Language Selector */}
        <div className="relative">
          <button
            onClick={() => setShowLang(!showLang)}
            className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-full border border-white/10 backdrop-blur-md transition-all text-xs font-bold"
          >
            <Globe className="w-4 h-4" />
            <span>{languages.find(l => l.code === lang)?.label}</span>
            <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-300 ${showLang ? 'rotate-180' : ''}`} />
          </button>

          {showLang && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowLang(false)} />
              <div className="absolute right-0 mt-3 w-48 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 overflow-hidden z-20 animate-in fade-in zoom-in duration-200 origin-top-right">
                {languages.map((l) => (
                  <button
                    key={l.code}
                    onClick={() => { setLang(l.code as any); setShowLang(false) }}
                    className={`w-full flex items-center justify-between px-4 py-3 text-xs transition-colors ${lang === l.code ? 'bg-green-50 text-green-700 font-bold' : 'text-gray-600 hover:bg-gray-50'}`}
                  >
                    <span className="flex items-center gap-3">
                      <span className="text-lg">{l.flag}</span>
                      {l.label}
                    </span>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </header>

      {/* Login Form Container */}
      <div className="relative z-10 w-full max-w-md mx-auto px-4 md:px-6 flex-1 flex flex-col justify-center pb-12 md:pb-20">
        <div className="text-center mb-6 md:mb-10">
          <h1 className="text-3xl md:text-4xl font-black text-white tracking-tight mb-1 md:mb-2">Welcome Back</h1>
          <p className="text-green-200/70 text-[12px] md:text-sm font-medium">Access your intelligent NYSC assistant.</p>
        </div>

        <div className="bg-white rounded-3xl md:rounded-[32px] shadow-2xl overflow-hidden border border-white/20">
          <div className="bg-green-600 px-6 md:px-8 py-3 md:py-4 text-white text-[9px] md:text-[10px] font-black uppercase tracking-[0.2em] text-center">
            Secured Access Portal
          </div>

          <form onSubmit={onSubmit} className="p-6 md:p-8 space-y-5 md:space-y-6">
            <div className="space-y-1.5">
              <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full bg-gray-50 border-0 rounded-2xl px-11 py-4 text-sm font-bold focus:ring-2 focus:ring-green-500 transition-all placeholder:text-gray-300 shadow-inner"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-gray-50 border-0 rounded-2xl px-11 py-4 text-sm font-bold focus:ring-2 focus:ring-green-500 transition-all placeholder:text-gray-300 shadow-inner"
                  required
                />
              </div>
            </div>

            {error && <div className="text-xs text-red-600 font-bold bg-red-50 p-3 rounded-xl text-center border border-red-100">{error}</div>}

            <button
              type="submit"
              disabled={loading}
              className="group w-full bg-green-600 hover:bg-green-700 text-white font-black text-xs uppercase tracking-[0.2em] py-4 rounded-2xl shadow-xl shadow-green-900/20 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <LogIn className="w-4 h-4 group-hover:scale-110 transition-transform" />
              {loading ? 'Authenticating...' : 'Sign In Now'}
            </button>

            <div className="text-center pt-4 space-y-3">
              <p className="text-xs font-bold text-gray-400">
                New to the platform?{' '}
                <a href="/signup" className="text-green-700 hover:text-green-600 transition-colors border-b-2 border-green-700/20">Create Account</a>
              </p>
              <a href="#" className="block text-[10px] font-black uppercase tracking-widest text-gray-300 hover:text-green-600 transition-colors">
                Forgot your credentials?
              </a>
            </div>
          </form>
        </div>
      </div>

      <div className="absolute bottom-8 w-full text-center">
        <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.3em]">
          Service and Humility • © 2026 NYSC
        </p>
      </div>
    </main>
  )
}

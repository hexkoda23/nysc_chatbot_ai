"use client"
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getUser, isAuthed, signOut } from '@/lib/auth'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'
import {
  Globe,
  ChevronDown,
  LogOut,
  MessageSquare,
  BookOpen,
  CreditCard,
  MapPin,
  UserCheck,
  ShieldCheck,
  ArrowRight
} from 'lucide-react'

export default function WelcomePage() {
  const router = useRouter()
  const { t, lang, setLang } = useI18n()
  const [name, setName] = useState<string>('Member')
  const [showLang, setShowLang] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    if (!isAuthed()) router.replace('/login')
    const u = getUser()
    if (u?.name) setName(u.name.split(' ')[0])

    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [router])

  const languages = [
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'yo', label: 'Yorùbá', flag: '🇳🇬' },
    { code: 'ha', label: 'Hausa', flag: '🇳🇬' },
    { code: 'ig', label: 'Igbo', flag: '🇳🇬' },
  ]

  const cards = [
    {
      icon: <CreditCard className="w-6 h-6 text-green-600" />,
      title: t('welcome_card_allowance') || 'Monthly Allowance',
      desc: 'Ask about your N77,000 monthly allowance, payment dates and eligibility.',
      href: '/app',
      color: 'hover:border-green-400 group',
    },
    {
      icon: <UserCheck className="w-6 h-6 text-blue-600" />,
      title: t('welcome_card_redeploy') || 'Redeployment',
      desc: 'Learn how to apply for redeployment, valid reasons and required documents.',
      href: '/app',
      color: 'hover:border-blue-400 group',
    },
    {
      icon: <MapPin className="w-6 h-6 text-yellow-600" />,
      title: t('welcome_card_ppa') || 'PPA & Posting',
      desc: 'Find your Place of Primary Assignment and understand your posting rights.',
      href: '/app',
      color: 'hover:border-yellow-400 group',
    },
    {
      icon: <BookOpen className="w-6 h-6 text-purple-600" />,
      title: t('welcome_card_mobil') || 'Mobilization',
      desc: 'Get information on call-up letters, camp dates and registration steps.',
      href: '/app',
      color: 'hover:border-purple-400 group',
    },
    {
      icon: <ShieldCheck className="w-6 h-6 text-red-600" />,
      title: 'Decree & Bye-Laws',
      desc: 'Read the NYSC Act, Decree and official corps bye-laws and regulations.',
      href: '/app',
      color: 'hover:border-red-400 group',
    },
    {
      icon: <MessageSquare className="w-6 h-6 text-teal-600" />,
      title: 'CDS & SAED',
      desc: 'Explore Community Development Service groups and skill acquisition options.',
      href: '/app',
      color: 'hover:border-teal-400 group',
    },
  ]

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-green-800/95 backdrop-blur-md shadow-lg py-1.5' : 'bg-green-800 py-2.5'}`}>
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between">
          <div className="flex items-center gap-2 hover:opacity-90 transition-opacity cursor-pointer" onClick={() => router.push('/')}>
            <div className="relative w-8 h-8 md:w-10 md:h-10">
              <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" fill className="rounded-full bg-white p-0.5" />
            </div>
            <div className="hidden xs:block text-white">
              <div className="text-[10px] md:text-xs font-black tracking-tighter leading-none uppercase">National Youth</div>
              <div className="text-[8px] md:text-[10px] font-bold text-green-300 uppercase">Service Corps</div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 md:gap-4">
            {/* Language Selector */}
            <div className="relative">
              <button
                onClick={() => setShowLang(!showLang)}
                className="flex items-center gap-1 bg-white/10 hover:bg-white/20 text-white px-2.5 py-1.5 rounded-full border border-white/10 transition-all text-[10px] md:text-xs font-bold"
              >
                <Globe className="w-3.5 h-3.5" />
                <span className="hidden xs:inline">{languages.find(l => l.code === lang)?.label}</span>
                <ChevronDown className={`w-3 h-3 transition-transform duration-300 ${showLang ? 'rotate-180' : ''}`} />
              </button>

              {showLang && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowLang(false)} />
                  <div className="absolute right-0 mt-3 w-48 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 overflow-hidden z-20 animate-in fade-in zoom-in duration-200 origin-top-right ring-1 ring-black/5">
                    <div className="px-4 py-2 text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-100">Select Language</div>
                    {languages.map((l) => (
                      <button
                        key={l.code}
                        onClick={() => { setLang(l.code as any); setShowLang(false) }}
                        className={`w-full flex items-center justify-between px-4 py-3 text-xs transition-colors ${lang === l.code ? 'bg-green-50 text-green-700 font-bold' : 'text-gray-600 hover:bg-gray-50'}`}
                      >
                        <span className="flex items-center gap-3">
                          <span className="text-lg leading-none">{l.flag}</span>
                          {l.label}
                        </span>
                        {lang === l.code && <div className="w-2 h-2 rounded-full bg-green-600 shadow-sm" />}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="flex items-center gap-1.5">
              <div className="flex items-center gap-1.5 bg-white/10 backdrop-blur-sm rounded-full px-1.5 py-1 border border-white/10 shadow-inner">
                <div className="h-6 w-6 md:h-7 md:w-7 rounded-full bg-gradient-to-tr from-green-500 to-green-400 flex items-center justify-center text-white font-bold text-[10px] md:text-xs ring-2 ring-white/20 shadow-lg">
                  {name[0]?.toUpperCase()}
                </div>
                <span className="hidden md:inline text-white text-[11px] font-black tracking-tight pr-1">{name}</span>
              </div>
              <button
                onClick={() => { signOut(); router.replace('/login') }}
                className="group flex items-center gap-1.5 bg-white/5 hover:bg-red-500 text-white px-2.5 py-1.5 rounded-full transition-all duration-300 border border-white/10"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5 text-red-400 group-hover:text-white transition-colors" />
                <span className="hidden xs:inline text-[9px] font-black uppercase tracking-widest">Exit</span>
              </button>
            </div>
          </div>
        </div>
      </header>
      <div className="h-12 md:h-14" /> {/* Spacer */}

      {/* Hero Banner with Glassmorphism Overlay */}
      <div className="relative h-[300px] md:h-[400px] flex items-center overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: "url('/NYSC-ORIENTATION-CAMPS-IN-NIGERIA-1-1024x531.jpg')" }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-green-950 via-green-900/90 to-black/40" />
        <div className="relative z-10 max-w-7xl mx-auto px-6 w-full pt-8 md:pt-16">
          <div className="flex items-center gap-2 mb-3 animate-in fade-in slide-in-from-left duration-700">
            <div className="h-0.5 w-6 md:w-10 bg-green-500 rounded-full" />
            <p className="text-green-400 text-[9px] md:text-[11px] font-black tracking-[0.3em] md:tracking-[0.4em] uppercase shadow-sm">Official AI Guide</p>
          </div>
          <h1 className="text-3xl md:text-6xl font-black text-white leading-[1.1] tracking-tighter drop-shadow-xl animate-in fade-in slide-in-from-left duration-700 delay-100">
            {t('welcome_hello').replace('{name}', name)}!
          </h1>
          <p className="text-green-50/90 mt-4 md:mt-6 text-xs md:text-lg max-w-2xl font-medium leading-relaxed drop-shadow-lg animate-in fade-in slide-in-from-left duration-700 delay-200">
            Your instant, smart companion for all NYSC inquiries. From allowances to postings, we speak your language and have the answers.
          </p>
          <div className="mt-10 flex flex-wrap gap-5 animate-in fade-in slide-in-from-bottom duration-1000 delay-300">
            <a
              href="/app"
              className="group flex items-center gap-3 bg-white text-green-900 font-extrabold text-sm uppercase tracking-widest px-8 py-4 rounded-full shadow-[0_20px_50px_rgba(0,0,0,0.3)] hover:shadow-green-500/40 hover:bg-green-50 hover:scale-105 transition-all duration-300"
            >
              <MessageSquare className="w-5 h-5 text-green-600 transition-transform group-hover:rotate-12" />
              {t('get_started') || 'Launch Assistant'}
            </a>
            <button className="hidden sm:flex items-center gap-2 bg-white/10 backdrop-blur-md text-white border border-white/20 font-black text-xs uppercase tracking-widest px-8 py-4 rounded-full hover:bg-white/20 hover:scale-105 transition-all duration-300">
              How it works
            </button>
          </div>
        </div>
      </div>

      {/* Topics Grid */}
      <section className="flex-1 max-w-7xl mx-auto px-4 -mt-12 md:-mt-16 relative z-20 pb-20 w-full">
        <div className="bg-white/70 backdrop-blur-2xl rounded-[40px] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.1)] border border-white/50 p-8 md:p-12">
          <div className="flex items-end justify-between mb-12">
            <div>
              <h2 className="text-gray-900 font-black text-3xl tracking-tight leading-none">{t('welcome_help')}</h2>
              <div className="h-1.5 w-16 bg-green-600 mt-4 rounded-full" />
            </div>
            <a href="/app" className="flex items-center gap-2 text-green-700 text-xs font-black uppercase tracking-widest hover:text-green-500 group transition-colors">
              Explore All
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1.5 transition-transform" />
            </a>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {cards.map((c, i) => (
              <a
                key={i}
                href={c.href}
                className={`bg-white rounded-[32px] border border-gray-100 p-8 shadow-sm hover:shadow-[0_40px_80px_-20px_rgba(21,128,61,0.12)] transition-all duration-500 hover:-translate-y-3 group relative overflow-hidden ${c.color}`}
              >
                <div className="absolute top-0 right-0 p-4 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-700 scale-150">
                  {c.icon}
                </div>
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gray-50 mb-8 group-hover:bg-green-600 group-hover:scale-110 transition-all duration-500 shadow-inner group-hover:shadow-green-200 group-hover:text-white">
                  <span className="transition-colors group-hover:text-white">{c.icon}</span>
                </div>
                <div className="font-black text-gray-900 text-lg mb-3 tracking-tight group-hover:text-green-800 transition-colors uppercase">{c.title}</div>
                <p className="text-xs text-gray-500 font-semibold leading-relaxed mb-8">{c.desc}</p>
                <div className="flex items-center justify-between">
                  <div className="text-[11px] font-black uppercase tracking-[0.2em] text-green-700 flex items-center gap-2">
                    {t('welcome_card_tap')}
                  </div>
                  <div className="w-10 h-10 rounded-full bg-green-50 flex items-center justify-center -translate-x-4 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 transition-all duration-500 shadow-sm border border-green-100">
                    <ArrowRight className="w-4 h-4 text-green-700" />
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Stats/Info Bar */}
      <div className="bg-white border-y border-gray-100 py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="bg-green-50 rounded-2xl px-6 py-4 border border-green-100 flex items-center gap-4">
            <div className="h-10 w-10 rounded-full bg-green-600 flex items-center justify-center text-white font-bold">₦</div>
            <div>
              <div className="text-[10px] font-black text-green-800 uppercase tracking-widest opacity-60">Current Allowance</div>
              <div className="text-lg font-black text-green-900 tracking-tighter leading-none mt-0.5">77,000 / month</div>
            </div>
          </div>

          <div className="flex flex-wrap justify-center gap-6">
            <div className="text-center">
              <div className="text-xl font-black text-gray-900 leading-none">100%</div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">Grounded</div>
            </div>
            <div className="w-px h-8 bg-gray-100" />
            <div className="text-center">
              <div className="text-xl font-black text-gray-900 leading-none">Instant</div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">Responses</div>
            </div>
            <div className="w-px h-8 bg-gray-100" />
            <div className="text-center">
              <div className="text-xl font-black text-gray-900 leading-none">Verified</div>
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">Sources</div>
            </div>
          </div>

          <div className="flex gap-4">
            <a href="https://www.nysc.gov.ng" target="_blank" rel="noopener noreferrer" className="p-3 bg-gray-50 rounded-full hover:bg-green-50 transition-colors border border-gray-100 uppercase text-[9px] font-black tracking-widest text-gray-600 hover:text-green-700">Official Site</a>
            <a href="https://portal.nysc.org.ng" target="_blank" rel="noopener noreferrer" className="p-3 bg-gray-50 rounded-full hover:bg-green-50 transition-colors border border-gray-100 uppercase text-[9px] font-black tracking-widest text-gray-600 hover:text-green-700">NYSC Portal</a>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-green-900 text-white pt-16 pb-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-start justify-between gap-12 pb-12 border-b border-white/10">
            <div className="max-w-xs">
              <div className="flex items-center gap-3 mb-6">
                <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" width={48} height={48} className="rounded-full bg-white p-1 shadow-2xl shadow-black/20" />
                <div className="font-black text-lg tracking-tighter uppercase leading-none">NYSC<br /><span className="text-green-400">Assistant</span></div>
              </div>
              <p className="text-xs text-green-100/60 font-medium leading-relaxed">
                Empowering every Nigerian Youth Service Corps member with instant, accurate, and multi-lingual official information to navigate their service year with confidence.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-12">
              <div>
                <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-green-500 mb-6 underline underline-offset-8 decoration-2 decoration-green-500/30">Connect</h4>
                <ul className="space-y-4 text-xs font-bold text-green-100/80">
                  <li><a href="#" className="hover:text-white transition-colors">Instagram</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">X (Twitter)</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">LinkedIn</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-green-500 mb-6 underline underline-offset-8 decoration-2 decoration-green-500/30">Resources</h4>
                <ul className="space-y-4 text-xs font-bold text-green-100/80">
                  <li><a href="/app" className="hover:text-white transition-colors">Chat Assistant</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Policy Docs</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Camp Safety</a></li>
                </ul>
              </div>
            </div>
          </div>

          <div className="pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-[10px] font-black uppercase tracking-widest text-green-100/40">
            <div>© 2026 National Youth Service Corps. Service and Humility.</div>
            <div className="flex gap-8">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Support</a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  )
}

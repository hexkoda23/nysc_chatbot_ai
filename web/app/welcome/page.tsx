"use client"
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getUser, isAuthed, signOut } from '../../lib/auth'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'
import { motion } from 'framer-motion'
import {
  Globe, ChevronDown, LogOut, MessageSquare, BookOpen, CreditCard,
  MapPin, UserCheck, ShieldCheck, ArrowRight, Menu, X
} from 'lucide-react'

const GREETING = () => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

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
    { code: 'en', label: 'English' },
    { code: 'yo', label: 'Yorùbá' },
    { code: 'ha', label: 'Hausa' },
    { code: 'ig', label: 'Igbo' },
  ]

  const cards = [
    {
      icon: CreditCard,
      title: t('welcome_card_allowance') || 'Monthly Allowance',
      desc: 'Ask about your N77,000 monthly allowance, payment dates and eligibility.',
      href: '/app',
      iconColor: 'text-[var(--accent-start)]',
      iconBg: 'bg-green-50 dark:bg-green-900/20',
      hoverBorder: 'hover:border-[var(--accent-end)]',
    },
    {
      icon: UserCheck,
      title: t('welcome_card_redeploy') || 'Redeployment',
      desc: 'Learn how to apply for redeployment, valid reasons and required documents.',
      href: '/app',
      iconColor: 'text-blue-600',
      iconBg: 'bg-blue-50 dark:bg-blue-900/20',
      hoverBorder: 'hover:border-blue-400',
    },
    {
      icon: MapPin,
      title: t('welcome_card_ppa') || 'PPA & Posting',
      desc: 'Find your Place of Primary Assignment and understand your posting rights.',
      href: '/app',
      iconColor: 'text-amber-600',
      iconBg: 'bg-amber-50 dark:bg-amber-900/20',
      hoverBorder: 'hover:border-amber-400',
    },
    {
      icon: BookOpen,
      title: t('welcome_card_mobil') || 'Mobilization',
      desc: 'Get information on call-up letters, camp dates and registration steps.',
      href: '/app',
      iconColor: 'text-purple-600',
      iconBg: 'bg-purple-50 dark:bg-purple-900/20',
      hoverBorder: 'hover:border-purple-400',
    },
    {
      icon: ShieldCheck,
      title: 'Decree & Bye-Laws',
      desc: 'Read the NYSC Act, Decree and official corps bye-laws and regulations.',
      href: '/app',
      iconColor: 'text-red-600',
      iconBg: 'bg-red-50 dark:bg-red-900/20',
      hoverBorder: 'hover:border-red-400',
    },
    {
      icon: MessageSquare,
      title: t('welcome_card_ai') || 'Ask AI Anything',
      desc: 'Get instant answers to any NYSC-related question in your preferred language.',
      href: '/app',
      iconColor: 'text-[var(--accent-gold)]',
      iconBg: 'bg-yellow-50 dark:bg-yellow-900/20',
      hoverBorder: 'hover:border-[var(--accent-gold)]',
    },
  ]

  return (
    <motion.main
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="min-h-screen"
      style={{ background: 'var(--bg-primary)' }}
    >
      {/* ── Sticky Nav ───────────────────────────────── */}
      <nav
        className={`sticky top-0 z-40 flex items-center justify-between px-6 py-3 transition-all duration-300 ${scrolled ? 'bg-[var(--bg-secondary)]/80 backdrop-blur-xl border-b border-[var(--border-default)] shadow-sm' : 'bg-transparent'
          }`}
      >
        <button onClick={() => router.push('/')} className="flex items-center gap-2.5">
          <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC" width={32} height={32} className="rounded-full" />
          <span className="font-display text-base text-primary hidden sm:block">NYSC AI</span>
        </button>

        <div className="flex items-center gap-3">
          {/* Language selector */}
          <div className="relative">
            <button
              onClick={() => setShowLang(!showLang)}
              className="flex items-center gap-1.5 border border-[var(--border-default)] text-secondary hover:text-primary hover:border-[var(--accent-end)] px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
            >
              <Globe className="w-3.5 h-3.5" />
              {languages.find(l => l.code === lang)?.label}
              <ChevronDown className={`w-3 h-3 transition-transform ${showLang ? 'rotate-180' : ''}`} />
            </button>
            {showLang && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowLang(false)} />
                <div className="absolute right-0 mt-2 w-36 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-xl shadow-xl z-20 overflow-hidden">
                  {languages.map(l => (
                    <button
                      key={l.code}
                      onClick={() => { setLang(l.code as any); setShowLang(false) }}
                      className={`w-full px-4 py-2.5 text-left text-xs transition-colors ${lang === l.code ? 'bg-[var(--sidebar-bg)] text-[var(--accent-start)] font-semibold' : 'text-secondary hover:bg-[var(--bg-primary)]'}`}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Logout */}
          <button
            onClick={() => { signOut(); router.replace('/login') }}
            className="flex items-center gap-1.5 border border-[var(--border-default)] text-secondary hover:text-primary hover:border-red-400 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t('chat_logout') || 'Logout'}</span>
          </button>
        </div>
      </nav>

      {/* ── Hero Greeting ─────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 pt-12 pb-8">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1 }}
        >
          <div className="text-xs font-black text-secondary uppercase tracking-widest mb-2">{GREETING()}</div>
          <h1 className="font-display text-4xl md:text-5xl text-primary">
            {name} <span className="not-italic">👋</span>
          </h1>
          <p className="text-secondary text-sm mt-2 max-w-xl">
            Your NYSC AI guide is ready. Ask anything about your service year.
          </p>
        </motion.div>

        {/* Quick launch button */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="mt-6"
        >
          <a
            href="/app"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)] hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-green-900/20"
          >
            <MessageSquare className="w-4 h-4" /> Start Chatting <ArrowRight className="w-4 h-4" />
          </a>
        </motion.div>
      </section>

      {/* ── Action Cards ──────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 pb-16">
        <div className="text-xs font-black text-secondary uppercase tracking-widest mb-5">Quick Access</div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card, i) => {
            const Icon = card.icon
            return (
              <motion.a
                key={card.title}
                href={card.href}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.15 + i * 0.06 }}
                className={`group flex flex-col gap-4 rounded-2xl border border-[var(--border-default)] ${card.hoverBorder} bg-[var(--bg-secondary)] hover:-translate-y-1 hover:shadow-xl hover:shadow-green-900/10 transition-all duration-300 p-6 cursor-pointer`}
              >
                <div className={`inline-flex items-center justify-center w-11 h-11 rounded-xl ${card.iconBg} group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className={`w-5 h-5 ${card.iconColor}`} />
                </div>
                <div>
                  <h3 className="font-semibold text-primary text-sm mb-1">{card.title}</h3>
                  <p className="text-xs text-secondary leading-relaxed">{card.desc}</p>
                </div>
                <div className={`flex items-center gap-1 text-xs font-semibold ${card.iconColor} opacity-0 group-hover:opacity-100 transition-opacity`}>
                  Open <ArrowRight className="w-3 h-3" />
                </div>
              </motion.a>
            )
          })}
        </div>
      </section>
    </motion.main>
  )
}

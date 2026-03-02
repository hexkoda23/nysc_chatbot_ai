"use client"
import { useEffect, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { ThemeToggle } from './theme-toggle'
import { GetStartedButton } from '@/components/get-started'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'

export function Header() {
  const { scrollY } = useScroll()
  const [scrolled, setScrolled] = useState(false)
  const [mounted, setMounted] = useState(false)
  const { t } = useI18n()

  useEffect(() => setMounted(true), [])
  useEffect(() => {
    const unsub = scrollY.on('change', v => setScrolled(v > 40))
    return unsub
  }, [scrollY])

  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled
          ? 'bg-[#040D06]/80 backdrop-blur-xl border-b border-white/8 shadow-lg shadow-black/20'
          : 'bg-transparent border-b border-transparent'
        }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo + Brand */}
        <a href="/" className="flex items-center gap-2.5 group">
          <Image
            src="/NYSC-Nigeria-Logo.png"
            alt="NYSC Logo"
            width={32}
            height={32}
            className="rounded-full group-hover:opacity-90 transition-opacity"
          />
          <div className="flex flex-col leading-tight">
            <span className="font-display text-white text-base leading-none">NYSC AI</span>
            <span className="text-[var(--accent-gold)] text-[8px] tracking-[0.2em] uppercase hidden sm:block">
              Official Assistant
            </span>
          </div>
          <span className="text-[9px] px-1.5 py-0.5 rounded-full border border-[var(--accent-gold)]/40 text-[var(--accent-gold)] ml-1 font-semibold">
            Beta
          </span>
        </a>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-7 text-[13px] text-white/60">
          <a href="#features" className="hover:text-white transition-colors duration-150">{t('nav_features')}</a>
          <a href="#how" className="hover:text-white transition-colors duration-150">{t('nav_how')}</a>
          <a href="#security" className="hover:text-white transition-colors duration-150">{t('nav_security')}</a>
          <a href="#faq" className="hover:text-white transition-colors duration-150">{t('nav_faq')}</a>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {mounted && <ThemeToggle />}
          <a
            href="/login"
            className="hidden sm:inline-flex items-center px-4 py-2 rounded-lg border border-white/15 text-white/70 hover:text-white hover:border-white/30 text-xs font-medium transition-all duration-200"
          >
            {t('login')}
          </a>
          <a
            href="/app"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)] hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-md shadow-green-900/30"
          >
            {t('get_started') || 'Get Started'}
          </a>
        </div>
      </div>
    </motion.header>
  )
}

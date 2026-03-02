"use client"
import { useEffect, useState } from 'react'
import { motion, useScroll } from 'framer-motion'
import { ThemeToggle } from './theme-toggle'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'
import { Globe, ChevronDown } from 'lucide-react'

type LangOption = { code: string; label: string }

interface HeaderProps {
  lang?: string
  onLangChange?: (l: 'en' | 'yo' | 'ig' | 'ha') => void
  langOptions?: LangOption[]
}

export function Header({ lang: externalLang, onLangChange, langOptions }: HeaderProps = {}) {
  const { scrollY } = useScroll()
  const [scrolled, setScrolled] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [showLang, setShowLang] = useState(false)
  const { t, lang: uiLang, setLang } = useI18n()

  const currentLang = externalLang || uiLang
  const options: LangOption[] = langOptions || [
    { code: 'en', label: 'English' },
    { code: 'yo', label: 'Yorùbá' },
    { code: 'ig', label: 'Igbo' },
    { code: 'ha', label: 'Hausa' },
  ]
  const currentLabel = options.find(o => o.code === currentLang)?.label || 'English'

  useEffect(() => setMounted(true), [])
  useEffect(() => {
    const unsub = scrollY.on('change', v => setScrolled(v > 40))
    return unsub
  }, [scrollY])

  const handleLang = (code: string) => {
    setShowLang(false)
    if (onLangChange) {
      onLangChange(code as any)
    } else {
      setLang(code as any)
      try { localStorage.setItem('nysc_lang', code) } catch { }
    }
  }

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
          <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" width={32} height={32} className="rounded-full group-hover:opacity-90 transition-opacity" />
          <div className="flex flex-col leading-tight">
            <span className="font-display text-white text-base leading-none">NYSC AI</span>
            <span className="text-[var(--accent-gold)] text-[8px] tracking-[0.2em] uppercase hidden sm:block">Official Assistant</span>
          </div>
          <span className="text-[9px] px-1.5 py-0.5 rounded-full border border-[var(--accent-gold)]/40 text-[var(--accent-gold)] ml-1 font-semibold">Beta</span>
        </a>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-7 text-[13px] text-white/60">
          <a href="#features" className="hover:text-white transition-colors duration-150">{t('nav_features')}</a>
          <a href="#how" className="hover:text-white transition-colors duration-150">{t('nav_how')}</a>
          <a href="#security" className="hover:text-white transition-colors duration-150">{t('nav_security')}</a>
          <a href="#faq" className="hover:text-white transition-colors duration-150">{t('nav_faq')}</a>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {mounted && <ThemeToggle />}

          {/* Language dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowLang(!showLang)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-white/15 text-white/70 hover:text-white hover:border-white/30 text-xs font-medium transition-all duration-200"
            >
              <Globe className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{currentLabel}</span>
              <ChevronDown className={`w-3 h-3 transition-transform ${showLang ? 'rotate-180' : ''}`} />
            </button>
            {showLang && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowLang(false)} />
                <div className="absolute right-0 mt-2 w-36 bg-[#0A1A0C] backdrop-blur-xl rounded-xl shadow-2xl border border-white/10 overflow-hidden z-20">
                  {options.map(o => (
                    <button
                      key={o.code}
                      onClick={() => handleLang(o.code)}
                      className={`w-full px-4 py-2.5 text-left text-xs transition-colors ${currentLang === o.code ? 'bg-white/15 text-white font-semibold' : 'text-white/60 hover:bg-white/8 hover:text-white'}`}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Login */}
          <a href="/login" className="hidden sm:inline-flex items-center px-4 py-2 rounded-lg border border-white/15 text-white/70 hover:text-white hover:border-white/30 text-xs font-medium transition-all duration-200">
            {t('login')}
          </a>
        </div>
      </div>
    </motion.header>
  )
}

"use client"
import { useEffect, useState } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { ThemeToggle } from './theme-toggle'
import { GetStartedButton } from '@/components/get-started'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'

export function Header() {
  const { scrollY } = useScroll()
  const height = useTransform(scrollY, [0, 120], [72, 60])
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  const { t } = useI18n()

  return (
    <motion.header
      style={{ height }}
      className="sticky top-0 z-40 w-full border-b border-green-900/40 backdrop-blur bg-green-700/95"
    >
      <div className="container flex items-center justify-between h-full">
        {/* Logo + Brand */}
        <div className="flex items-center gap-2.5">
          <Image
            src="/NYSC-Nigeria-Logo.png"
            alt="NYSC Logo"
            width={36}
            height={36}
            className="rounded-full"
          />
          <div className="flex flex-col leading-tight">
            <span className="text-white font-bold text-sm tracking-wider">NYSC AI</span>
            <span className="text-green-300 text-[9px] tracking-widest hidden sm:block">SERVICE AND HUMILITY</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full border border-green-400/60 text-green-200 ml-1">
            Beta
          </span>
        </div>

        {/* Nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm text-green-100">
          <a href="#features" className="hover:text-white transition-colors">{t('nav_features')}</a>
          <a href="#how" className="hover:text-white transition-colors">{t('nav_how')}</a>
          <a href="#demo" className="hover:text-white transition-colors">{t('nav_demo')}</a>
          <a href="#security" className="hover:text-white transition-colors">{t('nav_security')}</a>
          <a href="#faq" className="hover:text-white transition-colors">{t('nav_faq')}</a>
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {mounted && <ThemeToggle />}
          <a
            href="/login"
            className="hidden sm:inline-flex rounded-xl border border-green-400/60 text-green-100 hover:text-white px-4 py-1.5 text-sm transition-colors"
          >
            {t('login')}
          </a>
          <GetStartedButton className="px-4 py-1.5 text-sm bg-white text-green-700 hover:bg-green-50 rounded-xl font-semibold" label={t('get_started') || 'Enter'} />
        </div>
      </div>
    </motion.header>
  )
}

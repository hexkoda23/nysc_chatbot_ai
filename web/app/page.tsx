"use client"
import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Header } from '@/components/header'
import { Footer } from '@/components/footer'
import { useI18n } from '@/components/i18n'
import {
  MessageSquare, MapPin, FileText, DollarSign, ClipboardList, Globe2,
  Lock, CheckCircle, RefreshCw, ArrowRight, Plus, Minus
} from 'lucide-react'

const fadeUp = {
  initial: { opacity: 0, y: 28 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.5, ease: 'easeOut' },
}

const featureIcons = [MessageSquare, MapPin, FileText, DollarSign, ClipboardList, Globe2]
const securityIcons = [Lock, CheckCircle, RefreshCw]

export default function Page() {
  const { t, setLang, lang } = useI18n()
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  const handleLangChange = async (l: 'en' | 'yo' | 'ig' | 'ha') => {
    setLang(l)
    try { localStorage.setItem('nysc_lang', l) } catch { }
  }

  const LANG_OPTIONS = [
    { code: 'en', label: 'English' },
    { code: 'yo', label: 'Yorùbá' },
    { code: 'ig', label: 'Igbo' },
    { code: 'ha', label: 'Hausa' },
  ]

  const features = [
    [t('feature_qa_t'), t('feature_qa_s')],
    [t('feature_ppa_t'), t('feature_ppa_s')],
    [t('feature_callup_t'), t('feature_callup_s')],
    [t('feature_allowance_t'), t('feature_allowance_s')],
    [t('feature_mobil_t'), t('feature_mobil_s')],
    [t('feature_voice_t'), t('feature_voice_s')],
  ]

  const howSteps = [t('how_1'), t('how_2'), t('how_3'), t('how_4')]

  const security = [
    [t('security_enc_t'), t('security_enc_s')],
    [t('security_src_t'), t('security_src_s')],
    [t('security_upd_t'), t('security_upd_s')],
  ]

  const testimonials = [
    [t('testi_1_n'), t('testi_1_q')],
    [t('testi_2_n'), t('testi_2_q')],
    [t('testi_3_n'), t('testi_3_q')],
  ]

  const faq = [
    [t('faq_1_q'), t('faq_1_a')],
    [t('faq_2_q'), t('faq_2_a')],
    [t('faq_3_q'), t('faq_3_a')],
    [t('faq_4_q'), t('faq_4_a')],
    [t('faq_5_q'), t('faq_5_a')],
    [t('faq_6_q'), t('faq_6_a')],
  ]


  return (
    <motion.main
      key={lang}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="overflow-x-hidden"
    >
      <Header lang={lang as any} onLangChange={handleLangChange} langOptions={LANG_OPTIONS} />

      {/* ── HERO ─────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center hero-mesh overflow-hidden">
        <div className="absolute inset-0 hero-grid-overlay opacity-60" />

        {/* Floating chat bubble */}
        <div className="absolute right-8 top-24 md:right-20 md:top-40 hidden md:block animate-float z-10">
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl px-4 py-3 text-white text-sm max-w-[220px] shadow-2xl">
            <div className="text-[10px] text-green-300 font-bold mb-1">{t('brand')}</div>
            <p className="leading-snug opacity-90">{t('hero_bubble')}</p>
          </div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-32 md:py-40 w-full">
          {/* Eyebrow */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }} className="flex items-center gap-3 mb-6">
            <div className="h-px w-12 bg-[var(--accent-gold)]" />
            <span className="text-[var(--accent-gold)] text-xs font-black tracking-[0.3em] uppercase">{t('brand_tagline')}</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            key={t('hero_title')}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="font-display text-5xl sm:text-6xl md:text-7xl text-white leading-[1.08] tracking-tight max-w-3xl mb-6"
          >
            {t('hero_title')}
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            key={t('hero_subtitle')}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-green-100/75 text-base md:text-lg max-w-xl leading-relaxed mb-10"
          >
            {t('hero_subtitle')}
          </motion.p>

          {/* CTAs */}
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.48 }} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <a href="/app" className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-semibold text-white bg-gradient-to-r from-[#0B7A33] to-[#22C55E] hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 shadow-lg shadow-green-900/40">
              {t('get_started')} <ArrowRight className="w-4 h-4" />
            </a>
            <a href="/how-it-works" className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl font-semibold border border-white/25 text-white hover:border-[var(--accent-end)] hover:bg-white/5 transition-all duration-200">
              {t('nav_how')}
            </a>
          </motion.div>

          {/* Chips */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.65 }} className="flex flex-wrap gap-3 mt-8">
            {[t('chip_secure'), t('chip_ai'), t('chip_updated')].map(chip => (
              <span key={chip} className="text-[11px] font-semibold text-green-200 border border-green-600/40 bg-green-900/40 px-3 py-1 rounded-full backdrop-blur-sm">{chip}</span>
            ))}
          </motion.div>

        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[var(--bg-primary)] to-transparent" />
      </section>

      {/* ── FEATURES ─────────────────────────────────────── */}
      <section id="features" className="py-24 max-w-7xl mx-auto px-6">
        <motion.div {...fadeUp} className="text-center mb-16">
          <span className="text-xs font-black tracking-[0.3em] text-[var(--accent-start)] uppercase">{t('features_title')}</span>
          <h2 className="font-display text-4xl md:text-5xl text-primary mt-3">{t('features_title')}</h2>
        </motion.div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(([title, desc], i) => {
            const Icon = featureIcons[i]
            const isFeatured = i === 3
            return (
              <motion.div
                key={i}
                {...fadeUp}
                transition={{ duration: 0.5, delay: i * 0.07, ease: 'easeOut' }}
                className={`relative group rounded-2xl border ${isFeatured ? 'border-[var(--accent-gold)]/40' : 'border-[var(--border-default)]'} bg-secondary hover:border-[var(--accent-end)] hover:-translate-y-1 hover:shadow-xl hover:shadow-green-900/10 transition-all duration-300 p-7 cursor-pointer overflow-hidden`}
              >
                {isFeatured && <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-[var(--accent-gold)] to-[var(--accent-gold)]/30 rounded-l-2xl" />}
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] mb-5 shadow-lg shadow-green-900/20 group-hover:scale-110 transition-transform duration-300">
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-primary text-base mb-2">{title}</h3>
                <p className="text-sm text-secondary leading-relaxed">{desc}</p>
                {isFeatured && <div className="absolute top-4 right-4 text-[9px] font-black text-[var(--accent-gold)] uppercase tracking-widest border border-[var(--accent-gold)]/30 rounded-full px-2 py-0.5">{t('featured')}</div>}
              </motion.div>
            )
          })}
        </div>
      </section>

      {/* ── HOW IT WORKS ─────────────────────────────────── */}
      <section id="how" className="py-24 bg-surface relative overflow-hidden">
        <div className="absolute inset-0 hero-grid-overlay opacity-30 dark:opacity-10" />
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <motion.div {...fadeUp} className="text-center mb-16">
            <h2 className="font-display text-4xl md:text-5xl text-primary">{t('how_title')}</h2>
          </motion.div>
          {/* Desktop */}
          <div className="hidden md:flex items-start gap-0 relative">
            <div className="absolute top-8 left-[10%] right-[10%] h-px border-t-2 border-dashed border-[var(--border-default)]" />
            {howSteps.map((step, i) => (
              <motion.div key={i} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.12 }} className="flex-1 flex flex-col items-center text-center relative z-10 px-4">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] flex items-center justify-center text-white text-2xl font-black shadow-xl mb-5 ring-4 ring-[var(--bg-primary)]">{i + 1}</div>
                <p className="text-sm font-semibold text-primary leading-snug">{step}</p>
              </motion.div>
            ))}
          </div>
          {/* Mobile */}
          <div className="md:hidden space-y-6">
            {howSteps.map((step, i) => (
              <motion.div key={i} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.1 }} className="flex items-center gap-5">
                <div className="w-12 h-12 flex-shrink-0 rounded-full bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] flex items-center justify-center text-white text-lg font-black shadow-lg">{i + 1}</div>
                <p className="text-sm font-semibold text-primary">{step}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SECURITY ─────────────────────────────────────── */}
      <section id="security" className="py-24 max-w-7xl mx-auto px-6">
        <motion.div {...fadeUp} className="text-center mb-16">
          <h2 className="font-display text-4xl md:text-5xl text-primary">{t('security_title')}</h2>
        </motion.div>
        <div className="grid gap-6 md:grid-cols-3">
          {security.map(([title, desc], i) => {
            const Icon = securityIcons[i]
            return (
              <motion.div key={i} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.1 }} className="rounded-2xl border border-[var(--border-default)] bg-secondary p-8 text-center hover:border-[var(--accent-end)] hover:-translate-y-1 transition-all duration-300">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] mb-5 shadow-lg">
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-semibold text-primary mb-2">{title}</h3>
                <p className="text-sm text-secondary leading-relaxed">{desc}</p>
              </motion.div>
            )
          })}
        </div>
      </section>

      {/* ── TESTIMONIALS ─────────────────────────────────── */}
      <section className="py-24 relative overflow-hidden grain-overlay">
        <div className="absolute inset-0 bg-surface" />
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <motion.div {...fadeUp} className="text-center mb-16">
            <h2 className="font-display text-4xl md:text-5xl text-primary">{t('testimonials_title')}</h2>
          </motion.div>
          <div className="grid gap-6 md:grid-cols-3">
            {testimonials.map(([name, quote], i) => (
              <motion.div key={i} {...fadeUp} transition={{ duration: 0.5, delay: i * 0.12 }} style={{ marginTop: i === 1 ? 24 : 0 }} className="rounded-2xl border border-[var(--border-default)] bg-secondary p-8 hover:border-[var(--accent-end)] hover:-translate-y-1 transition-all duration-300">
                <div className="font-display text-5xl text-[var(--accent-start)] leading-none mb-4">&ldquo;</div>
                <p className="text-sm text-secondary leading-relaxed italic mb-6">{quote}</p>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] flex items-center justify-center text-white text-xs font-bold">{name[0]}</div>
                  <span className="font-semibold text-sm text-primary">{name}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────── */}
      <section id="faq" className="py-24 max-w-3xl mx-auto px-6">
        <motion.div {...fadeUp} className="text-center mb-16">
          <h2 className="font-display text-4xl md:text-5xl text-primary">{t('faq_title')}</h2>
        </motion.div>
        <div className="space-y-3">
          {faq.map(([q, a], i) => (
            <motion.div key={i} {...fadeUp} transition={{ duration: 0.4, delay: i * 0.06 }} className="rounded-xl border border-[var(--border-default)] bg-secondary overflow-hidden">
              <button className="w-full flex items-center justify-between px-6 py-5 text-left" onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                <span className="font-semibold text-sm text-primary pr-4">{q}</span>
                <span className="flex-shrink-0 w-7 h-7 rounded-full border border-[var(--border-default)] flex items-center justify-center text-[var(--accent-start)]">
                  {openFaq === i ? <Minus className="w-3 h-3" /> : <Plus className="w-3 h-3" />}
                </span>
              </button>
              <AnimatePresence>
                {openFaq === i && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25, ease: 'easeInOut' }} className="overflow-hidden">
                    <div className="px-6 pb-5 text-sm text-secondary leading-relaxed border-t border-[var(--border-default)] pt-4">{a}</div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </section>

      <Footer />
    </motion.main>
  )
}

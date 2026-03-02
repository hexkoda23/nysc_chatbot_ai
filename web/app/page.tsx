"use client"
import { useEffect, useState } from 'react'
import { Header } from '@/components/header'
import { Footer } from '@/components/footer'
import { ChatMock } from '@/components/chat-mock'
import { motion } from 'framer-motion'
import { GetStartedButton } from '@/components/get-started'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'
import { translateTexts } from '../lib/api'

export default function Page() {
  const { t, setLang, lang } = useI18n()
  const [selectedLang, setSelectedLang] = useState<'en' | 'yo' | 'ig' | 'ha'>(lang)
  const [heroTitle, setHeroTitle] = useState('AI That Understands NYSC.')
  const [heroSubtitle, setHeroSubtitle] = useState('Get instant, accurate answers on call-up letters, PPA postings, allowances, mobilization, and official policies.')
  const [features, setFeatures] = useState<[string, string][]>([
    ['Real-time AI Q&A', 'Accurate, policy-grounded answers at any time.'],
    ['PPA Posting Guidance', 'Navigate PPA placement with context-aware advice.'],
    ['Call-up Letter Help', 'Understand timelines and required documentation.'],
    ['Allowance & Payments', 'Up-to-date allowance and payment guidance.'],
    ['Mobilization Checklist', 'Everything you need before reporting.'],
    ['Multilingual Voice Support', 'Inclusive support that scales nationwide.'],
  ])
  const [howSteps, setHowSteps] = useState<string[]>(['Ask a Question', 'AI Understands Context', 'Retrieves Official Information', 'Responds Instantly'])
  const [demoHeading, setDemoHeading] = useState('Interactive Chat Preview')
  const [securityItems, setSecurityItems] = useState<[string, string][]>([
    ['Encrypted Communication', 'All chat and data exchanges use modern encryption.'],
    ['Verified NYSC Sources', 'Grounded in official NYSC materials and updates.'],
    ['Continuous Model Updates', 'Regular improvements for precision and coverage.'],
  ])
  const [testimonials, setTestimonials] = useState<[string, string][]>([
    ['Aisha, Batch B', 'Got step-by-step redeployment instructions — fast and accurate.'],
    ['Chinedu, Stream II', 'Simple PPA change steps and accurate N77,000 allowance info.'],
    ['Zainab, Alumni', 'Reliable answers grounded in official NYSC policy — no guesswork.'],
  ])
  const [faq, setFaq] = useState<[string, string][]>([
    ['What do I need to register for NYSC?', 'You need your NIN, JAMB registration number, matriculation number, a passport photo (white background), and your name on your school’s Senate/Academic Board list. Register on the portal: https://portal.nysc.org.ng/nysc1/ .'],
    ['How do I check if my name is on the Senate List?', 'Open https://portal.nysc.org.ng/nysc2/VerifySenateLists.aspx , select your institution, enter your Matric number, Surname and Date of Birth, then Search. If “No Record Found”, contact your Student Affairs Office.'],
    ['How do I print my call‑up letter?', 'Log in to your NYSC dashboard (https://portal.nysc.org.ng/nysc1/) when posting is released. Click Call‑up Letter and print in colour. Do not laminate; laminated copies are rejected at camp.'],
    ['What is the NYSC monthly allowance?', 'N77,000 per month (from March 2025). Some states and PPAs may pay additional stipends which vary by location and employer.'],
    ['Can I apply for redeployment?', 'Yes. Valid reasons are health, marriage (female only), recognized insecurity states, or DG directive. Apply in camp with documents or via your portal after camp.'],
    ['How can I change my PPA?', 'Obtain a rejection from your current PPA or an acceptance from a new PPA, then submit to your LGI for reposting approval. Continue serving at your current PPA until you receive an official reposting letter.'],
  ])
  useEffect(() => {
    try {
      const saved = localStorage.getItem('nysc_lang')
      if (saved && ['en', 'yo', 'ig', 'ha'].includes(saved)) {
        setSelectedLang(saved as any)
      }
    } catch { }
  }, [])
  const translateAll = async (lang: 'en' | 'yo' | 'ig' | 'ha') => {
    if (lang === 'en') {
      return
    }
    const texts: string[] = [
      heroTitle, heroSubtitle,
      ...features.flat(), ...howSteps, demoHeading,
      ...securityItems.flat(), ...testimonials.map(([, q]) => q),
      ...faq.flat(),
    ]
    const data = await translateTexts(lang, texts)
    const t = Array.isArray(data?.translations) ? (data.translations as string[]) : []
    const need =
      2 +                      // heroTitle, heroSubtitle
      features.length * 2 +    // feature title+desc
      howSteps.length +        // steps
      1 +                      // demoHeading
      securityItems.length * 2 + // security title+desc
      testimonials.length +    // quotes only
      faq.length * 2           // faq q+a
    if (t.length < need) {
      return
    }
    let i = 0
    setHeroTitle(t[i++] || heroTitle)
    setHeroSubtitle(t[i++] || heroSubtitle)
    const feats: [string, string][] = []
    for (let k = 0; k < features.length; k++) {
      const ft = t[i++] || features[k][0]
      const fd = t[i++] || features[k][1]
      feats.push([ft, fd])
    }
    setFeatures(feats)
    const steps: string[] = []
    for (let k = 0; k < howSteps.length; k++) {
      steps.push(t[i++] || howSteps[k])
    }
    setHowSteps(steps)
    setDemoHeading(t[i++] || demoHeading)
    const sec: [string, string][] = []
    for (let k = 0; k < securityItems.length; k++) {
      const st = t[i++] || securityItems[k][0]
      const sd = t[i++] || securityItems[k][1]
      sec.push([st, sd])
    }
    setSecurityItems(sec)
    const testi: [string, string][] = []
    for (let k = 0; k < testimonials.length; k++) {
      const name = testimonials[k][0]
      const quote = t[i++] || testimonials[k][1]
      testi.push([name, quote])
    }
    setTestimonials(testi)
    const faqPairs: [string, string][] = []
    for (let k = 0; k < faq.length; k++) {
      const q = t[i++] || faq[k][0]
      const a = t[i++] || faq[k][1]
      faqPairs.push([q, a])
    }
    setFaq(faqPairs)
  }
  const handleLangChange = (l: 'en' | 'yo' | 'ig' | 'ha') => {
    setSelectedLang(l)
    setLang(l)
  }
  return (
    <main>
      <Header />

      {/* NYSC Corps Photo Banner */}
      <div
        className="relative h-52 md:h-64 overflow-hidden flex items-center"
        style={{
          backgroundImage: "url('/NYSC-ORIENTATION-CAMPS-IN-NIGERIA-1-1024x531.jpg')",
          backgroundSize: 'cover',
          backgroundPosition: 'center 30%',
        }}
      >
        <div className="absolute inset-0 bg-green-900/80 md:bg-green-900/65 transition-colors" />
        <div className="relative z-10 container flex flex-col md:flex-row items-center gap-4 md:gap-6 px-6">
          <div className="relative w-16 h-16 md:w-20 md:h-20 flex-shrink-0">
            <Image
              src="/NYSC-Nigeria-Logo.png"
              alt="NYSC Logo"
              fill
              className="rounded-full border-2 md:border-4 border-white/30 shadow-xl object-contain bg-white/10"
            />
          </div>
          <div className="text-center md:text-left text-white">
            <div className="text-lg md:text-3xl font-black md:font-extrabold tracking-tight md:tracking-wider leading-tight">NATIONAL YOUTH SERVICE CORPS</div>
            <div className="text-green-300 text-[10px] md:text-sm tracking-[0.2em] md:tracking-[0.3em] font-bold mt-1 uppercase">• Service and Humility •</div>
            <div className="text-green-100 text-[10px] md:text-xs mt-2 max-w-lg opacity-80 font-medium">AI-Powered Assistant for all NYSC-related queries</div>
          </div>
        </div>
      </div>

      {/* Hero */}
      <section className="relative">
        <div className="absolute inset-0 -z-10 opacity-40 blur-3xl bg-[radial-gradient(600px_circle_at_20%_20%,#2BB673_10%,transparent_60%),radial-gradient(700px_circle_at_80%_30%,#0B7A33_10%,transparent_60%)] dark:opacity-20" />
        <div className="container py-16 md:py-24 grid md:grid-cols-2 gap-10 items-center">
          <div>
            <div className="text-xs font-semibold tracking-widest text-green-700 dark:text-green-400 uppercase mb-2">
              {t('welcome_label')}
            </div>
            <motion.h1
              initial={false}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="text-5xl md:text-6xl font-bold tracking-tight"
            >
              {t('hero_title')}
            </motion.h1>
            <p className="mt-4 text-lg text-slate-700 dark:text-slate-300 max-w-xl">
              {t('hero_subtitle')}
            </p>
            <div className="mt-6 flex gap-3 items-center flex-wrap">
              <GetStartedButton />
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs">🌐</span>
                <select
                  className="pl-7 rounded-xl border border-default bg-secondary text-sm px-3 py-2 shadow-sm hover:shadow-md transition"
                  value={selectedLang}
                  onChange={(e) => handleLangChange(e.target.value as any)}
                  aria-label={t('language_label')}
                >
                  <option value="en">English</option>
                  <option value="yo">Yorùbá</option>
                  <option value="ig">Igbo</option>
                  <option value="ha">Hausa</option>
                </select>
              </div>
              <a href="#demo" className="inline-flex rounded-xl border border-slate-300/60 dark:border-slate-700/60 px-6 py-3">
                {t('cta_view_demo')}
              </a>
            </div>
            <div className="mt-6 flex gap-4 text-xs text-slate-600 dark:text-slate-400">
              <span className="rounded-full border border-green-300 bg-green-50 dark:bg-green-900/30 dark:border-green-700 px-3 py-1 text-green-700 dark:text-green-300">{t('chip_secure')}</span>
              <span className="rounded-full border border-green-300 bg-green-50 dark:bg-green-900/30 dark:border-green-700 px-3 py-1 text-green-700 dark:text-green-300">{t('chip_ai')}</span>
              <span className="rounded-full border border-green-300 bg-green-50 dark:bg-green-900/30 dark:border-green-700 px-3 py-1 text-green-700 dark:text-green-300">{t('chip_updated')}</span>
            </div>
          </div>
          <ChatMock />
        </div>
      </section>

      {/* Features */}
      <section id="features" className="container py-20">
        <div className="text-center mb-12">
          <div className="inline-block text-xs font-bold tracking-widest text-green-600 dark:text-green-400 uppercase mb-2 bg-green-50 dark:bg-green-900/30 px-4 py-1 rounded-full border border-green-200 dark:border-green-800">
            {t('features_title')}
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mt-2">{t('features_title')}</h2>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {([
            ['💬', t('feature_qa_t'), t('feature_qa_s')],
            ['📍', t('feature_ppa_t'), t('feature_ppa_s')],
            ['📄', t('feature_callup_t'), t('feature_callup_s')],
            ['💰', t('feature_allowance_t'), t('feature_allowance_s')],
            ['📋', t('feature_mobil_t'), t('feature_mobil_s')],
            ['🌍', t('feature_voice_t'), t('feature_voice_s')],
          ] as [string, string, string][]).map(([icon, title, desc]) => (
            <motion.div
              key={title}
              initial={false}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="group rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 hover:border-green-400 hover:shadow-lg transition-all duration-200"
            >
              <div className="text-3xl mb-4">{icon}</div>
              <div className="font-semibold text-slate-900 dark:text-white mb-1">{title}</div>
              <div className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{desc}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section id="how" className="py-20 bg-green-700">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white">{t('how_title')}</h2>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            {([
              ['❓', t('how_1')],
              ['🧠', t('how_2')],
              ['📚', t('how_3')],
              ['⚡', t('how_4')],
            ] as [string, string][]).map(([icon, step], i) => (
              <motion.div
                key={step}
                initial={false}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="bg-green-800/60 rounded-2xl p-6 text-center border border-green-600"
              >
                <div className="text-4xl mb-3">{icon}</div>
                <div className="text-3xl font-black text-green-300 mb-2">{i + 1}</div>
                <div className="text-sm text-green-100 font-medium">{step}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo */}
      <section id="demo" className="py-20">
        <div className="container">
          <div className="text-center mb-10">
            <h2 className="text-3xl md:text-4xl font-bold">{t('demo_title')}</h2>
            <p className="text-slate-500 dark:text-slate-400 mt-2 text-sm">
              {t('hero_subtitle')}
            </p>
          </div>
          <ChatMock />
        </div>
      </section>

      {/* Security */}
      <section id="security" className="py-20 bg-slate-50 dark:bg-slate-900/50">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">{t('security_title')}</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {([
              ['🔐', t('security_enc_t'), t('security_enc_s')],
              ['✅', t('security_src_t'), t('security_src_s')],
              ['🔄', t('security_upd_t'), t('security_upd_s')],
            ] as [string, string, string][]).map(([icon, title, desc]) => (
              <div key={title} className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-6 text-center shadow-sm">
                <div className="text-4xl mb-4">{icon}</div>
                <div className="font-semibold mb-2">{title}</div>
                <div className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">{t('testimonials_title')}</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {([
              ['🟢', t('testi_1_n'), t('testi_1_q')],
              ['🟡', t('testi_2_n'), t('testi_2_q')],
              ['🔵', t('testi_3_n'), t('testi_3_q')],
            ] as [string, string, string][]).map(([dot, name, quote]) => (
              <div key={name} className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-6 shadow-sm">
                <div className="text-2xl mb-3">"</div>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed italic">{quote}</p>
                <div className="flex items-center gap-2 mt-4">
                  <span className="text-lg">{dot}</span>
                  <span className="font-medium text-sm">{name}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-20 bg-green-50 dark:bg-green-950/20">
        <div className="container max-w-3xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">{t('faq_title')}</h2>
          </div>
          <div className="space-y-3">
            {([
              [t('faq_1_q'), t('faq_1_a')],
              [t('faq_2_q'), t('faq_2_a')],
              [t('faq_3_q'), t('faq_3_a')],
              [t('faq_4_q'), t('faq_4_a')],
              [t('faq_5_q'), t('faq_5_a')],
              [t('faq_6_q'), t('faq_6_a')],
            ] as [string, string][]).map(([q, a]) => (
              <details key={q} className="group rounded-xl border border-green-200 dark:border-green-800 bg-white dark:bg-slate-900 p-4 open:shadow-md transition-all">
                <summary className="font-medium cursor-pointer flex items-center justify-between list-none">
                  <span>{q}</span>
                  <span className="ml-2 text-green-600 group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <div className="text-sm text-slate-600 dark:text-slate-400 mt-3 leading-relaxed border-t border-green-100 dark:border-green-900 pt-3">{a}</div>
              </details>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </main>
  )
}

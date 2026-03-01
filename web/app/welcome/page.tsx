"use client"
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getUser, isAuthed, signOut } from '@/lib/auth'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'

export default function WelcomePage() {
  const router = useRouter()
  const { t } = useI18n()
  const [name, setName] = useState<string>('Member')

  useEffect(() => {
    if (!isAuthed()) router.replace('/login')
    const u = getUser()
    if (u?.name) setName(u.name.split(' ')[0])
  }, [router])

  const cards = [
    {
      icon: '💰',
      title: t('welcome_card_allowance') || 'Monthly Allowance',
      desc: 'Ask about your N77,000 monthly allowance, payment dates and eligibility.',
      href: '/app',
      color: 'border-green-200 hover:border-green-400',
    },
    {
      icon: '🔄',
      title: t('welcome_card_redeploy') || 'Redeployment',
      desc: 'Learn how to apply for redeployment, valid reasons and required documents.',
      href: '/app',
      color: 'border-blue-200 hover:border-blue-400',
    },
    {
      icon: '🏢',
      title: t('welcome_card_ppa') || 'PPA & Posting',
      desc: 'Find your Place of Primary Assignment and understand your posting rights.',
      href: '/app',
      color: 'border-yellow-200 hover:border-yellow-400',
    },
    {
      icon: '📋',
      title: t('welcome_card_mobil') || 'Mobilization',
      desc: 'Get information on call-up letters, camp dates and registration steps.',
      href: '/app',
      color: 'border-purple-200 hover:border-purple-400',
    },
    {
      icon: '📜',
      title: 'Decree & Bye-Laws',
      desc: 'Read the NYSC Act, Decree and official corps bye-laws and regulations.',
      href: '/app',
      color: 'border-red-200 hover:border-red-400',
    },
    {
      icon: '🤝',
      title: 'CDS & SAED',
      desc: 'Explore Community Development Service groups and skill acquisition options.',
      href: '/app',
      color: 'border-teal-200 hover:border-teal-400',
    },
  ]

  return (
    <main className="min-h-[100dvh] bg-gray-50">
      {/* Header */}
      <header className="bg-green-700 shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" width={44} height={44} className="rounded-full" />
            <div className="text-white">
              <div className="text-sm font-bold tracking-wider">NATIONAL YOUTH SERVICE CORPS</div>
              <div className="text-[10px] text-green-200 tracking-[0.2em]">• SERVICE AND HUMILITY •</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 bg-green-800 rounded-full px-3 py-1.5">
              <div className="h-7 w-7 rounded-full bg-green-500 flex items-center justify-center text-white font-bold text-xs">
                {name[0]?.toUpperCase()}
              </div>
              <span className="text-white text-sm">{name}</span>
            </div>
            <button
              onClick={() => { signOut(); router.replace('/login') }}
              className="text-green-200 hover:text-white text-xs border border-green-500 rounded px-3 py-1.5 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div
        className="relative h-48 md:h-64 flex items-center overflow-hidden"
        style={{
          backgroundImage: "url('/NYSC-ORIENTATION-CAMPS-IN-NIGERIA-1-1024x531.jpg')",
          backgroundSize: 'cover',
          backgroundPosition: 'center 30%',
        }}
      >
        <div className="absolute inset-0 bg-green-900/70" />
        <div className="relative z-10 max-w-7xl mx-auto px-6 w-full">
          <p className="text-green-300 text-sm font-medium tracking-widest mb-1">NYSC AI ASSISTANT</p>
          <h1 className="text-3xl md:text-4xl font-extrabold text-white leading-tight">
            Welcome back, {name}!
          </h1>
          <p className="text-green-100 mt-2 text-sm max-w-lg">
            Your intelligent guide for all NYSC-related questions — allowances, redeployment, registration and more.
          </p>
          <a
            href="/app"
            className="mt-4 inline-flex items-center gap-2 bg-white text-green-700 font-semibold text-sm px-5 py-2.5 rounded-full shadow hover:bg-green-50 transition-colors"
          >
            💬 Open Chat Assistant
          </a>
        </div>
      </div>

      {/* Cards */}
      <section className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-gray-800 font-bold text-lg">Quick Topics</h2>
          <a href="/app" className="text-green-700 text-sm font-medium hover:underline">Ask anything →</a>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((c) => (
            <a
              key={c.title}
              href={c.href}
              className={`bg-white rounded-2xl border-2 p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 ${c.color}`}
            >
              <div className="text-3xl mb-3">{c.icon}</div>
              <div className="font-semibold text-gray-800 text-sm mb-1">{c.title}</div>
              <div className="text-xs text-gray-500 leading-relaxed">{c.desc}</div>
              <div className="mt-3 text-green-600 text-xs font-medium">Tap to ask →</div>
            </a>
          ))}
        </div>
      </section>

      {/* Info Bar */}
      <div className="bg-green-50 border-t border-green-100 py-4 px-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-sm text-green-800 font-medium">
            📢 Current Allowance: <span className="font-bold">₦77,000/month</span> (as of March 2025)
          </div>
          <div className="flex gap-4 text-xs text-green-700">
            <a href="https://www.nysc.gov.ng" target="_blank" rel="noopener noreferrer" className="hover:underline">nysc.gov.ng</a>
            <a href="https://portal.nysc.org.ng" target="_blank" rel="noopener noreferrer" className="hover:underline">NYSC Portal</a>
            <a href="/preferences" className="hover:underline">⚙ Preferences</a>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-green-800 text-white py-6 px-4 mt-2">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" width={32} height={32} className="rounded-full opacity-80" />
            <div className="text-sm">
              <div className="font-semibold">NYSC AI Assistant</div>
              <div className="text-green-300 text-xs">Powered by official NYSC documentation</div>
            </div>
          </div>
          <div className="text-xs text-green-300 text-center">
            © 2026 National Youth Service Corps. All rights reserved.
          </div>
        </div>
      </footer>
    </main>
  )
}

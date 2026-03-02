"use client"
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowLeft, MessageSquare, BookOpen, ShieldCheck, Zap } from 'lucide-react'

const steps = [
    {
        num: '01',
        icon: MessageSquare,
        title: 'Ask Naturally',
        desc: 'No complex commands needed. Type your question in English, Yorùbá, Hausa, or Igbo — just like talking to a friend.',
        color: 'from-[var(--accent-start)] to-[var(--accent-end)]',
        iconBg: 'bg-green-50 dark:bg-green-900/20',
        iconColor: 'text-[var(--accent-start)]',
    },
    {
        num: '02',
        icon: BookOpen,
        title: 'Grounded in Facts',
        desc: 'Our AI retrieves answers directly from the latest official NYSC decrees, bye-laws, and portal updates.',
        color: 'from-blue-600 to-blue-400',
        iconBg: 'bg-blue-50 dark:bg-blue-900/20',
        iconColor: 'text-blue-600',
    },
    {
        num: '03',
        icon: ShieldCheck,
        title: 'Secure & Private',
        desc: 'Your conversations are handled according to modern data privacy standards. Nothing is sold or shared.',
        color: 'from-purple-600 to-purple-400',
        iconBg: 'bg-purple-50 dark:bg-purple-900/20',
        iconColor: 'text-purple-600',
    },
    {
        num: '04',
        icon: Zap,
        title: 'Instant Responses',
        desc: 'Get answers 24/7 without waiting for office hours. Perfect for quick checks in camp or on the go.',
        color: 'from-amber-500 to-yellow-400',
        iconBg: 'bg-amber-50 dark:bg-amber-900/20',
        iconColor: 'text-amber-600',
    },
]

export default function HowItWorksPage() {
    const router = useRouter()

    return (
        <motion.main
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="min-h-screen"
            style={{ background: 'var(--bg-primary)' }}
        >
            {/* Header */}
            <div className="max-w-5xl mx-auto px-6 pt-10 pb-4">
                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-secondary hover:text-primary text-xs font-semibold uppercase tracking-widest transition-colors mb-10"
                >
                    <ArrowLeft className="w-4 h-4" /> Back
                </button>

                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1, duration: 0.45 }}
                    className="text-center mb-20"
                >
                    <div className="text-xs font-black text-secondary uppercase tracking-[0.3em] mb-3">Process</div>
                    <h1 className="font-display text-5xl md:text-6xl text-primary mb-4">How NYSC AI Works</h1>
                    <p className="text-secondary max-w-xl mx-auto">Your intelligent companion for a smooth service year — powered by official sources, answered in your language.</p>
                </motion.div>
            </div>

            {/* Timeline */}
            <section className="max-w-5xl mx-auto px-6 pb-20">
                {steps.map((step, i) => {
                    const Icon = step.icon
                    const isLeft = i % 2 === 0
                    return (
                        <motion.div
                            key={step.num}
                            initial={{ opacity: 0, x: isLeft ? -24 : 24 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true, margin: '-60px' }}
                            transition={{ duration: 0.5, ease: 'easeOut' }}
                            className={`flex flex-col md:flex-row items-center gap-8 mb-16 ${!isLeft && 'md:flex-row-reverse'}`}
                        >
                            {/* Card */}
                            <div className="flex-1 rounded-2xl border border-[var(--border-default)] bg-[var(--bg-secondary)] p-8 hover:border-[var(--accent-end)] hover:-translate-y-1 hover:shadow-xl hover:shadow-green-900/10 transition-all duration-300">
                                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${step.iconBg} mb-5`}>
                                    <Icon className={`w-6 h-6 ${step.iconColor}`} />
                                </div>
                                <h3 className="font-semibold text-primary text-lg mb-3">{step.title}</h3>
                                <p className="text-secondary text-sm leading-relaxed">{step.desc}</p>
                            </div>

                            {/* Step number (center on desktop, hidden on mobile overlap) */}
                            <div className={`flex-shrink-0 w-20 h-20 rounded-full bg-gradient-to-br ${step.color} flex items-center justify-center shadow-xl text-white font-black text-2xl ring-4 ring-[var(--bg-primary)]`}>
                                {step.num}
                            </div>

                            {/* Spacer */}
                            <div className="hidden md:block flex-1" />
                        </motion.div>
                    )
                })}
            </section>

            {/* CTA */}
            <section className="max-w-5xl mx-auto px-6 pb-20">
                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5 }}
                    className="relative rounded-3xl overflow-hidden text-center py-16 px-8"
                    style={{ background: 'linear-gradient(135deg, var(--accent-start), var(--accent-end))' }}
                >
                    <div className="absolute inset-0 hero-grid-overlay opacity-30" />
                    <div className="relative z-10">
                        <h2 className="font-display text-4xl md:text-5xl text-white mb-4">Ready to start?</h2>
                        <p className="text-green-100/80 mb-8 max-w-md mx-auto">Ask anything about your NYSC service year — instantly, in your language.</p>
                        <a href="/app" className="inline-flex items-center gap-2 bg-white text-[var(--accent-start)] font-bold px-8 py-4 rounded-xl hover:bg-green-50 hover:scale-105 active:scale-[0.98] transition-all shadow-lg">
                            Launch Assistant <Zap className="w-4 h-4" />
                        </a>
                    </div>
                </motion.div>
            </section>
        </motion.main>
    )
}

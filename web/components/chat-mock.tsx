"use client"
import { motion } from 'framer-motion'
import { useI18n } from '@/components/i18n'

export function ChatMock() {
  const { t } = useI18n()
  return (
    <div className="card p-4">
      <div className="text-xs text-secondary border-b border-default pb-2">
        {t('demo_title')}
      </div>
      <div className="py-3 space-y-3">
        <div className="max-w-[80%] rounded-2xl bg-sidebar border border-default text-primary px-3 py-2 text-sm">
          {t('faq_4_q')}
        </div>
        <motion.div
          initial={false}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-[85%] rounded-2xl accent text-white shadow px-3 py-2 text-sm ml-auto"
        >
          {t('faq_4_a')}
          <div className="mt-2 text-[10px] opacity-80">Today • 10:24</div>
        </motion.div>
        <div className="flex gap-2 pt-2">
          {[t('suggest_allowance'), t('suggest_redeploy'), t('suggest_ppa')].map((s) => (
            <button
              key={s}
              className="rounded-full border border-default bg-primary text-xs px-3 py-1"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

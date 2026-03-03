"use client"
import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useI18n } from '@/components/i18n'
import { Info } from 'lucide-react'

type Props = {
  open: boolean
  onClose: () => void
  onContinue: () => void
  onLogin: () => void
  onSignup: () => void
}

export function WarningModal({ open, onClose, onContinue, onLogin, onSignup }: Props) {
  const { t } = useI18n()
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", duration: 0.5 }}
            className="relative w-full max-w-md bg-[#0A1A0C]/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
          >
            {/* Top accent line */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)]" />

            <div className="p-6 sm:p-8">
              <div className="w-12 h-12 rounded-full bg-green-900/30 border border-green-500/20 flex items-center justify-center mb-5">
                <Info className="w-6 h-6 text-green-400" />
              </div>

              <h3 className="font-display text-2xl text-white mb-2">{t('modal_title')}</h3>
              <p className="text-sm leading-relaxed text-white/60 mb-8">{t('modal_body')}</p>

              <div className="flex flex-col gap-3">
                <button
                  onClick={onSignup}
                  className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)] hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-green-900/20 text-sm"
                >
                  {t('auth_signup_link')}
                </button>
                <div className="flex gap-3">
                  <button
                    onClick={onLogin}
                    className="flex-1 py-3 rounded-xl border border-white/10 text-white hover:bg-white/5 transition-colors text-sm font-medium"
                  >
                    {t('login')}
                  </button>
                  <button
                    onClick={onContinue}
                    className="flex-1 py-3 rounded-xl text-white/50 hover:text-white transition-colors text-xs font-medium"
                  >
                    {t('modal_continue')}
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}

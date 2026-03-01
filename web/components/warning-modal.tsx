"use client"
import { useEffect } from 'react'
import { useI18n } from '@/components/i18n'

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

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative z-10 w-[90%] max-w-md rounded-2xl bg-secondary border border-default shadow-xl p-6">
        <div className="text-lg font-semibold">{t('modal_title')}</div>
        <p className="mt-2 text-sm text-secondary">{t('modal_body')}</p>
        <div className="mt-5 flex flex-col sm:flex-row gap-2">
          <button
            onClick={onContinue}
            className="inline-flex justify-center rounded-xl accent px-4 py-2 shadow hover:opacity-90"
          >
            {t('modal_continue')}
          </button>
          <button
            onClick={onLogin}
            className="inline-flex justify-center rounded-xl border border-default px-4 py-2"
          >
            {t('login')}
          </button>
          <button
            onClick={onSignup}
            className="inline-flex justify-center rounded-xl border border-default px-4 py-2"
          >
            {t('cta_get_started')}
          </button>
        </div>
      </div>
    </div>
  )
}

"use client"
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { isAuthed } from '@/lib/auth'
import { WarningModal } from '@/components/warning-modal'
import { useI18n } from '@/components/i18n'

type Props = {
  className?: string
  label?: string
}

export function GetStartedButton({ className = '', label }: Props) {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [authed, setAuthed] = useState(false)
  useEffect(() => setAuthed(isAuthed()), [])
  const { t } = useI18n()

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault()
    if (authed) {
      router.push('/app')
    } else {
      setOpen(true)
    }
  }

  return (
    <>
      <a
        href="/app"
        onClick={handleClick}
        className={
          'inline-flex rounded-xl accent px-6 py-3 shadow hover:opacity-90 ' +
          className
        }
      >
        {label ?? t('get_started') ?? 'Enter'}
      </a>
      <WarningModal
        open={open}
        onClose={() => setOpen(false)}
        onContinue={() => {
          setOpen(false)
          router.push('/app')
        }}
        onLogin={() => {
          setOpen(false)
          router.push('/login')
        }}
        onSignup={() => {
          setOpen(false)
          router.push('/signup')
        }}
      />
    </>
  )
}

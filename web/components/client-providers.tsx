"use client"
import { LanguageProvider } from '@/components/i18n'
import { ThemeProvider } from '@/components/theme-provider'

export function ClientProviders({ children }: { children: React.ReactNode }) {
  return (
    <LanguageProvider>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        {children}
      </ThemeProvider>
    </LanguageProvider>
  )
}

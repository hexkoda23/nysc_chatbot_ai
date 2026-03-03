"use client"
import { useI18n } from '@/components/i18n'
import Image from 'next/image'

export function Footer() {
  const { t } = useI18n()
  return (
    <footer className="mt-0 border-t border-green-200 dark:border-green-900">
      {/* Upper footer */}
      <div className="bg-green-800 text-white">
        <div className="container py-12 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="lg:col-span-1">
            <div className="flex items-center gap-3 mb-4">
              <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" width={44} height={44} className="rounded-full" />
              <div>
                <div className="font-bold text-sm tracking-widest">{t('brand')}</div>
                <div className="text-green-300 text-[10px] tracking-widest uppercase">{t('brand_motto')}</div>
              </div>
            </div>
            <p className="text-green-200 text-xs leading-relaxed">{t('hero_subtitle')}</p>
            <div className="mt-4 text-xs text-green-300">
              <div>support@nysc.ai</div>
              <div className="mt-1">
                <a href="https://www.nysc.gov.ng" target="_blank" rel="noopener noreferrer" className="hover:text-white underline">nysc.gov.ng</a>
              </div>
            </div>
          </div>

          {/* Product */}
          <div>
            <div className="font-bold mb-4 text-sm tracking-wider text-green-200 uppercase">{t('footer_product')}</div>
            <ul className="space-y-2 text-sm text-green-300">
              <li><a href="#features" className="hover:text-white transition-colors">{t('footer_features')}</a></li>
              <li><a href="#demo" className="hover:text-white transition-colors">{t('footer_demo')}</a></li>
              <li><a href="#how" className="hover:text-white transition-colors">{t('nav_how')}</a></li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <div className="font-bold mb-4 text-sm tracking-wider text-green-200 uppercase">{t('footer_resources')}</div>
            <ul className="space-y-2 text-sm text-green-300">
              <li><a href="#faq" className="hover:text-white transition-colors">{t('footer_faq')}</a></li>
              <li><a href="#security" className="hover:text-white transition-colors">{t('footer_security')}</a></li>
              <li>
                <a href="https://portal.nysc.org.ng" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                  {t('footer_portal')}
                </a>
              </li>
            </ul>
          </div>

          {/* Legal & Contact */}
          <div>
            <div className="font-bold mb-4 text-sm tracking-wider text-green-200 uppercase">{t('footer_legal_contact')}</div>
            <ul className="space-y-2 text-sm text-green-300">
              <li><a href="/legal#terms" className="hover:text-white transition-colors">{t('footer_terms')}</a></li>
              <li><a href="/legal#privacy" className="hover:text-white transition-colors">{t('footer_privacy')}</a></li>
              <li><a href="/contact" className="hover:text-white transition-colors">{t('footer_contact')}</a></li>
            </ul>
          </div>
        </div>
      </div>

      {/* Lower footer */}
      <div className="bg-green-900 border-t border-green-700">
        <div className="container py-4 text-xs text-green-400 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>{t('footer_copyright_full')}</p>
          <div className="flex gap-4">
            <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">{t('social_twitter')}</a>
            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">{t('social_linkedin')}</a>
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">{t('social_github')}</a>
          </div>
        </div>
      </div>
    </footer>
  )
}

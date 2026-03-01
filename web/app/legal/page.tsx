"use client"

export default function LegalPage() {
  return (
    <main className="min-h-[100dvh] bg-primary text-primary">
      <div className="container py-12 max-w-3xl">
        <h1 className="text-3xl font-semibold mb-6">Legal</h1>

        <section id="terms" className="rounded-2xl border border-default bg-secondary p-6 mb-6">
          <h2 className="text-xl font-semibold mb-2">Terms of Use</h2>
          <p className="text-sm text-secondary">
            NYSC AI provides informational assistance based on official NYSC materials and public updates. It does not replace
            directives from NYSC, Corps Producing Institutions, or government authorities. Users remain responsible for verifying
            critical decisions with official channels. By using this service, you agree not to misuse the platform, automate abuse,
            or rely on outputs where legal or institutional approval is required.
          </p>
        </section>

        <section id="privacy" className="rounded-2xl border border-default bg-secondary p-6 mb-6">
          <h2 className="text-xl font-semibold mb-2">Privacy Policy</h2>
          <p className="text-sm text-secondary">
            We collect minimal data necessary to operate features such as chat history (stored locally when enabled) and session
            analytics for quality improvement. We do not sell personal data. You can disable local history in Preferences at any time.
            For official NYSC records or corrections, use the NYSC Portal.
          </p>
        </section>

        <section className="rounded-2xl border border-default bg-secondary p-6">
          <h2 className="text-xl font-semibold mb-2">Official Sources</h2>
          <ul className="text-sm text-secondary list-disc pl-5 space-y-1">
            <li>NYSC Website – https://www.nysc.gov.ng</li>
            <li>NYSC Portal – https://portal.nysc.org.ng</li>
          </ul>
        </section>
      </div>
    </main>
  )
}

"use client"
import { useRouter } from 'next/navigation'
import { ArrowLeft, HelpCircle } from 'lucide-react'

export default function SupportPage() {
    const router = useRouter()
    return (
        <main className="min-h-screen bg-gray-50 p-6 md:p-12">
            <div className="max-w-3xl mx-auto bg-white rounded-[32px] shadow-sm border border-gray-100 p-8 md:p-12">
                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-green-700 font-black uppercase tracking-widest text-xs mb-8 hover:text-green-500 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </button>
                <div className="flex items-center gap-4 mb-6">
                    <HelpCircle className="w-10 h-10 text-blue-500" />
                    <h1 className="text-3xl md:text-5xl font-black text-gray-900 tracking-tighter">Support & Help</h1>
                </div>
                <div className="space-y-8">
                    <p className="text-gray-600 font-medium leading-relaxed">
                        Need assistance with the NYSC AI chatbot or have specific service questions? We're here to help.
                    </p>

                    <div className="grid gap-6">
                        <div className="p-6 bg-blue-50 rounded-2xl border border-blue-100">
                            <h3 className="text-blue-900 font-black uppercase text-xs tracking-widest mb-2">Email Support</h3>
                            <p className="text-sm font-bold text-blue-800">support@nysc-ai.ng</p>
                        </div>
                        <div className="p-6 bg-gray-50 rounded-2xl border border-gray-100">
                            <h3 className="text-gray-900 font-black uppercase text-xs tracking-widest mb-2">Office Hours</h3>
                            <p className="text-sm font-bold text-gray-700">Monday - Friday: 8:00 AM - 4:00 PM</p>
                        </div>
                    </div>

                    <section>
                        <h2 className="text-xl font-black text-gray-800 uppercase tracking-tight mb-4">Common Issues</h2>
                        <div className="space-y-4">
                            <details className="group border-b border-gray-100 pb-4">
                                <summary className="list-none font-bold text-gray-800 cursor-pointer flex justify-between items-center">
                                    Login issues
                                    <span className="group-open:rotate-180 transition-transform">↓</span>
                                </summary>
                                <p className="mt-2 text-sm text-gray-500 font-medium">Clear your browser cache and ensure you're using the correct enrollment email.</p>
                            </details>
                            <details className="group border-b border-gray-100 pb-4">
                                <summary className="list-none font-bold text-gray-800 cursor-pointer flex justify-between items-center">
                                    Incorrect information
                                    <span className="group-open:rotate-180 transition-transform">↓</span>
                                </summary>
                                <p className="mt-2 text-sm text-gray-500 font-medium">The AI is grounded in official docs, but if you find a discrepancy, please report it via the Support email.</p>
                            </details>
                        </div>
                    </section>
                </div>
            </div>
        </main>
    )
}

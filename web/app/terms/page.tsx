"use client"
import { useRouter } from 'next/navigation'
import { ArrowLeft, Scale } from 'lucide-react'

export default function TermsPage() {
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
                    <Scale className="w-10 h-10 text-gray-700" />
                    <h1 className="text-3xl md:text-5xl font-black text-gray-900 tracking-tighter">Terms of Service</h1>
                </div>
                <div className="prose prose-gray max-w-none text-gray-600 font-medium leading-relaxed space-y-4 text-sm">
                    <p>By using the NYSC AI Assistant, you agree to the following terms.</p>

                    <h2 className="text-lg font-black text-gray-800 uppercase tracking-tight mt-6 mb-2">1. Use of Service</h2>
                    <p>This AI assistant is provided for informational purposes only. While we strive for absolute accuracy, always verify critical deployment details with your LGI or ZI.</p>

                    <h2 className="text-lg font-black text-gray-800 uppercase tracking-tight mt-6 mb-2">2. User Conduct</h2>
                    <p>Users agree not to use the service for any illegal activities or to attempt to bypass security measures.</p>

                    <h2 className="text-lg font-black text-gray-800 uppercase tracking-tight mt-6 mb-2">3. Limitation of Liability</h2>
                    <p>NYSC AI is not responsible for any decisions made based on AI-generated responses. Final authority remains with official NYSC management.</p>
                </div>
            </div>
        </main>
    )
}

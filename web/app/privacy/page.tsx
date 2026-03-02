"use client"
import { useRouter } from 'next/navigation'
import { ArrowLeft, Lock } from 'lucide-react'

export default function PrivacyPage() {
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
                    <Lock className="w-10 h-10 text-green-500" />
                    <h1 className="text-3xl md:text-5xl font-black text-gray-900 tracking-tighter">Privacy Policy</h1>
                </div>
                <div className="prose prose-green max-w-none text-gray-600 font-medium leading-relaxed space-y-4 text-sm">
                    <p>Last Updated: March 2, 2026</p>
                    <p>Your privacy is paramount. This policy outlines how we handle your data when using the NYSC AI Assistant.</p>

                    <h2 className="text-lg font-black text-gray-800 uppercase tracking-tight mt-6 mb-2">1. Data Collection</h2>
                    <p>We collect only the information necessary to provide accurate AI responses, including your name (for personalization) and your chat queries.</p>

                    <h2 className="text-lg font-black text-gray-800 uppercase tracking-tight mt-6 mb-2">2. Data Usage</h2>
                    <p>Your chat history is used solely to provide context for your current session and to improve our AI's accuracy over time. We do not sell your personal data.</p>

                    <h2 className="text-lg font-black text-gray-800 uppercase tracking-tight mt-6 mb-2">3. Security</h2>
                    <p>All data is transmitted via secure, encrypted channels. We implement industry-standard security measures to protect your information.</p>
                </div>
            </div>
        </main>
    )
}

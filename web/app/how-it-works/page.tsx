"use client"
import { useRouter } from 'next/navigation'
import { ArrowLeft, BookOpen, MessageSquare, ShieldCheck, Zap } from 'lucide-react'

export default function HowItWorksPage() {
    const router = useRouter()
    return (
        <main className="min-h-screen bg-gray-50 p-6 md:p-12">
            <div className="max-w-4xl mx-auto">
                <button
                    onClick={() => router.back()}
                    className="flex items-center gap-2 text-green-700 font-black uppercase tracking-widest text-xs mb-8 hover:text-green-500 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </button>

                <div className="text-center mb-16">
                    <h1 className="text-4xl md:text-6xl font-black text-gray-900 tracking-tight mb-4">How NYSC AI Works</h1>
                    <p className="text-gray-500 font-bold text-lg max-w-2xl mx-auto">Your intelligent companion for a smooth service year.</p>
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                    <div className="bg-white p-8 rounded-[32px] shadow-sm border border-gray-100">
                        <div className="w-12 h-12 bg-green-100 rounded-2xl flex items-center justify-center mb-6">
                            <MessageSquare className="w-6 h-6 text-green-600" />
                        </div>
                        <h3 className="text-xl font-black text-gray-900 uppercase tracking-tight mb-3">1. Ask Naturally</h3>
                        <p className="text-gray-600 font-medium text-sm leading-relaxed">
                            No need for complex commands. Type your questions in English, Yoruba, Hausa, or Igbo just like you would talk to a friend.
                        </p>
                    </div>

                    <div className="bg-white p-8 rounded-[32px] shadow-sm border border-gray-100">
                        <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center mb-6">
                            <BookOpen className="w-6 h-6 text-blue-600" />
                        </div>
                        <h3 className="text-xl font-black text-gray-900 uppercase tracking-tight mb-3">2. Grounded in Facts</h3>
                        <p className="text-gray-600 font-medium text-sm leading-relaxed">
                            Our AI retrieves information directly from the latest official NYSC decrees, bye-laws, and portal updates.
                        </p>
                    </div>

                    <div className="bg-white p-8 rounded-[32px] shadow-sm border border-gray-100">
                        <div className="w-12 h-12 bg-purple-100 rounded-2xl flex items-center justify-center mb-6">
                            <ShieldCheck className="w-6 h-6 text-purple-600" />
                        </div>
                        <h3 className="text-xl font-black text-gray-900 uppercase tracking-tight mb-3">3. Secure & Private</h3>
                        <p className="text-gray-600 font-medium text-sm leading-relaxed">
                            Your conversations are encrypted and your personal details are handled according to federal data privacy standards.
                        </p>
                    </div>

                    <div className="bg-white p-8 rounded-[32px] shadow-sm border border-gray-100">
                        <div className="w-12 h-12 bg-yellow-100 rounded-2xl flex items-center justify-center mb-6">
                            <Zap className="w-6 h-6 text-yellow-600" />
                        </div>
                        <h3 className="text-xl font-black text-gray-900 uppercase tracking-tight mb-3">4. Instant Responses</h3>
                        <p className="text-gray-600 font-medium text-sm leading-relaxed">
                            Get answers 24/7 without waiting for office hours. Perfect for quick checks while on the go or in camp.
                        </p>
                    </div>
                </div>

                <div className="mt-16 bg-green-900 rounded-[40px] p-10 md:p-16 text-center text-white">
                    <h2 className="text-3xl md:text-5xl font-black tracking-tight mb-6">Ready to start?</h2>
                    <a
                        href="/app"
                        className="inline-block bg-white text-green-900 font-black uppercase tracking-widest px-10 py-5 rounded-2xl hover:bg-green-50 transition-all hover:scale-105"
                    >
                        Launch Assistant
                    </a>
                </div>
            </div>
        </main>
    )
}

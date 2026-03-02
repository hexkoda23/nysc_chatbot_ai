"use client"
import { useRouter } from 'next/navigation'
import { ArrowLeft, Shield } from 'lucide-react'

export default function SafetyPage() {
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
                    <Shield className="w-10 h-10 text-red-500" />
                    <h1 className="text-3xl md:text-5xl font-black text-gray-900 tracking-tighter">Camp Safety</h1>
                </div>
                <div className="prose prose-red max-w-none text-gray-600 font-medium leading-relaxed space-y-4">
                    <p>Essential safety guidelines for Orientation Camp and during the service year.</p>
                    <section className="mt-8 space-y-6">
                        <div className="p-6 bg-red-50 rounded-2xl border border-red-100">
                            <h3 className="text-red-900 font-black uppercase text-xs tracking-widest mb-2">Emergency Contacts</h3>
                            <p className="text-sm font-bold text-red-800">NYSC Distress Call Center: 0800-NYSC-HELP</p>
                        </div>
                        <div>
                            <h2 className="text-xl font-black text-gray-800 uppercase tracking-tight mb-4">Key Safety Rules</h2>
                            <ul className="list-disc pl-5 gap-2 flex flex-col">
                                <li>Always carry your ID card.</li>
                                <li>Avoid night travels.</li>
                                <li>Report suspicious activities to the Camp Security Officer (CSO).</li>
                                <li>Follow all health and hygiene protocols in camp.</li>
                            </ul>
                        </div>
                    </section>
                </div>
            </div>
        </main>
    )
}

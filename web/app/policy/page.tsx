"use client"
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'

export default function PolicyPage() {
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
                <h1 className="text-3xl md:text-5xl font-black text-gray-900 tracking-tighter mb-6">Policy Documents</h1>
                <div className="prose prose-green max-w-none text-gray-600 font-medium leading-relaxed space-y-4">
                    <p>Official NYSC policy documents and guidelines for corps members.</p>
                    <div className="p-6 bg-green-50 rounded-2xl border border-green-100 text-green-800 italic">
                        This page is currently being updated with the latest 2024/2025 service year policies.
                    </div>
                    <section className="mt-8">
                        <h2 className="text-xl font-black text-gray-800 uppercase tracking-tight mb-4">Core Policies</h2>
                        <ul className="list-disc pl-5 gap-2 flex flex-col">
                            <li>Mobilization and Call-up Requirements</li>
                            <li>Orientation Camp Regulations</li>
                            <li>Primary Assignment Guidelines</li>
                            <li>Monthly Clearance and Allowance Procedures</li>
                        </ul>
                    </section>
                </div>
            </div>
        </main>
    )
}

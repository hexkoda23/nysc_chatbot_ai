"use client"
import { useState } from "react"

export default function ContactPage() {
  const [sent, setSent] = useState(false)
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [message, setMessage] = useState("")

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setSent(true)
  }

  return (
    <main className="min-h-[100dvh] bg-primary text-primary">
      <div className="container py-12 max-w-3xl">
        <h1 className="text-3xl font-semibold mb-6">Contact</h1>
        <div className="rounded-2xl border border-default bg-secondary p-6">
          {!sent ? (
            <form onSubmit={submit} className="space-y-4">
              <div className="grid gap-2">
                <label className="text-sm">Name</label>
                <input
                  className="rounded-lg border border-default bg-primary px-3 py-2 text-sm"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  required
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm">Email</label>
                <input
                  type="email"
                  className="rounded-lg border border-default bg-primary px-3 py-2 text-sm"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm">Message</label>
                <textarea
                  className="rounded-lg border border-default bg-primary px-3 py-2 text-sm min-h-[120px]"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="How can we help?"
                  required
                />
              </div>
              <div className="flex gap-2">
                <button type="submit" className="rounded-lg accent px-4 py-2 text-sm">Send</button>
                <a href="/" className="rounded-lg border border-default bg-primary px-4 py-2 text-sm">Cancel</a>
              </div>
              <div className="text-xs text-secondary">
                Or email me directly at <a href="mailto:[EMAIL_ADDRESS]">[kehindeadeleke92@gmail.com]</a>
              </div>
            </form>
          ) : (
            <div className="text-sm">
              Thanks, {name.split(" ")[0] || "there"} — your message has been recorded. I’ll get back to you at {email}.
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

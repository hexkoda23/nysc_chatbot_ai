"use client"
import { useEffect, useRef, useState } from 'react'
import { getUser, isAuthed, signOut } from '../../lib/auth'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft, Mic, Send, Plus, LogOut, Settings, Search,
  Globe, ChevronDown, X, Menu
} from 'lucide-react'
import { useI18n } from '@/components/i18n'
import Image from 'next/image'
import { sendMessage, reloadCorpus, translateTexts, BASE_URL } from '../../lib/api'
import { generateSessionId } from '../../lib/utils'

type Source = { source: string; snippet: string }
type Msg = { id: string; role: 'user' | 'assistant'; content: string; sources?: Source[]; langName?: string; langCode?: string }
type Chat = { id: string; title: string; msgs: Msg[]; langCode?: string }

const STORAGE_KEY = 'nysc_chats'
const isGreeting = (t: string) => {
  const s = t.trim().toLowerCase()
  return ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'].some(g => s === g || s.startsWith(g + ' '))
}

const SUGGESTIONS = [
  { label: 'Allowance details', sub: 'N77,000/month since March 2025' },
  { label: 'Redeployment steps', sub: 'Valid reasons and process' },
  { label: 'Call-up letter help', sub: 'How to print and timelines' },
  { label: 'PPA posting info', sub: 'Understanding your posting rights' },
]

const LANGUAGES = [
  { code: 'auto', label: 'Auto' },
  { code: 'en', label: 'English' },
  { code: 'yo', label: 'Yorùbá' },
  { code: 'ig', label: 'Igbo' },
  { code: 'ha', label: 'Hausa' },
]

export default function ChatApp() {
  const router = useRouter()
  const [chats, setChats] = useState<Chat[]>([])
  const [currentId, setCurrentId] = useState<string>('')
  const [input, setInput] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [showAnonNotice, setShowAnonNotice] = useState(false)
  const [authed, setAuthed] = useState(false)
  const [userName, setUserName] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showLangDropdown, setShowLangDropdown] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { t, lang: uiLang, setLang } = useI18n()
  const [selectedLang, setSelectedLang] = useState<'auto' | 'en' | 'yo' | 'ig' | 'ha'>('auto')
  const sessionIdRef = useRef<string>(undefined)
  if (!sessionIdRef.current) sessionIdRef.current = generateSessionId()
  const ANON_LIMIT = 5
  const [anonQuestionCount, setAnonQuestionCount] = useState(0)
  const [showLoginGate, setShowLoginGate] = useState(false)

  const renderContent = (text: string) => {
    const parts = text.split(/(https?:\/\/[^\s]+)/g)
    return parts.map((p, i) => {
      const clean = p.replace(/^`+|`+$/g, '')
      if (/^https?:\/\/[^\s]+$/.test(clean))
        return <a key={i} href={clean} target="_blank" rel="noopener noreferrer" className="underline text-[var(--accent-end)] break-all">{clean}</a>
      return <span key={i}>{p}</span>
    })
  }

  const filteredChats = query ? chats.filter(c => c.title.toLowerCase().includes(query.toLowerCase())) : chats
  const current = chats.find(c => c.id === currentId)
  const messages = current?.msgs ?? []

  const persist = (next: Chat[]) => {
    setChats(next)
    if (!authed) return
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { }
  }
  const updateMsgContent = (cid: string, mid: string, content: string, sources?: Source[]) => {
    setChats(prev => {
      const next = prev.map(c => {
        if (c.id !== cid) return c
        return { ...c, msgs: c.msgs.map(m => m.id === mid ? { ...m, content, sources: sources ?? m.sources } : m) }
      })
      if (authed) { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { } }
      return next
    })
  }
  const typeOut = (text: string, cid: string, mid: string, sources?: Source[]) => {
    setLoading(true)
    const total = text.length
    let i = 0
    const step = total > 2000 ? 4 : total > 1000 ? 3 : 2
    const tick = () => {
      i = Math.min(total, i + step)
      updateMsgContent(cid, mid, text.slice(0, i))
      if (i < total) setTimeout(tick, 16)
      else { updateMsgContent(cid, mid, text, sources); setLoading(false) }
    }
    tick()
  }

  const newChat = () => {
    const id = generateSessionId()
    const chat: Chat = { id, title: 'New chat', msgs: [], langCode: uiLang }
    persist([chat, ...chats])
    setCurrentId(id)
  }
  const ensureCurrent = (): Chat => {
    const c = chats.find(x => x.id === currentId)
    if (c) return c
    const id = generateSessionId()
    const chat: Chat = { id, title: 'New chat', msgs: [], langCode: uiLang }
    const next = [chat, ...chats]
    setCurrentId(id)
    persist(next)
    return chat
  }

  useEffect(() => {
    try {
      const saved = typeof window !== 'undefined' ? window.localStorage.getItem('nysc_lang') : null
      if (saved && ['en', 'yo', 'ig', 'ha'].includes(saved)) {
        setSelectedLang(saved as any)
        setLang(saved as any)
      }
    } catch { }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const translateChats = async () => {
      let changed = false
      const nextChats = await Promise.all(chats.map(async (c) => {
        if (c.msgs.length > 0 && c.langCode !== uiLang) {
          try {
            const textsToTranslate = c.msgs.map(m => m.content)
            const data = await translateTexts(uiLang, textsToTranslate)
            if (data.translations && data.translations.length === textsToTranslate.length) {
              changed = true
              return { ...c, langCode: uiLang, msgs: c.msgs.map((m, i) => ({ ...m, content: data.translations[i], langName: undefined, langCode: uiLang })) }
            }
          } catch (err) { console.error('Failed to translate history:', err) }
        }
        if (c.msgs.length === 0 && c.langCode !== uiLang) { changed = true; return { ...c, langCode: uiLang } }
        return c
      }))
      if (changed) {
        setChats(nextChats)
        if (authed) { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(nextChats)) } catch { } }
      }
    }
    translateChats()
  }, [uiLang, chats.length])

  useEffect(() => {
    const a = isAuthed()
    setAuthed(a)
    if (!a) setShowAnonNotice(true)
    const u = getUser()
    setUserName(u?.name || null)
    if (a) {
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (raw) { const saved: Chat[] = JSON.parse(raw); setChats(saved); if (saved.length) setCurrentId(saved[0].id); else newChat() }
        else newChat()
      } catch { newChat() }
    } else { newChat() }
  }, [])

  useEffect(() => { reloadCorpus() }, [])
  useEffect(() => { if (!listRef.current) return; listRef.current.scrollTop = listRef.current.scrollHeight }, [messages, loading])

  // Auto-resize textarea
  useEffect(() => {
    if (!textareaRef.current) return
    textareaRef.current.style.height = 'auto'
    textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 140) + 'px'
  }, [input])

  const appendMsg = (m: Msg, chatId?: string) => {
    const cid = chatId ?? currentId
    if (!cid) return
    setChats(prev => {
      let found = false
      const next = prev.map(c => {
        if (c.id === cid) { found = true; return { ...c, title: titleFor(c, m), msgs: [...c.msgs, m] } }
        return c
      })
      if (!found) {
        const created: Chat = { id: cid, title: m.role === 'user' ? (m.content.split(/\s+/).slice(0, 6).join(' ') || 'New chat') : 'New chat', msgs: [m], langCode: uiLang }
        next.unshift(created)
      }
      if (authed) { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { } }
      return next
    })
  }
  const titleFor = (c: Chat, m: Msg) => {
    if (c.msgs.length > 0 || m.role !== 'user') return c.title
    return m.content.split(/\s+/).slice(0, 6).join(' ') || 'New chat'
  }

  const send = async () => {
    if (!input.trim() || loading) return
    if (!authed && anonQuestionCount >= ANON_LIMIT) { setShowLoginGate(true); return }
    const target = ensureCurrent()
    const targetId = target.id
    const text = input.trim()
    const userMsg: Msg = { id: generateSessionId(), role: 'user', content: text, langCode: uiLang }
    appendMsg(userMsg, targetId)
    setInput('')
    if (!authed && !isGreeting(text)) setAnonQuestionCount(prev => prev + 1)
    if (isGreeting(text)) {
      const ai: Msg = { id: generateSessionId(), role: 'assistant', content: t('chat_greeting'), langCode: uiLang }
      appendMsg(ai, targetId)
      return
    }
    setLoading(true)
    try {
      const data = await sendMessage({ session_id: sessionIdRef.current!, message: text, selectedLang: selectedLang === 'auto' ? '' : selectedLang })
      const aiId = generateSessionId()
      const ai: Msg = { id: aiId, role: 'assistant', content: '', langName: data.detected_language_name, langCode: uiLang }
      appendMsg(ai, targetId)
      typeOut(String(data.answer || ''), targetId, aiId, data.sources || [])
      return
    } catch {
      const ai: Msg = { id: generateSessionId(), role: 'assistant', content: `Unable to reach the NYSC assistant at ${BASE_URL}. Please check your connection or ensure the backend is running.`, langCode: uiLang }
      appendMsg(ai, targetId)
    } finally { setLoading(false) }
  }

  const Sidebar = ({ inDrawer = false }: { inDrawer?: boolean }) => (
    <div className={`flex flex-col h-full ${inDrawer ? 'w-full' : ''}`}>
      {/* Brand */}
      <div className="flex items-center gap-3 p-5 border-b border-[var(--border-default)]">
        <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC" width={32} height={32} className="rounded-full" />
        <div>
          <div className="font-display text-sm text-primary leading-tight">NYSC AI</div>
          <div className="text-[10px] text-secondary">Official Assistant</div>
        </div>
        {inDrawer && <button onClick={() => setSidebarOpen(false)} className="ml-auto text-secondary hover:text-primary"><X className="w-4 h-4" /></button>}
      </div>

      {/* New Chat */}
      <div className="p-4">
        <button
          onClick={() => { newChat(); setSidebarOpen(false) }}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-semibold text-white text-sm bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)] hover:opacity-90 hover:scale-[1.01] transition-all shadow-lg shadow-green-900/20 relative overflow-hidden"
        >
          <span className="absolute inset-0 animate-shimmer pointer-events-none" />
          <Plus className="w-4 h-4" /> {t('chat_new_chat') || 'New Chat'}
        </button>
      </div>

      {/* Search */}
      <div className="px-4 pb-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-secondary" />
          <input
            className="w-full bg-[var(--bg-primary)] border border-[var(--border-default)] rounded-full pl-8 pr-4 py-2 text-xs text-primary focus:outline-none focus:ring-2 focus:ring-[var(--accent-end)] transition-all"
            placeholder={t('chat_search_history') || 'Search chats…'}
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>
      </div>

      {/* History */}
      <div className="px-3 mb-2">
        <div className="text-[10px] font-black text-secondary uppercase tracking-widest px-2">{t('chat_history') || 'History'}</div>
      </div>
      <div className="flex-1 overflow-y-auto px-3 space-y-0.5">
        {filteredChats.map(c => (
          <button
            key={c.id}
            onClick={() => { setCurrentId(c.id); setSidebarOpen(false) }}
            className={`w-full text-left px-3 py-2.5 rounded-lg text-xs transition-all duration-150 group ${c.id === currentId ? 'bg-[var(--surface-elevated)] border-l-2 border-[var(--accent-end)] text-primary font-semibold' : 'text-secondary hover:bg-[var(--bg-primary)] hover:text-primary'}`}
            title={c.title}
          >
            <div className="truncate">{c.title}</div>
          </button>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-[var(--border-default)] space-y-1">
        <button className="w-full flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-xs text-secondary hover:text-primary hover:bg-[var(--bg-primary)] transition-all"
          onClick={() => router.push('/preferences')}>
          <Settings className="w-3.5 h-3.5" /> {t('chat_preferences') || 'Preferences'}
        </button>
        <button className="w-full flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-xs text-secondary hover:text-primary hover:bg-[var(--bg-primary)] transition-all"
          onClick={() => { signOut(); router.replace('/login') }}>
          <LogOut className="w-3.5 h-3.5" /> {t('chat_logout') || 'Logout'}
        </button>
      </div>
    </div>
  )

  return (
    <motion.main
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="h-[100dvh] flex text-primary overflow-hidden"
      style={{ background: 'var(--bg-primary)' }}
    >
      {/* ── Desktop Sidebar ─────────────────────────── */}
      <aside
        className="hidden md:flex w-72 flex-col border-r border-[var(--border-default)] backdrop-blur-sm"
        style={{ background: 'var(--sidebar-bg)' }}
      >
        <Sidebar />
      </aside>

      {/* ── Mobile Sidebar Drawer ────────────────────── */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: -320 }} animate={{ x: 0 }} exit={{ x: -320 }}
              transition={{ type: 'spring', damping: 28, stiffness: 280 }}
              className="fixed left-0 top-0 bottom-0 w-72 z-50 border-r border-[var(--border-default)] md:hidden"
              style={{ background: 'var(--sidebar-bg)' }}
            >
              <Sidebar inDrawer />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ── Main Chat Area ───────────────────────────── */}
      <section className="flex-1 flex flex-col min-w-0 relative">
        {/* Top bar */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border-default)]" style={{ background: 'var(--bg-secondary)' }}>
          <button className="md:hidden p-2 rounded-lg text-secondary hover:text-primary hover:bg-[var(--bg-primary)] transition-all" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5" />
          </button>
          <button onClick={() => router.push('/welcome')} className="flex items-center gap-1.5 text-xs text-secondary hover:text-primary transition-colors px-2 py-1.5 rounded-lg hover:bg-[var(--bg-primary)]">
            <ArrowLeft className="w-3.5 h-3.5" /> Back
          </button>

          <div className="ml-auto flex items-center gap-2">
            {/* Lang dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowLangDropdown(!showLangDropdown)}
                className="flex items-center gap-1.5 text-xs border border-[var(--border-default)] rounded-lg px-3 py-1.5 text-secondary hover:border-[var(--accent-end)] hover:text-primary transition-all"
              >
                <Globe className="w-3 h-3" />
                {LANGUAGES.find(l => l.code === selectedLang)?.label}
                <ChevronDown className={`w-3 h-3 transition-transform ${showLangDropdown ? 'rotate-180' : ''}`} />
              </button>
              {showLangDropdown && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowLangDropdown(false)} />
                  <div className="absolute right-0 mt-2 w-36 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-xl shadow-xl z-20 overflow-hidden">
                    {LANGUAGES.map(l => (
                      <button
                        key={l.code}
                        onClick={() => {
                          setSelectedLang(l.code as any)
                          if (l.code !== 'auto') setLang(l.code as any)
                          setShowLangDropdown(false)
                        }}
                        className={`w-full text-left px-4 py-2.5 text-xs transition-colors ${selectedLang === l.code ? 'bg-[var(--sidebar-bg)] text-[var(--accent-start)] font-semibold' : 'text-secondary hover:bg-[var(--bg-primary)]'}`}
                      >
                        {l.label}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="flex items-center gap-1.5 pl-2 border-l border-[var(--border-default)]">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] flex items-center justify-center text-white text-[10px] font-bold">
                {userName ? userName[0].toUpperCase() : 'N'}
              </div>
              <span className="hidden sm:inline text-xs font-medium text-secondary">{userName || 'Guest'}</span>
            </div>
          </div>
        </div>

        {/* Anonymous notice */}
        {showAnonNotice && (
          <div className="px-4 py-2 bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-200 flex items-center justify-between">
            <span>Chats aren't saved. <a className="underline font-semibold" href="/signup">Sign up</a> or <a className="underline font-semibold" href="/login">log in</a> to store history.</span>
            <button onClick={() => setShowAnonNotice(false)} className="ml-4 text-amber-600 hover:text-amber-800"><X className="w-3 h-3" /></button>
          </div>
        )}

        {/* Messages */}
        <div ref={listRef} className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {/* Empty state */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-12 animate-in fade-in duration-500">
              <Image src="/NYSC-Nigeria-Logo.png" alt="NYSC" width={80} height={80} className="rounded-full opacity-20 mb-6" />
              <h2 className="font-display text-3xl md:text-4xl text-primary mb-2">{t('chat_assist_title')}</h2>
              <p className="text-sm text-secondary mb-10 max-w-xs">Policy-grounded answers in English, Yorùbá, Hausa, and Igbo — instantly.</p>
              <div className="flex flex-wrap gap-3 justify-center max-w-lg">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s.label}
                    onClick={() => setInput(s.label)}
                    className="flex flex-col items-start gap-0.5 border border-[var(--border-default)] hover:border-[var(--accent-end)] bg-[var(--bg-secondary)] hover:bg-[var(--surface-elevated)] rounded-xl px-4 py-3 text-left transition-all hover:-translate-y-0.5 group"
                  >
                    <span className="text-xs font-semibold text-primary group-hover:text-[var(--accent-start)]">{s.label}</span>
                    <span className="text-[10px] text-secondary">{s.sub}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages list */}
          <AnimatePresence initial={false}>
            {messages.map((m, idx) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: idx === messages.length - 1 ? 0 : 0 }}
                className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}
              >
                {m.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] flex-shrink-0 flex items-center justify-center mr-2 mt-1 shadow">
                    <Image src="/NYSC-Nigeria-Logo.png" alt="AI" width={18} height={18} className="rounded-full" />
                  </div>
                )}
                <div className={`max-w-[80%] flex flex-col gap-1`}>
                  {m.langName && m.langName !== 'English' && m.role === 'assistant' && (
                    <div className="text-[10px] text-secondary">🌐 {m.langName}</div>
                  )}
                  <div
                    className={`px-4 py-3 text-sm leading-relaxed ${m.role === 'user'
                        ? 'bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] text-white shadow-lg shadow-green-900/20'
                        : 'bg-[var(--surface-elevated)] border border-[var(--border-default)] text-primary whitespace-pre-wrap'
                      }`}
                    style={{
                      borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '4px 18px 18px 18px',
                    }}
                  >
                    {renderContent(m.content)}
                  </div>
                  {/* Source pills */}
                  {m.sources && m.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {m.sources.map((s, si) => (
                        <span key={si} className="text-[10px] border border-[var(--border-default)] bg-[var(--bg-primary)] text-secondary px-2 py-0.5 rounded-full">
                          📄 {s.source}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Loading indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] flex-shrink-0 flex items-center justify-center mr-2 mt-1">
                <Image src="/NYSC-Nigeria-Logo.png" alt="AI" width={18} height={18} className="rounded-full" />
              </div>
              <div className="bg-[var(--surface-elevated)] border border-[var(--border-default)] px-5 py-4 flex items-center gap-1.5" style={{ borderRadius: '4px 18px 18px 18px' }}>
                <span className="w-2 h-2 rounded-full bg-[var(--accent-end)] dot-1" />
                <span className="w-2 h-2 rounded-full bg-[var(--accent-end)] dot-2" />
                <span className="w-2 h-2 rounded-full bg-[var(--accent-end)] dot-3" />
              </div>
            </div>
          )}
        </div>

        {/* ── Input Area ──────────────────────────────── */}
        <div className="relative px-4 pb-4 pt-2">
          {/* Top fade gradient */}
          <div className="absolute -top-8 left-0 right-0 h-8 bg-gradient-to-t from-[var(--bg-primary)] to-transparent pointer-events-none" />

          <div className="rounded-2xl border border-[var(--border-default)] bg-[var(--bg-secondary)] shadow-lg shadow-green-900/5 p-3 flex items-end gap-3">
            {/* Mic button */}
            <button
              onClick={() => alert(t('coming_soon'))}
              className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)] text-secondary hover:text-[var(--accent-start)] hover:border-[var(--accent-end)] transition-all"
              title={t('chat_voice_input')}
            >
              <Mic className="w-4 h-4" />
            </button>

            {/* Textarea */}
            <textarea
              ref={textareaRef}
              className="flex-1 resize-none bg-transparent text-sm text-primary placeholder:text-secondary/60 focus:outline-none leading-relaxed min-h-[36px] max-h-[140px]"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={t('chat_placeholder') || 'Ask me anything about NYSC…'}
              rows={1}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
            />

            {/* Send button */}
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-xl text-white bg-gradient-to-br from-[var(--accent-start)] to-[var(--accent-end)] disabled:opacity-40 hover:opacity-90 hover:scale-105 active:scale-95 transition-all shadow-md shadow-green-900/20"
              aria-label="Send"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* Anonymous limit gate */}
      {showLoginGate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[var(--bg-secondary)] rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)] px-6 py-5 text-white text-center">
              <div className="text-3xl mb-1">🎓</div>
              <div className="font-semibold text-lg">You've used {ANON_LIMIT} free questions</div>
              <div className="text-green-100 text-sm mt-1">Create a free account to continue</div>
            </div>
            <div className="px-6 py-5 space-y-3">
              <a href="/signup" className="block w-full text-center py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-[var(--accent-start)] to-[var(--accent-end)] hover:opacity-90 transition-all">Create Free Account</a>
              <a href="/login" className="block w-full text-center py-3 rounded-xl font-semibold border border-[var(--border-default)] text-[var(--accent-start)] hover:border-[var(--accent-end)] transition-all">Log In</a>
              <button onClick={() => setShowLoginGate(false)} className="block w-full text-center text-xs text-secondary hover:text-primary py-1 transition-colors">Dismiss</button>
            </div>
          </div>
        </div>
      )}
    </motion.main>
  )
}

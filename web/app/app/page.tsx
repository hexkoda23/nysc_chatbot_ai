"use client"
import { useEffect, useRef, useState } from 'react'
import { getUser, isAuthed, signOut } from '../../lib/auth'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Mic, Send, Plus, LogOut, Settings, Search } from 'lucide-react'
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
  const listRef = useRef<HTMLDivElement>(null)
  const { t, lang: uiLang, setLang } = useI18n()
  // Chat answer language:
  // - "auto" => backend detects from the question and answers in that language
  // - explicit code => force backend to answer in that language
  const [selectedLang, setSelectedLang] = useState<'auto' | 'en' | 'yo' | 'ig' | 'ha'>('auto')
  const sessionIdRef = useRef<string>(undefined)
  if (!sessionIdRef.current) sessionIdRef.current = generateSessionId()
  // Anonymous user question limit
  const ANON_LIMIT = 5
  const [anonQuestionCount, setAnonQuestionCount] = useState(0)
  const [showLoginGate, setShowLoginGate] = useState(false)
  const renderContent = (text: string) => {
    const parts = text.split(/(https?:\/\/[^\s]+)/g)
    return parts.map((p, i) => {
      const clean = p.replace(/^`+|`+$/g, '')
      if (/^https?:\/\/[^\s]+$/.test(clean)) {
        return (
          <a
            key={i}
            href={clean}
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            {clean}
          </a>
        )
      }
      return <span key={i}>{p}</span>
    })
  }

  const filteredChats = query
    ? chats.filter(c => c.title.toLowerCase().includes(query.toLowerCase()))
    : chats
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
        return {
          ...c,
          msgs: c.msgs.map(m => (m.id === mid ? { ...m, content, sources: sources ?? m.sources } : m)),
        }
      })
      if (authed) {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { }
      }
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
      if (i < total) {
        setTimeout(tick, 16)
      } else {
        updateMsgContent(cid, mid, text, sources)
        setLoading(false)
      }
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
      const saved = typeof window !== 'undefined'
        ? window.localStorage.getItem('nysc_lang')
        : null
      if (saved && ['en', 'yo', 'ig', 'ha'].includes(saved)) {
        setSelectedLang(saved as 'en' | 'yo' | 'ig' | 'ha')
        setLang(saved as any)
      }
    } catch {
      // ignore storage errors (private mode, etc.)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Centralized retroactive translation when uiLang changes
  useEffect(() => {
    if (typeof window === 'undefined') return
    const translateChats = async () => {
      let changed = false
      const nextChats = await Promise.all(
        chats.map(async (c) => {
          // If the chat has messages and its language code doesn't match the current UI language
          if (c.msgs.length > 0 && c.langCode !== uiLang) {
            try {
              const textsToTranslate = c.msgs.map(m => m.content)
              const data = await translateTexts(uiLang, textsToTranslate)
              if (data.translations && data.translations.length === textsToTranslate.length) {
                changed = true
                return {
                  ...c,
                  langCode: uiLang,
                  msgs: c.msgs.map((m, i) => ({
                    ...m,
                    content: data.translations[i],
                    langName: undefined,
                    langCode: uiLang
                  }))
                }
              }
            } catch (err) {
              console.error("Failed to translate history:", err)
            }
          }
          // Default to setting the langCode if newly created / empty
          if (c.msgs.length === 0 && c.langCode !== uiLang) {
            changed = true;
            return { ...c, langCode: uiLang }
          }
          return c
        })
      )
      if (changed) {
        setChats(nextChats)
        if (authed) {
          try { localStorage.setItem(STORAGE_KEY, JSON.stringify(nextChats)) } catch { }
        }
      }
    }
    translateChats()
  }, [uiLang, chats.length]) // run when uiLang changes or total chats changes


  useEffect(() => {
    const a = isAuthed()
    setAuthed(a)
    if (!a) setShowAnonNotice(true)
    const u = getUser()
    setUserName(u?.name || null)
    if (a) {
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (raw) {
          const saved: Chat[] = JSON.parse(raw)
          setChats(saved)
          if (saved.length) setCurrentId(saved[0].id)
          else newChat()
        } else {
          newChat()
        }
      } catch {
        newChat()
      }
    } else {
      newChat()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Ensure backend picks up any new documents by reloading corpus once
  useEffect(() => {
    reloadCorpus()
    // fire-and-forget; safe in dev, idempotent on server
  }, [])

  useEffect(() => {
    if (!listRef.current) return
    listRef.current.scrollTop = listRef.current.scrollHeight
  }, [messages, loading])

  const appendMsg = (m: Msg, chatId?: string) => {
    const cid = chatId ?? currentId
    if (!cid) return
    setChats(prev => {
      let found = false
      const next = prev.map(c => {
        if (c.id === cid) {
          found = true
          return { ...c, title: titleFor(c, m), msgs: [...c.msgs, m] }
        }
        return c
      })
      if (!found) {
        const created: Chat = {
          id: cid,
          title: m.role === 'user' ? (m.content.split(/\s+/).slice(0, 6).join(' ') || 'New chat') : 'New chat',
          msgs: [m],
          langCode: uiLang
        }
        next.unshift(created)
      }
      if (authed) {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)) } catch { }
      }
      return next
    })
  }

  const titleFor = (c: Chat, m: Msg) => {
    if (c.msgs.length > 0 || m.role !== 'user') return c.title
    const t = m.content.split(/\s+/).slice(0, 6).join(' ')
    return t || 'New chat'
  }

  const send = async () => {
    if (!input.trim() || loading) return

    // Anonymous question gate
    if (!authed) {
      if (anonQuestionCount >= ANON_LIMIT) {
        setShowLoginGate(true)
        return
      }
    }
    const target = ensureCurrent()
    const targetId = target.id
    const text = input.trim()
    const userMsg: Msg = { id: generateSessionId(), role: 'user', content: text, langCode: uiLang }
    appendMsg(userMsg, targetId)
    setInput('')

    // Count this question for anonymous users (don't count greetings)
    if (!authed && !isGreeting(text)) {
      setAnonQuestionCount(prev => prev + 1)
    }

    // Greeting: respond politely immediately
    if (isGreeting(text)) {
      const ai: Msg = {
        id: generateSessionId(),
        role: 'assistant',
        content: t('chat_greeting'),
        langCode: uiLang
      }
      appendMsg(ai, targetId)
      return
    }

    setLoading(true)
    try {
      const data = await sendMessage({
        session_id: sessionIdRef.current!,
        message: text,
        selectedLang: selectedLang === 'auto' ? '' : selectedLang,
      })
      const aiId = generateSessionId()
      const ai: Msg = { id: aiId, role: 'assistant', content: '', langName: data.detected_language_name, langCode: uiLang }
      appendMsg(ai, targetId)
      typeOut(String(data.answer || ''), targetId, aiId, data.sources || [])
      return
    } catch (e) {
      const ai: Msg = {
        id: generateSessionId(),
        role: 'assistant',
        content: `Unable to reach the NYSC assistant at ${BASE_URL}. Please check your internet connection or ensure the backend is running.`,
        langCode: uiLang,
      }
      appendMsg(ai, targetId)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-[100dvh] bg-primary text-primary">

      {/* Login Gate Modal — shows after 5 anonymous questions */}
      {showLoginGate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="bg-green-600 px-6 py-4 text-white text-center">
              <div className="text-2xl mb-1">🎓</div>
              <div className="font-bold text-lg">You've used {ANON_LIMIT} free questions</div>
              <div className="text-green-100 text-sm mt-1">Create a free account to continue asking</div>
            </div>
            <div className="px-6 py-5">
              <p className="text-sm text-slate-600 dark:text-slate-400 text-center mb-5">
                Sign up or log in to get <strong>unlimited questions</strong>, save your chat history, and access all NYSC AI features — completely free.
              </p>
              <div className="space-y-3">
                <a
                  href="/signup"
                  className="block w-full text-center bg-green-600 hover:bg-green-700 text-white font-semibold py-2.5 rounded-xl transition-colors"
                >
                  Create Free Account
                </a>
                <a
                  href="/login"
                  className="block w-full text-center border border-green-600 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/30 font-semibold py-2.5 rounded-xl transition-colors"
                >
                  Log In
                </a>
                <button
                  onClick={() => setShowLoginGate(false)}
                  className="block w-full text-center text-xs text-slate-400 hover:text-slate-600 py-1 transition-colors"
                >
                  Dismiss (questions will be blocked)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Anonymous question counter — only visible to non-authed users */}
      {!authed && anonQuestionCount > 0 && !showLoginGate && (
        <div
          className="fixed bottom-24 right-4 z-30 bg-green-600 text-white text-xs px-3 py-1.5 rounded-full shadow-lg cursor-pointer"
          onClick={() => anonQuestionCount >= ANON_LIMIT && setShowLoginGate(true)}
          title="Free questions remaining"
        >
          {ANON_LIMIT - anonQuestionCount > 0
            ? `${ANON_LIMIT - anonQuestionCount} free question${ANON_LIMIT - anonQuestionCount !== 1 ? 's' : ''} left`
            : '⚠ Limit reached — Sign up to continue'}
        </div>
      )}

      <div className="flex h-[100dvh]">
        <aside className="hidden md:flex w-72 flex-col border-r border-default p-4 bg-sidebar">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 rounded-full bg-secondary border border-default flex items-center justify-center text-sm">
              {userName ? userName[0]?.toUpperCase() : 'N'}
            </div>
            <div className="text-sm">
              <div className="font-medium">{userName || 'NYSC Member'}</div>
              <div className="text-secondary">@nysc</div>
            </div>
          </div>
          <button
            onClick={newChat}
            className="mb-4 inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm accent"
            aria-label="New Chat"
          >
            <Plus size={16} /> New Chat
          </button>
          <div className="relative mb-3">
            <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-secondary" />
            <input
              className="w-full rounded-lg border border-default bg-secondary px-7 py-1.5 text-sm focus-ring"
              placeholder="Search chats…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="text-xs text-secondary mb-1">History</div>
          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {filteredChats.map(c => (
              <button
                key={c.id}
                onClick={() => setCurrentId(c.id)}
                className={
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors duration-150 ' +
                  (c.id === currentId ? 'bg-secondary' : 'hover:bg-secondary')
                }
                title={c.title}
              >
                {c.title}
              </button>
            ))}
          </div>
          <div className="mt-3 border-t border-default pt-3 space-y-2">
            <button
              className="w-full inline-flex items-center gap-2 rounded-lg border border-default bg-secondary px-3 py-2 text-left text-sm"
              onClick={() => router.push('/preferences')}
              title="Preferences"
            >
              <Settings size={16} /> Preferences
            </button>
            <button
              className="w-full inline-flex items-center gap-2 rounded-lg border border-default bg-secondary px-3 py-2 text-left text-sm"
              onClick={() => { signOut(); router.replace('/login') }}
              title="Logout"
            >
              <LogOut size={16} /> Logout
            </button>
          </div>
        </aside>

        <section className="flex-1">
          <div className="max-w-3xl mx-auto p-4">
            <div className="mb-3 flex items-center justify-center gap-2">
              <img src="/NYSC-Nigeria-Logo.png" alt="NYSC Logo" className="h-10 w-10 rounded-full" />
              <div className="text-center">
                <div className="text-xs font-bold text-green-700 tracking-wider leading-tight">NATIONAL YOUTH SERVICE CORPS</div>
                <div className="text-[9px] text-green-500 tracking-widest">• SERVICE AND HUMILITY •</div>
              </div>
            </div>
            <div className="mb-4 flex items-center justify-between">
              <button
                onClick={() => router.push('/welcome')}
                className="inline-flex items-center gap-1 rounded-lg border border-default bg-secondary px-3 py-1.5 text-sm"
              >
                <ArrowLeft size={14} /> Back
              </button>
              <select
                className="rounded-lg border border-default bg-secondary text-sm px-2 py-1"
                value={selectedLang}
                onChange={async (e) => {
                  const code = e.target.value as 'auto' | 'en' | 'yo' | 'ig' | 'ha'
                  setSelectedLang(code)
                  if (code !== 'auto') {
                    setLang(code as any)
                    // The retroactive translation is now handled centrally via the useEffect!
                  }
                }}
                title={t('language_label')}
              >
                <option value="auto">Auto</option>
                <option value="en">English</option>
                <option value="yo">Yorùbá</option>
                <option value="ig">Igbo</option>
                <option value="ha">Hausa</option>
              </select>
            </div>
            {showAnonNotice && (
              <div className="mb-3 rounded-xl border border-amber-300 bg-amber-50 text-amber-900 px-4 py-3 text-xs">
                Chats aren’t saved. <a className="underline" href="/signup">Sign up</a> or <a className="underline" href="/login">log in</a> to store history.
                <button onClick={() => setShowAnonNotice(false)} className="float-right underline">Dismiss</button>
              </div>
            )}

            <div className="rounded-2xl border border-default bg-secondary p-0 shadow-xl">
              <div className="p-6">
                <div className="mb-4 text-center">
                  <h2 className="text-2xl md:text-3xl font-semibold">{t('chat_assist_title')}</h2>
                </div>
                <div ref={listRef} className="h-[58vh] overflow-y-auto space-y-4">
                  {messages.length === 0 && (
                    <div className="grid gap-3 sm:grid-cols-2">
                      {[
                        [t('chat_suggest_redeploy'), t('chat_suggest_redeploy_sub')],
                        [t('chat_suggest_registration'), t('chat_suggest_registration_sub')],
                        [t('chat_suggest_change_ppa'), t('chat_suggest_change_ppa_sub')],
                        [t('chat_suggest_allowance'), t('chat_suggest_allowance_sub')],
                        [t('chat_suggest_callup'), t('chat_suggest_callup_sub')],
                        [t('chat_suggest_policy'), t('chat_suggest_policy_sub')],
                      ].map(([tq, sub]) => (
                        <button
                          key={tq}
                          onClick={() => setInput(tq)}
                          className="rounded-xl border border-default bg-primary px-4 py-3 text-left hover:translate-y-[-1px] transition-transform duration-150"
                        >
                          <div className="text-sm">{tq}</div>
                          <div className="text-xs text-secondary">{sub}</div>
                        </button>
                      ))}
                    </div>
                  )}
                  {messages.map((m) => (
                    <div key={m.id} className={m.role === 'user' ? 'text-right' : 'text-left'}>
                      <div
                        className={
                          'inline-block max-w-[80%] rounded-2xl px-4 py-2 text-sm leading-relaxed transition-colors duration-150 ' +
                          (m.role === 'user'
                            ? 'accent'
                            : 'bg-secondary border border-default whitespace-pre-wrap')
                        }
                      >
                        {m.langName && m.langName !== 'English' && m.role === 'assistant' ? (
                          <div className="text-[10px] text-secondary mb-1">🌐 {m.langName}</div>
                        ) : null}
                        {renderContent(m.content)}
                      </div>
                    </div>
                  ))}
                  {loading && <div className="text-xs text-secondary">Typing…</div>}
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <button
                    onClick={() => alert(t('coming_soon'))}
                    className="h-10 w-10 inline-flex items-center justify-center rounded-full border border-default bg-primary"
                    title={t('chat_voice_input')}
                  >
                    <Mic size={18} />
                  </button>
                  <input
                    className="flex-1 rounded-full border border-default px-4 py-2 bg-primary text-primary focus-ring"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask me anything about NYSC…"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault(); send()
                      }
                    }}
                  />
                  <div className="hidden md:flex items-center gap-2">
                    {(['auto', 'en', 'yo', 'ig', 'ha'] as const).map((code) => (
                      <button
                        key={code}
                        onClick={async () => {
                          setSelectedLang(code)
                          if (code !== 'auto') {
                            setLang(code as any)
                            // The retroactive translation is now handled centrally via the useEffect!
                          }
                        }}
                        className={
                          'rounded-full border px-3 py-1 text-xs ' +
                          (selectedLang === code ? 'accent' : 'bg-secondary border-default')
                        }
                        title={code}
                      >
                        {code === 'auto' ? 'Auto' : code.toUpperCase()}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={send}
                    disabled={loading || !input.trim()}
                    className="h-10 w-10 inline-flex items-center justify-center rounded-full accent disabled:opacity-50"
                    aria-label="Send"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}

 "use client"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useTheme } from "next-themes"
import { useI18n } from "@/components/i18n"

type Prefs = {
  suggestions: boolean
  saveHistory: boolean
  language: string
}

const STORAGE_KEY = "nysc_prefs"

export default function PreferencesPage() {
  const router = useRouter()
  const { theme, setTheme, systemTheme } = useTheme()
  const { t, setLang } = useI18n()
  const [prefs, setPrefs] = useState<Prefs>({ suggestions: true, saveHistory: true, language: "en" })
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        setPrefs(JSON.parse(raw))
      } else {
        const savedLang = localStorage.getItem("nysc_lang")
        if (savedLang && ["en", "yo", "ig", "ha"].includes(savedLang)) {
          setPrefs((p) => ({ ...p, language: savedLang }))
        }
      }
    } catch {}
    setLoaded(true)
  }, [])

  const save = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
      if (!prefs.saveHistory) localStorage.removeItem("nysc_chats")
      if (prefs.language && ["en", "yo", "ig", "ha"].includes(prefs.language)) {
        localStorage.setItem("nysc_lang", prefs.language)
        setLang(prefs.language as any)
      }
    } catch {}
  }

  const Toggle = ({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) => (
    <button
      onClick={() => onChange(!checked)}
      aria-pressed={checked}
      className={
        "h-6 w-11 rounded-full transition-colors " +
        (checked ? "bg-emerald-600" : "bg-slate-400 dark:bg-slate-600")
      }
    >
      <span
        className={
          "block h-5 w-5 bg-white rounded-full translate-y-[2px] transition-transform " +
          (checked ? "translate-x-6" : "translate-x-1")
        }
      />
    </button>
  )

  return (
    <main className="min-h-[100dvh] bg-primary text-primary">
      <div className="max-w-3xl mx-auto p-4">
        <div className="mb-4 flex items-center justify-between">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 rounded-lg border border-default bg-secondary px-3 py-1.5 text-sm"
          >
            {t("chat_back")}
          </button>
          <button
            onClick={() => { save(); router.push("/app") }}
            className="inline-flex items-center gap-2 rounded-lg accent px-3 py-1.5 text-sm"
          >
            {t("modal_continue")}
          </button>
        </div>

        <div className="rounded-2xl border border-default bg-secondary shadow-xl">
          <div className="p-6 space-y-6">
            <div>
              <div className="text-lg font-semibold mb-1">Appearance</div>
              <div className="text-xs text-secondary mb-3">Choose how NYSC AI looks on your device.</div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {[
                  ["system", "System"],
                  ["light", "Light"],
                  ["dark", "Dark"],
                ].map(([val, label]) => (
                  <button
                    key={val}
                    onClick={() => setTheme(val)}
                    className={
                      "rounded-lg border px-3 py-2 text-sm " +
                      (theme === val || (!theme && val === "system") ? "border-emerald-500" : "border-default bg-primary")
                    }
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="mt-2 text-xs text-secondary">
                Current: {theme || "system"} {theme === "system" && systemTheme ? `(${systemTheme})` : ""}
              </div>
            </div>

            <div className="border-t border-default pt-4">
              <div className="text-lg font-semibold mb-1">Chat Suggestions</div>
              <div className="flex items-center justify-between rounded-lg border border-default bg-primary px-3 py-2">
                <div className="text-sm">Show quick suggestions on an empty chat</div>
                <Toggle
                  checked={prefs.suggestions}
                  onChange={(v) => setPrefs((p) => ({ ...p, suggestions: v }))}
                />
              </div>
            </div>

            <div className="border-t border-default pt-4">
              <div className="text-lg font-semibold mb-1">Save Chat History</div>
              <div className="flex items-center justify-between rounded-lg border border-default bg-primary px-3 py-2">
                <div className="text-sm">Store chats on this device for signed-in users</div>
                <Toggle
                  checked={prefs.saveHistory}
                  onChange={(v) => setPrefs((p) => ({ ...p, saveHistory: v }))}
                />
              </div>
              <div className="mt-2 text-xs text-secondary">
                Turning this off clears local chat history storage.
              </div>
            </div>

            <div className="border-t border-default pt-4">
              <div className="text-lg font-semibold mb-1">{t("language_label")}</div>
              <select
                value={prefs.language}
                onChange={(e) => setPrefs((p) => ({ ...p, language: e.target.value }))}
                className="rounded-lg border border-default bg-primary px-3 py-2 text-sm"
              >
                <option value="en">English</option>
                <option value="yo">Yorùbá</option>
                <option value="ig">Igbo</option>
                <option value="ha">Hausa</option>
              </select>
            </div>
          </div>
        </div>

        {loaded && (
          <div className="mt-4 flex gap-2">
            <button
              onClick={save}
              className="rounded-lg border border-default bg-primary px-3 py-2 text-sm"
            >
              {t("modal_continue")}
            </button>
            <button
              onClick={() => router.push("/app")}
              className="rounded-lg border border-default bg-primary px-3 py-2 text-sm"
            >
              {t("dismiss_label")}
            </button>
          </div>
        )}
      </div>
    </main>
  )
}

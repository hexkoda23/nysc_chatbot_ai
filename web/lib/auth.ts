export type User = {
  name: string
  email: string
  createdAt: number
}

const KEY = 'nysc_auth'

export function isAuthed(): boolean {
  if (typeof window === 'undefined') return false
  return !!localStorage.getItem(KEY)
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null
  const raw = localStorage.getItem(KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function signInOrUp(user: { name: string; email: string }) {
  if (typeof window === 'undefined') return
  const payload: User = { ...user, createdAt: Date.now() }
  localStorage.setItem(KEY, JSON.stringify(payload))
}

export function signOut() {
  if (typeof window === 'undefined') return
  localStorage.removeItem(KEY)
}

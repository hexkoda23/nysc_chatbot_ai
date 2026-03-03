// web/lib/auth.ts

export interface User {
  id: string;
  name: string;
  phone: string;
  language: string;
  createdAt: string;
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("nysc_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setUser(user: User): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("nysc_user", JSON.stringify(user));
}

export function clearUser(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("nysc_user");
}

export function isAuthed(): boolean {
  return !!getUser();
}

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("nysc_token");
}

export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("nysc_token", token);
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("nysc_token");
}

export function signOut(): void {
  clearUser();
  clearAuthToken();
}

export function signInOrUp(user: { name: string; email: string }): void {
  const newUser: User = {
    id: Math.random().toString(36).substring(2),
    name: user.name,
    phone: '',
    language: 'en',
    createdAt: new Date().toISOString()
  };
  setUser(newUser);
  setAuthToken("mock_token_" + newUser.id);
}
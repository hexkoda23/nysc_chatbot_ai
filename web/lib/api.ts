// web/lib/api.ts

export const BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
    session_id: string;
    message: string;
    selectedLang: string;
}

export interface ChatResponse {
    answer: string;
    sources: {
        source: string;
        snippet: string;
        title?: string;
        filepath?: string;
        source_url?: string;
        topic?: string;
        score?: number;
    }[];
    detected_language: string;
    detected_language_name: string;
    message_id?: string;
    conversation_id?: string;
    is_fallback?: boolean;
    provider?: string | null;
    confidence?: number;
    low_confidence?: boolean;
}

export async function sendMessage(
    payload: ChatMessage
): Promise<ChatResponse> {
    const res = await fetch(`${BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

export async function checkHealth(): Promise<{ status: string }> {
    const res = await fetch(`${BASE_URL}/health`);
    return res.json();
}

export async function translateTexts(
    target_lang: string,
    texts: string[]
): Promise<{ translations: string[] }> {
    const res = await fetch(`${BASE_URL}/api/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_lang, texts }),
    });
    if (!res.ok) throw new Error(`Translation error: ${res.status}`);
    return res.json();
}

export async function reloadCorpus(): Promise<void> {
    await fetch(`${BASE_URL}/api/reload`, { method: "POST" }).catch(() => { });
}

export async function sendFeedback(payload: {
    message_id: string;
    rating: "good" | "bad";
    comment?: string;
}): Promise<{ status: string; id: number }> {
    const res = await fetch(`${BASE_URL}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Feedback error: ${res.status}`);
    return res.json();
}

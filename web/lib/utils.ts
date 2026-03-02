// web/lib/utils.ts

export function cn(...classes: (string | undefined | null | false)[]) {
    return classes.filter(Boolean).join(" ");
}

export function generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export function formatTime(date: Date): string {
    return date.toLocaleTimeString("en-NG", {
        hour: "2-digit",
        minute: "2-digit",
    });
}
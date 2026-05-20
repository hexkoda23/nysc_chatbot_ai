from __future__ import annotations

import re
from typing import List, Optional


LANG_CODES = {"en", "yo", "ig", "ha"}


def detect_language(text: str) -> str:
    lowered = text.lower()
    if any(ch in lowered for ch in ("ṣ", "ẹ", "ọ", "à", "á", "è", "é", "ì", "ò", "ù")):
        return "yo"
    if any(ch in lowered for ch in ("ị", "ụ", "ṅ")) or any(word in lowered for word in ("kedu", "ndị", "anyị")):
        return "ig"
    if any(ch in lowered for ch in ("ƙ", "ɗ")) or any(word in lowered for word in ("sannu", "yaya", "zaka", "zan")):
        return "ha"
    return "en"


def translate_to_english(text: str, source_lang: str) -> str:
    return text


def translate_from_english(text: str, target_lang: str) -> str:
    return text


def translate_texts(texts: List[str], target_lang: str, source_lang: Optional[str] = None) -> List[str]:
    # Translation is deliberately a no-cost fallback. The chat endpoint can still answer
    # in the selected language when an LLM provider is configured.
    if target_lang not in LANG_CODES:
        return texts
    return [re.sub(r"\s+$", "", text) for text in texts]

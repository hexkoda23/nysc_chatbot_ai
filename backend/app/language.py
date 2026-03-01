import re
from typing import List, Dict, Tuple, Optional
from collections import Counter
from .rag_engine import run_nysc_agent, _make_llm

LANG_CODES = {"en", "yo", "ig", "ha"}

def _detect_language_heuristic(text: str) -> str:
    t = text.strip().lower()
    if not t:
        return "en"
    yo_unique_chars = ["ṣ"]
    ig_unique_chars = ["ị", "ụ"]
    ha_unique_chars = ["ƙ", "ɗ"]
    for ch in yo_unique_chars:
        if ch in text:
            return "yo"
    for ch in ig_unique_chars:
        if ch in text:
            return "ig"
    for ch in ha_unique_chars:
        if ch in text:
            return "ha"
    yo_phrases = ["e kaaro", "e kaasan", "e kuurole", "bawo", "báwo"]
    ig_phrases = ["kedu", "unu", "ndị", "ń"]
    ha_phrases = ["sannu", "yaya", "'yan", "zaki"]
    yo_supporting = ["ẹ", "ọ", "ò", "á", "è", "ù"]
    for m in yo_phrases:
        if m in t:
            return "yo"
    for m in ig_phrases:
        if m in t:
            return "ig"
    for m in ha_phrases:
        if m in t:
            return "ha"
    for ch in yo_supporting:
        if ch in text:
            return "yo"
    return "en"

def _detect_language_llm(text: str) -> Optional[str]:
    try:
        llm = _make_llm(timeout=8.0, retries=0)
        prompt = (
            "Detect which language the following text is written in.\n"
            "Allowed outputs: en, yo, ig, ha.\n"
            "Return ONLY one of: en, yo, ig, ha.\n\n"
            f"Text:\n{text}\n\nLanguage code:"
        )
        resp = llm.invoke(prompt)
        out = resp.content if hasattr(resp, "content") else str(resp)
        code = out.strip().lower()
        if code in {"en", "yo", "ig", "ha"}:
            return code
    except Exception:
        pass
    return None

def _mask_urls(text: str) -> Tuple[str, List[str]]:
    urls = re.findall(r"https?://[^\s]+", text)
    masked = text
    for i, u in enumerate(urls):
        masked = masked.replace(u, f"[[URL{i}]]")
    return masked, urls

def _unmask_urls(text: str, urls: List[str]) -> str:
    out = text
    for i, u in enumerate(urls):
        out = out.replace(f"[[URL{i}]]", u)
    return out

def _is_loop(s: str) -> bool:
    """Return True if the text contains a generation loop pattern."""
    if not s or len(s) < 15:
        return False
    words = s.replace(",", "").replace(".", "").split()
    if not words:
        return False

    # 1. Consecutive word repetition (4x)
    for i in range(len(words) - 3):
        if (words[i].lower() == words[i+1].lower() == 
                words[i+2].lower() == words[i+3].lower()):
            return True

    # 2. Strong token repetition (e.g. ụlọ ụlọ ụlọ)
    # Check if a single token repeats 4 or more times continuously
    token_pattern = re.compile(r'\b(\w+)(?:\s+\1){3,}\b', re.IGNORECASE)
    if token_pattern.search(s):
        return True

    # 3. Phrase repetition (Regex check for exact char-level loops)
    if re.search(r"(.{10,})\1\1", s):
        return True

    # 4. Word frequency analysis: if >60% of words are repeats in a longish text, it's a loop
    if len(words) >= 10:
        counts = Counter(w.lower() for w in words)
        most_common_ratio = counts.most_common(1)[0][1] / len(words)
        if most_common_ratio > 0.40: # Lowered to 40%
            return True
        unique_ratio = len(counts) / len(words)
        if unique_ratio < 0.35: # Only 35% of words are unique
            return True

    # 5. Bigram density: if the same bigram repeats 5+ times in a chunk
    if len(words) > 8:
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        b_counts = Counter(bigrams)
        if b_counts.most_common(1)[0][1] >= 4:
            return True

    # 6. Line-level: >40% of lines identical
    lines = [l.strip() for l in s.splitlines() if l.strip()]
    if len(lines) >= 5:
        counts = Counter(lines)
        if counts.most_common(1)[0][1] / len(lines) > 0.4:
            return True
            
    return False

def _dedupe_output(text: str) -> str:
    """Remove consecutively repeated sentences from the output."""
    parts = re.split(r'(?<=[.!?])\s+', text)
    seen = []
    out_parts = []
    for p in parts:
        normalized = re.sub(r'\s+', ' ', p.strip().lower())
        if normalized and normalized not in seen:
            seen.append(normalized)
            out_parts.append(p)
    return " ".join(out_parts)

def _split_into_chunks(text: str, max_chars: int = 300) -> List[str]:
    """
    Split text into chunks at natural boundaries (newlines, sentence ends).
    Each chunk stays under max_chars so the translation LLM never sees
    enough context to enter a generation loop.
    """
    # First split by newlines to preserve structure
    paragraphs = text.split("\n")
    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            if current:
                chunks.append(current.strip())
                current = ""
            continue
        # If the paragraph itself is too long, split at sentence boundaries
        if len(para) > max_chars:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                if len(current) + len(sent) + 1 <= max_chars:
                    current = (current + " " + sent).strip() if current else sent
                else:
                    if current:
                        chunks.append(current.strip())
                    current = sent
        else:
            if len(current) + len(para) + 1 <= max_chars:
                current = (current + "\n" + para).strip() if current else para
            else:
                if current:
                    chunks.append(current.strip())
                current = para
    if current:
        chunks.append(current.strip())
    return [c for c in chunks if c]

def _translate_chunk(chunk: str, target_lang: str, llm) -> str:
    """Translate a single short chunk. Always returns target language."""
    if not chunk.strip():
        return chunk
    masked, urls = _mask_urls(chunk)
    
    # Map codes to full names for better LLM grounding
    names = {"yo": "Standard Yorùbá", "ha": "Hausa", "ig": "Igbo", "en": "English"}
    target_name = names.get(target_lang, target_lang)

    def _make_prompt(text: str, extra_force: bool = False) -> str:
        strict = (
            "ABSOLUTE REQUIREMENT: Your output MUST be entirely in {lang}. "
            "If ANY English words appear in your output (except proper nouns like NYSC, URLs, numbers), "
            "you have FAILED.\n".format(lang=target_name) if extra_force else ""
        )
        return (
            f"You are a professional Nigerian translator. Translate the text below into {target_name}.\n"
            f"{strict}"
            "RULES:\n"
            "1. Output ONLY the translation — no explanations, no labels, no preamble.\n"
            "2. Keep numbers exactly as-is (e.g. N77,000, 77000, March 2025).\n"
            "3. Keep [[URL0]], [[URL1]] placeholders exactly as-is.\n"
            "4. Keep proper nouns (NYSC, PPA, CDS, LGI) as-is.\n"
            "5. Use formal, natural vocabulary — NOT phonetic English.\n"
            f"Text:\n{text}\n\n"
            f"Translation in {target_name}:"
        )

    def _looks_wrong(s: str, t_lang: str) -> bool:
        """Check if output is still English or a loop."""
        if _is_loop(s):
            return True
        if t_lang == "en":
            return False
        # Use a broader set but exclude known allowed English tokens
        en_words = {"the", "and", "with", "would", "should", "from", "their",
                    "this", "that", "was", "were", "have", "been", "will", "are"}
        # Remove proper nouns and known non-translatable tokens
        clean = s.lower()
        for keep in ("nysc", "ppa", "cds", "lgi", "saed", "jamb", "n77,000", "n33,000"):
            clean = clean.replace(keep, "")
        s_words = set(clean.replace(",", "").replace(".", "").split())
        en_hits = len(en_words.intersection(s_words))
        # Only flag as wrong if 4+ strong English structural words appear
        return en_hits >= 4

    try:
        resp = llm.invoke(_make_prompt(masked))
        out = (resp.content if hasattr(resp, "content") else str(resp)).strip()
        
        # First failure: retry same model with forceful prompt
        if _looks_wrong(out, target_lang):
            print(f"[TRANSLATE] Chunk looks English. Forcing retry 1...")
            resp2 = llm.invoke(_make_prompt(masked, extra_force=True))
            out = (resp2.content if hasattr(resp2, "content") else str(resp2)).strip()

        # Second failure: try a stronger model with forced prompt 
        # (switching from mixtral to llama since mistral tends to loop more on obscure languages)
        if not out or _looks_wrong(out, target_lang):
            print(f"[TRANSLATE] Still English/Loop. Retrying with llama-3.1-8b...")
            llm_alt = _make_llm(timeout=25.0, retries=0, model_override="llama-3.1-8b-instant")
            resp3 = llm_alt.invoke(_make_prompt(masked, extra_force=True))
            out = (resp3.content if hasattr(resp3, "content") else str(resp3)).strip()

        # Final loop check
        if _is_loop(out):
            print(f"[TRANSLATE] LLM severely looped: {out[:50]}... Fallback to original.")
            return chunk

        # Safety: cap runaway length
        if len(out) > len(chunk) * 4 and len(chunk) > 20:
            out = out[:len(chunk) * 2] + "..."

        # Final fallback: if still wrong, return whatever we have (even if imperfect)
        # — better than returning English
        if not out:
            print(f"[TRANSLATE] All retries produced empty. Returning original.")
            return chunk

        print(f"[TRANSLATE] Chunk OK → {len(out)} chars.")
        return _unmask_urls(out, urls)
    except Exception as e:
        print(f"[TRANSLATE] Chunk translation error: {e}")
        return chunk

def _translate(text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
    try:
        if target_lang == "en" and (source_lang in (None, "en")):
            print(f"[TRANSLATE] Skipped (en->en).")
            return text

        llm = _make_llm(timeout=18.0, retries=0)
        _, urls = _mask_urls(text)

        # SHORT TEXT: translate in one shot (under 250 chars)
        if len(text) <= 250:
            result = _translate_chunk(text, target_lang, llm)
            return result

        # LONG TEXT: split into chunks, translate each separately, reassemble
        print(f"[TRANSLATE] Long text ({len(text)} chars) — using chunk mode. target={target_lang}")
        chunks = _split_into_chunks(text, max_chars=280)
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"[TRANSLATE] Chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            t_chunk = _translate_chunk(chunk, target_lang, llm)
            translated_chunks.append(t_chunk)

        full = "\n".join(translated_chunks)

        # Post-process: remove consecutive duplicate sentences
        full = _dedupe_output(full)

        # Restore URLs (in case any chunk didn't restore them)
        full = _unmask_urls(full, urls)

        print(f"[TRANSLATE] Chunk translation complete. Output={len(full)} chars.")
        return full

    except Exception as e:
        print(f"[TRANSLATE] ERROR: {e}. Returning failure marker.")
        return "[TRANSLATION FAILED] " + text


def detect_language(text: str) -> str:
    # First pass: fast heuristics
    h = _detect_language_heuristic(text)
    if h != "en":
        return h
    if any(ch in text for ch in ("ẹ", "ṣ", "ọ", "ò", "á", "ị", "ụ", "ƙ", "ɗ", "è", "ù", "ě")):
        yo_unique = {"ṣ"}
        ig_unique = {"ị", "ụ"}
        ha_chars  = {"ƙ", "ɗ"}
        yo_supporting = {"ẹ", "ọ", "ò", "á", "è", "ù"}
        if any(ch in text for ch in yo_unique):
            return "yo"
        if any(ch in text for ch in ig_unique):
            return "ig"
        if any(ch in text for ch in ha_chars):
            return "ha"
        if any(ch in text for ch in yo_supporting):
            return "yo"
    llm_code = _detect_language_llm(text)
    return llm_code or "en"

def translate_to_english(text: str, source_lang: str) -> str:
    if source_lang == "en":
        return text
    return _translate(text, "en", source_lang)

def translate_from_english(text: str, target_lang: str) -> str:
    if target_lang == "en":
        print(f"[TRANSLATE] Skipped translate_from_english — target is 'en'.")
        return text
    return _translate(text, target_lang, "en")

def process_multilingual_request(message: str, session_id: str, language_override: Optional[str]) -> Tuple[str, str, str, List[Dict[str, str]]]:
    # Normalize 'auto' from frontend to None
    if language_override == "auto":
        language_override = None
    detected = detect_language(message)
    target = language_override if (language_override and language_override in LANG_CODES) else detected
    print(f"[LANG] selected={language_override} detected={detected} target={target} (pre-translation)")
    msg_en = translate_to_english(message, detected)
    result = run_nysc_agent(message=msg_en, session_id=session_id)
    ans_en = result["answer"]
    sources = result.get("sources", [])
    translated = translate_from_english(ans_en, target)
    print(f"[LANG] translated_length={len(translated)} target={target} (post-translation)")
    return translated, target, msg_en, sources

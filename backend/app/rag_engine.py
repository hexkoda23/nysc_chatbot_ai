import os
import json
import re
import httpx
import asyncio
from functools import lru_cache
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from collections import defaultdict
from datetime import datetime, timedelta

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


# Load .env from backend directory or project root
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)
load_dotenv()  # Also try current directory and parent directories


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CURSOR_PROMPT_PATH = os.path.join(PROJECT_ROOT, "NYSC_Cursor_Prompt.md")

def _load_external_prompt() -> str:
    try:
        if os.path.exists(CURSOR_PROMPT_PATH):
            with open(CURSOR_PROMPT_PATH, "r", encoding="utf-8") as f:
                txt = f.read().strip()
                return txt
    except Exception:
        pass
    return ""

LANGUAGE_TEMPLATES = {
    "en": {
        "officialSource": "Official Source",
        "followUpPrompt": "You may also want to ask:",
        "website": "NYSC Website",
        "portal": "NYSC Portal"
    },
    "yo": {
        "officialSource": "Orísun ìsọfúnni",
        "followUpPrompt": "Àwọn ìbéèrè míràn tí o lè béèrè:",
        "website": "Ìkànnì NYSC",
        "portal": "Ojúewé NYSC"
    },
    "ig": {
        "officialSource": "Isi mmalite ozi",
        "followUpPrompt": "Ajụjụ ndị ọzọ ị nwere ike jụọ:",
        "website": "Webụsaịtị NYSC",
        "portal": "Ọdụ NYSC"
    },
    "ha": {
        "officialSource": "Tushen bayanai",
        "followUpPrompt": "Sauran tambayoyin da zaka iya yi:",
        "website": "Gidan yanar gizon NYSC",
        "portal": "Shafin NYSC"
    }
}

# Official sources and search roots
NYSC_SOURCES = {
    "main": "https://www.nysc.gov.ng",
    "portal": "https://portal.nysc.org.ng",
    "faq": "https://www.nysc.gov.ng/faq",
    "mobilization": "https://www.nysc.gov.ng/mobilization",
    "redeployment": "https://www.nysc.gov.ng/redeployment",
    "allowance": "https://www.nysc.gov.ng/allowance",
    "senate_check": "https://portal.nysc.org.ng/nysc2/VerifySenateLists.aspx",
    "registration": "https://portal.nysc.org.ng/nysc1/",
    "exclusion": "https://portal.nysc.org.ng/nysc1/ExclusionLetter.aspx",
}

NYSC_SEARCH_URLS = [
    "https://www.nysc.gov.ng",
    "https://portal.nysc.org.ng",
]

# In-memory conversation history storage (session_id -> list of (user_msg, assistant_msg) tuples)
# Stores last 10 exchanges per session
CONVERSATION_HISTORY: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
MAX_HISTORY_LENGTH = 10  # Keep last 10 exchanges


def _normalize_text(t: str) -> str:
    repl = (
        ("\u00a0", " "),        # non-breaking space
        ("â–º", "•"),           # bullet artifact
        ("Â", ""),              # stray encoding
        ("â‚¦", "₦"),
        ("\r", " "),
    )
    for a, b in repl:
        t = t.replace(a, b)
    t = " ".join(t.split())
    return t.strip()


def _infer_topic_from_filename(name: str) -> Tuple[str, str]:
    n = name.lower()
    if "allowance" in n or "stipend" in n or "pay" in n:
        return "allowance", "policy"
    if "redeploy" in n or "relocat" in n or "transfer" in n:
        return "redeployment", "process"
    if "call_up" in n or "callup" in n or "call-up" in n or "call up" in n:
        return "call_up", "process"
    if "registration" in n or "register" in n or "enroll" in n:
        return "registration", "process"
    if "exemption" in n or "exempt" in n:
        return "exemption", "policy"
    if "decree" in n or "act" in n or "law" in n:
        return "decree", "policy"
    if "faq" in n or "frequently" in n:
        return "faq", "faq"
    if "posting" in n or "placement" in n or "ppa" in n:
        return "posting", "policy"
    if "saed" in n or "skill_acqui" in n or "entrepreneurship" in n:
        return "saed", "guide"
    if "cds" in n or "community_dev" in n:
        return "cds", "guide"
    return "general", "policy"


ALLOWED_FILES = {
    "call_up.md",
    "corrections.md",
    "decree.md",
    "faq.md",
    "posting.md",
    "redeployment.md",
    "registration.md",
    "safety.md",
    "nysc_allowance_2024.txt",
    "nysc_current_information_2024_2025.txt",
    "nysc_policy_on_sexual_harassment.txt",
    "nyscdecree.txt",
    "bye-law pfd_103222.txt",
}
def _is_low_quality(filename: str) -> bool:
    return filename.lower() not in ALLOWED_FILES


@lru_cache(maxsize=1)
def _load_corpus() -> List[Dict[str, Any]]:
    """
    Load and chunk documents from DATA_DIR into a simple corpus suitable for fast local retrieval.
    Avoids network-bound embeddings for speed and reliability.
    """
    docs: List[Any] = _load_documents()
    corpus: List[Dict[str, Any]] = []
    for d in docs:
        text = _normalize_text(d.page_content)
        if not text:
            continue
        corpus.append(
            {
                "text": text,
                "source": d.metadata.get("source", "unknown"),
                "topic": d.metadata.get("topic", "general"),
                "doc_type": d.metadata.get("document_type", "policy"),
            }
        )
    return corpus


def _simple_retrieve(query: str, k: int = 4) -> List[Dict[str, Any]]:
    """
    Very fast local retriever based on token overlap scoring.
    Good enough for small corpora and sub-5s responses without external services.
    """
    q = query.lower()
    q_tokens = set(t for t in q.replace("\n", " ").split() if len(t) > 2)
    if not q_tokens:
        return []

    scored: List[Tuple[float, Dict[str, Any]]] = []
    q_has_allowance = "allowance" in q or "stipend" in q
    intent_topic = _classify_intent(q)
    corpus = _load_corpus()
    for item in corpus:
        text_lower = item["text"].lower()
        text_tokens = set(t for t in text_lower.split() if len(t) > 2)
        if not text_tokens:
            continue
        overlap = len(q_tokens & text_tokens)
        if overlap == 0:
            continue
        score = overlap / (len(q_tokens) + 1e-6)
        if intent_topic and item.get("topic") == intent_topic:
            score += 0.5
        if q_has_allowance and "allowance" in text_lower:
            score += 0.8
        if q_has_allowance and ("monthly" in text_lower or "per month" in text_lower):
            score += 0.4
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    threshold = 0.25
    filtered = [it for it in scored if it[0] >= threshold]
    deduped: List[Tuple[float, Dict[str, Any]]] = []
    seen_topics = set()
    for sc, it in filtered:
        topic = it.get("topic") or "general"
        if topic in seen_topics:
            continue
        seen_topics.add(topic)
        deduped.append((sc, it))
        if len(deduped) >= 3:
            break
    if not deduped and filtered:
        deduped = filtered[:k]
    return [it for _, it in deduped]


def _web_search_nysc(query: str) -> str:
    serpapi_key = os.getenv("SERPAPI_KEY")
    if serpapi_key:
        try:
            params = {
                "q": f"site:nysc.gov.ng OR site:portal.nysc.org.ng {query}",
                "api_key": serpapi_key,
                "num": 5,
                "engine": "google",
            }
            resp = httpx.get("https://serpapi.com/search", params=params, timeout=8.0)
            data = resp.json()
            results = data.get("organic_results", [])
            if results:
                snippets = []
                for r in results[:4]:
                    title = r.get("title", "") or ""
                    snippet = r.get("snippet", "") or ""
                    link = r.get("link", "") or ""
                    snippets.append(f"{title}: {snippet} (source: {link})")
                return "\n".join(snippets)
        except Exception as e:
            print(f"[WEB SEARCH] SerpAPI failed: {e}")
    try:
        pages_to_try = [
            NYSC_SOURCES.get("faq", ""),
            NYSC_SOURCES.get("main", ""),
        ]
        for url in pages_to_try:
            if not url:
                continue
            try:
                r = httpx.get(url, timeout=6.0, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200 and r.text:
                    text = re.sub(r"<[^>]+>", " ", r.text)
                    text = re.sub(r"\s+", " ", text)
                    ql = query.lower().split()
                    anchor = ql[0] if ql else "nysc"
                    idx = text.lower().find(anchor)
                    if idx > 0:
                        return text[max(0, idx - 100) : idx + 1500]
                    return text[:2000]
            except Exception:
                continue
    except Exception as e:
        print(f"[WEB SEARCH] Direct fetch failed: {e}")
    return ""

def _classify_intent(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["allowance", "stipend", "pay", "salary"]):
        return "allowance"
    if any(w in q for w in ["redeploy", "redeployment", "relocate", "transfer"]):
        return "redeployment"
    if any(w in q for w in ["who owns", "ownership", "established by", "founded by", "who created", "who started"]):
        return "decree"
    if any("serve in" in q or "posting" in q or "state of origin" in q for _ in [0]):
        return "posting"
    if any(w in q for w in ["register", "registration", "enroll", "apply"]):
        return "registration"
    if "call-up" in q or "call up" in q or "callup" in q:
        return "call_up"
    if "exemption" in q or "exempt" in q:
        return "exemption"
    if "decree" in q or "act" in q or "law" in q:
        return "decree"
    if any(w in q for w in ["saed", "skill", "skill acquisition", "entrepreneurship", "craft", "trade", "vocational", "learn skill"]):
        return "saed"
    if any(w in q for w in ["cds", "community development", "community service", "cds group", "secondary assignment", "group to join"]):
        return "cds"
    return ""

def _extractive_answer(query: str, docs: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    if not docs:
        return None
    q = query.lower()
    q_tokens = set(t for t in q.replace("\n", " ").split() if len(t) > 2)
    if not q_tokens:
        return None
    bigrams = set()
    q_words = [w for w in q.replace("\n", " ").split() if len(w) > 2]
    for i in range(len(q_words) - 1):
        bigrams.add(q_words[i] + " " + q_words[i + 1])
    candidates: List[Tuple[float, str, str]] = []
    is_allowance_q = ("allowance" in q) or ("stipend" in q) or ("how" in q and "much" in q)
    # currency/amount patterns
    import re
    amount_pat = re.compile(r"(₦\s?\d[\d,\.]*|\bN\s?\d[\d,\.]*\b|\bNGN\s?\d[\d,\.]*\b|\b\d[\d,\.]*\s?naira\b)", re.IGNORECASE)
    sep_pat = re.compile(r"\.\s+")
    def _header_like(s: str) -> bool:
        if "====" in s or "----" in s or "____" in s:
            return True
        letters = [ch for ch in s if ch.isalpha()]
        if letters:
            if sum(1 for ch in letters if ch.isupper()) / max(1, len(letters)) > 0.6 and len(s) > 6:
                return True
        if s.strip().endswith(":"):
            return True
        return False
    for d in docs:
        src = d.get("source", "unknown")
        text = d.get("text") or d.get("page_content") or ""
        text = _normalize_text(text)
        # paragraph-wise splitting then sentence-level
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        parts: List[str] = []
        for para in paragraphs:
            parts.extend([s.strip() for s in sep_pat.split(para) if s.strip()])
        for sent in parts:
            # Skip question headers unless they contain an amount and allowance keyword
            sent_stripped = sent.strip()
            if _header_like(sent_stripped):
                continue
            tokens = set(t for t in sent.lower().split() if len(t) > 2)
            if not tokens:
                continue
            overlap = len(tokens & q_tokens)
            if overlap == 0:
                continue
            score = overlap / (len(q_tokens) + 1e-6)
            s_lower = " ".join(sent.lower().split())
            for bg in bigrams:
                if bg in s_lower:
                    score += 0.5
            if is_allowance_q:
                has_allow = ("allowance" in s_lower) or ("stipend" in s_lower)
                has_currency = bool(amount_pat.search(s_lower))
                if has_allow and has_currency:
                    score += 1.2
                if "per month" in s_lower or "monthly" in s_lower:
                    score += 0.6
                # If it's clearly a Q header and lacks amount, downweight heavily
                if (sent_stripped.lower().startswith("q:") or sent_stripped.lower().startswith("question")) and not has_currency:
                    score -= 1.0
                # If sentence lacks 'allowance' for an allowance query, downweight
                if not has_allow:
                    score -= 0.8
                # Require a currency amount for allowance queries
                if not has_currency:
                    continue
            candidates.append((score, sent_stripped, src))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    grouped: Dict[str, List[Tuple[float, str]]] = {}
    for sc, st, sr in candidates:
        grouped.setdefault(sr, []).append((sc, st))
    for arr in grouped.values():
        arr.sort(key=lambda x: x[0], reverse=True)
    ordered = sorted(grouped.items(), key=lambda kv: kv[1][0][0], reverse=True)
    selected: List[Tuple[str, str]] = []
    for src, arr in ordered:
        for _, st in arr[:2]:
            selected.append((st, src))
            if len(selected) >= 3:
                break
        if len(selected) >= 3:
            break
    # For allowance questions, enforce first sentence includes an amount
    if is_allowance_q and selected:
        if not amount_pat.search(selected[0][0].lower()):
            for idx, (st, src) in enumerate(selected):
                if amount_pat.search(st.lower()):
                    # Move this sentence to front
                    selected.insert(0, selected.pop(idx))
                    break
    if not selected:
        return None
    direct = selected[0][0]
    bullets = [s for s, _ in selected[1:]]
    # Remove any asterisks from extracted text (no markdown emphasis)
    direct = direct.replace("*", "").strip()
    bullets = [b.replace("*", "").strip() for b in bullets]
    parts: List[str] = [direct]
    # Add up to 3 numbered details, each on its own line
    if bullets:
        parts.append("")
        for i, b in enumerate(bullets[:3], start=1):
            parts.append(f"{i}. {b}")
    # Optional follow-up suggestions based on intent (also numbered)
    intent = _classify_intent(query)
    suggestions: List[str] = []
    if intent == "allowance":
        suggestions = [
            "Do you want details about when allowances are paid?",
            "Need clarification on eligibility for monthly payments?",
        ]
    elif intent == "redeployment":
        suggestions = [
            "Would you like the steps and required documents for redeployment?",
            "Need to know valid reasons accepted by NYSC?",
        ]
    elif intent == "posting":
        suggestions = [
            "Do you want guidance on changing your PPA?",
            "Need clarification on posting outside state of origin?",
        ]
    elif intent == "registration":
        suggestions = [
            "Do you want the camp registration document checklist?",
            "Need timelines for call-up and mobilization?",
        ]
    if suggestions:
        parts.append("")
        parts.append("You may also ask:")
        for i, s in enumerate(suggestions[:3], start=1):
            parts.append(f"{i}. {s}")
    # Append official links section in plain text
    parts.append("")
    parts.append("Official Source:")
    parts.append("NYSC Official Website – https://www.nysc.gov.ng")
    parts.append("NYSC Portal – https://portal.nysc.gov.ng")
    answer = "\n".join(parts).strip()
    sources = [{"source": src, "snippet": s[:200]} for s, src in selected]
    return {"answer": answer, "sources": sources}


def _load_documents() -> List[Any]:
    """Load NYSC-related documents (TXT, markdown) from the local data directory."""
    if not os.path.isdir(DATA_DIR):
        return []

    docs: List[Any] = []

    # Walk the data directory and load .md and .txt files explicitly
    from langchain_community.document_loaders import TextLoader
    for root, _, files in os.walk(DATA_DIR):
        for filename in files:
            path = os.path.join(root, filename)
            lower = filename.lower()
            try:
                if _is_low_quality(lower):
                    continue
                if lower.endswith(".md"):
                    loader = TextLoader(path, encoding="utf-8", autodetect_encoding=True)
                    docs.extend(loader.load())
                elif lower.endswith(".txt"):
                    loader = TextLoader(path, encoding="utf-8", autodetect_encoding=True)
                    docs.extend(loader.load())
            except Exception:
                # If a single file fails to load, skip it but continue with others
                continue

    if not docs:
        return []

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n#", "\n\n", "\n", ". "],
    )
    split_docs = splitter.split_documents(docs)

    # Ensure each doc has a simple source field
    for d in split_docs:
        src = d.metadata.get("source") or d.metadata.get("file_path") or "local_nysc_docs"
        base = os.path.basename(src)
        d.metadata["source"] = base
        topic, doc_type = _infer_topic_from_filename(base)
        d.metadata["topic"] = topic
        d.metadata["document_type"] = doc_type
    return split_docs


@lru_cache(maxsize=1)
def get_vector_store():
    """Create (or retrieve cached) in-memory vector store from NYSC documents."""
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import DocArrayInMemorySearch
    docs = _load_documents()
    if not docs:
        # Create an empty store to avoid crashes; retrieval will just return no docs.
        return DocArrayInMemorySearch.from_texts(
            ["No NYSC documents loaded yet."],
            embedding=OpenAIEmbeddings(),
            metadatas=[{"source": "system"}],
        )

    embeddings = OpenAIEmbeddings()
    store = DocArrayInMemorySearch.from_documents(docs, embeddings)
    print(f"Loaded {len(docs)} document chunks into vector store")
    return store


@tool
def search_local_docs(query: str) -> str:
    """
    Search the local NYSC document database for policy information, procedures,
    registration steps, allowances, redeployment rules, camp info, and guidelines.
    Always call this first for any NYSC question.
    """
    top = _simple_retrieve(query, k=4)
    if not top:
        return "No relevant documents found in local database."
    results = []
    for i, doc in enumerate(top, 1):
        results.append(f"[Source {i}: {doc['source']}]\n{doc['text'][:600]}")
    return "\n\n".join(results)


@tool
def search_nysc_online(query: str) -> str:
    """
    Search live NYSC official websites for current, time-sensitive information:
    current allowance, batch dates, recent policy changes, and portal steps.
    Always call this after search_local_docs.
    """
    web_result = _web_search_nysc(query)
    if web_result:
        return "[Live NYSC Web Data]\n" + web_result
    return "Could not fetch live data. Visit https://www.nysc.gov.ng or https://portal.nysc.org.ng"


@tool
def get_nysc_portal_links(topic: str) -> str:
    """
    Return official NYSC portal URLs for a given topic. Topics include:
    registration, senate_check, redeployment, allowance, exclusion, mobilization, faq.
    Always include main and portal links.
    """
    topic_lower = (topic or "").lower()
    links: List[str] = []
    if any(w in topic_lower for w in ["register", "registration", "sign up", "create"]):
        links.append(f"Registration Portal: {NYSC_SOURCES['registration']}")
    if any(w in topic_lower for w in ["senate", "list", "verify", "check", "name"]):
        links.append(f"Senate List Verification: {NYSC_SOURCES['senate_check']}")
    if any(w in topic_lower for w in ["redeploy", "relocat", "transfer", "move"]):
        links.append(f"Redeployment Info: {NYSC_SOURCES['redeployment']}")
    if any(w in topic_lower for w in ["exempt", "exclusion", "exclude", "above 30"]):
        links.append(f"Exclusion Letter: {NYSC_SOURCES['exclusion']}")
    if any(w in topic_lower for w in ["allowance", "stipend", "pay", "salary", "money"]):
        links.append(f"Allowance Info: {NYSC_SOURCES['allowance']}")
    if any(w in topic_lower for w in ["faq", "question", "help"]):
        links.append(f"NYSC FAQ: {NYSC_SOURCES['faq']}")
    links.append(f"NYSC Main Website: {NYSC_SOURCES['main']}")
    links.append(f"NYSC Portal: {NYSC_SOURCES['portal']}")
    return "\n".join(links)


_llm_cache: Dict[Tuple[float, int, str | None], Any] = {}
def _make_llm(timeout: float = 10.0, retries: int = 2, model_override: str | None = None):
    """
    Create a Chat LLM. If NYSC (Groq) key is present, use Groq OpenAI-compatible API.
    Otherwise use default OpenAI.
    """
    from langchain_openai import ChatOpenAI
    groq_key = os.getenv("NYSC")
    
    # Use explicit override, then Groq model env, then OpenAI model env, then defaults
    if groq_key:
        model = model_override or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        base_url = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1")
    else:
        model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        base_url = None # Use default OpenAI base

    cache_key = (timeout, retries, model, base_url)
    if cache_key in _llm_cache:
        return _llm_cache[cache_key]

    common_params = {
        "model": model,
        "temperature": 0.4,
        "frequency_penalty": 0.8,
        "presence_penalty": 0.3,
        "max_tokens": 1000,
        "timeout": timeout,
        "max_retries": retries,
    }

    if groq_key:
        common_params["api_key"] = groq_key
        common_params["base_url"] = base_url
    
    llm = ChatOpenAI(**common_params)
    _llm_cache[cache_key] = llm
    return llm


def get_agent(target_lang: str = "en"):
    if not (os.getenv("NYSC") or os.getenv("OPENAI_API_KEY")):
        raise RuntimeError("Set NYSC (Groq) or OPENAI_API_KEY in .env")
    llm = _make_llm(timeout=25.0, retries=1)
    tools = [search_local_docs, search_nysc_online, get_nysc_portal_links]
    
    lang_names = {"yo": "Standard Yorùbá", "ha": "Hausa", "ig": "Igbo", "en": "English"}
    lang_name = lang_names.get(target_lang, "English")
    
    # Load exact target language strings to prevent LLM translation hallucination
    t_strings = LANGUAGE_TEMPLATES.get(target_lang, LANGUAGE_TEMPLATES["en"])
    official_source_txt = t_strings["officialSource"]
    follow_up_txt = t_strings["followUpPrompt"]
    website_txt = t_strings["website"]
    portal_txt = t_strings["portal"]
    
    if target_lang != "en":
        lang_instruction = (
            f"IMPORTANT LANGUAGE INSTRUCTION:\n"
            f"You MUST write your ENTIRE response natively in {lang_name}. "
            f"Do NOT write any part of your answer in English. "
            f"Use EXACTLY these native phrases for the footer sections:\n"
            f"- For Official Source, use: '{official_source_txt}'\n"
            f"- For Follow-up questions, use: '{follow_up_txt}'\n"
            f"- For Website/Portal names, use: '{website_txt}' and '{portal_txt}'"
        )
    else:
        lang_instruction = ""

    system_prompt = (
        f"You are NYSC AI — a fast, accurate assistant for the Nigerian National Youth Service Corps. "
        f"You are speaking to the user in {lang_name}.\n\n"
        "You have THREE tools available.\n\n"
        "YOUR BEHAVIOR FOR EVERY QUESTION:\n"
        "1. ALWAYS call search_local_docs first to check the local database\n"
        "2. ALWAYS call search_nysc_online second to get current live data\n"
        "3. Call get_nysc_portal_links to attach the right official URL\n"
        "4. Merge ALL results and write a clean final answer\n\n"
        "ANSWER FORMAT — always follow this structure:\n"
        "[Direct answer in 1-2 sentences]\n\n"
        "[Numbered steps or key details if needed]\n"
        "1. ...\n2. ...\n3. ...\n\n"
        "[Official Links section]\n"
        f"{official_source_txt}:\n"
        f"- [Relevant specific link from get_nysc_portal_links]\n"
        f"- {website_txt}: https://www.nysc.gov.ng\n"
        f"- {portal_txt}: https://portal.nysc.org.ng\n\n"
        f"{follow_up_txt}\n"
        "1. [Relevant follow-up question]\n"
        "2. [Relevant follow-up question]\n\n"
        f"{lang_instruction}\n\n"
        "STRICT RULES:\n"
        "- Answer ONLY the Current Question. Do NOT summarize or repeat previous history.\n"
        "- DO NOT repeat yourself or any word multiple times. If you see a loop, stop the sentence immediately.\n"
        f"- Write in professional, formal {lang_name}. Do NOT use informal slang like 'Omo', 'wàhálà', or 'koko' in Yorùbá.\n"
        "- Each point in a numbered list MUST provide NEW information. Do NOT repeat the same fact in different points.\n"
        "- Give SPECIFIC information: exact amounts, exact URLs, exact steps.\n"
        "- Current allowance is N77,000/month (effective March 2025).\n"
        "- Registration portal: https://portal.nysc.org.ng/nysc1/\n"
        "- Never say \"I cannot find\" if tools returned results — synthesize them professionally."
    )
    external = _load_external_prompt()
    if external:
        system_prompt = external + "\n\n" + system_prompt
    graph = create_react_agent(llm, tools, state_modifier=system_prompt)
    return graph


def _get_conversation_context(session_id: str) -> str:
    """Get recent conversation history as context string."""
    history = CONVERSATION_HISTORY.get(session_id, [])
    if not history:
        return ""
    
    context_parts = []
    for user_msg, assistant_msg in history[-5:]:  # Last 5 exchanges
        context_parts.append(f"User: {user_msg}")
        context_parts.append(f"Assistant: {assistant_msg}")
    
    return "\n".join(context_parts)


def _update_conversation_history(session_id: str, user_message: str, assistant_message: str):
    """Update conversation history for a session."""
    history = CONVERSATION_HISTORY[session_id]
    history.append((user_message, assistant_message))
    
    # Keep only last MAX_HISTORY_LENGTH exchanges
    if len(history) > MAX_HISTORY_LENGTH:
        CONVERSATION_HISTORY[session_id] = history[-MAX_HISTORY_LENGTH:]


def run_nysc_agent(message: str, session_id: str, target_lang: str = "en") -> Dict[str, Any]:
    template = _get_template_response(message)
    if template:
        _update_conversation_history(session_id, message, template["answer"])
        return template
    conversation_context = _get_conversation_context(session_id)
    full_message = message
    if conversation_context:
        full_message = f"Previous conversation:\n{conversation_context}\n\nCurrent question: {message}"
    def _run_agent():
        agent = get_agent(target_lang=target_lang)
        result = agent.invoke({"messages": [HumanMessage(content=full_message)]})
        msgs = result.get("messages", [])
        for msg in reversed(msgs):
            if hasattr(msg, "content") and msg.content:
                if not getattr(msg, "tool_calls", None):
                    return msg.content
        return "I was unable to generate a response. Please try again."
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_run_agent)
    try:
        answer = future.result(timeout=28.0)
        sources = []
        url_pattern = re.compile(r'https?://[^\s\)]+')
        urls = url_pattern.findall(answer)
        for url in set(urls[:3]):
            sources.append({"source": url, "snippet": ""})
        result = {"answer": answer, "sources": sources}
        _update_conversation_history(session_id, message, answer)
        return result
    except FutureTimeoutError:
        executor.shutdown(wait=False)
        print("[WARN] Agent timed out — using fast RAG fallback")
        fallback = _fast_rag_response(message, conversation_context, target_lang=target_lang)
        _update_conversation_history(session_id, message, fallback["answer"])
        return fallback
    except Exception:
        executor.shutdown(wait=False)
        import traceback
        traceback.print_exc()
        fallback = _fast_rag_response(message, conversation_context, target_lang=target_lang)
        _update_conversation_history(session_id, message, fallback["answer"])
        return fallback
    finally:
        executor.shutdown(wait=False)


def _fast_rag_response(message: str, conversation_context: str = "", target_lang: str = "en") -> Dict[str, Any]:
    """
    Fast RAG response using direct retrieval + LLM with conversation context.
    """
    lang_names = {"yo": "Standard Yorùbá", "ha": "Hausa", "ig": "Igbo", "en": "English"}
    lang_name = lang_names.get(target_lang, "English")
    t_strings = LANGUAGE_TEMPLATES.get(target_lang, LANGUAGE_TEMPLATES["en"])
    official_source_txt = t_strings["officialSource"]
    follow_up_txt = t_strings["followUpPrompt"]
    website_txt = t_strings["website"]
    portal_txt = t_strings["portal"]

    # Build a language instruction for the follow-up suggestions
    if target_lang != "en":
        lang_instruction = (
            f"IMPORTANT: You MUST write your ENTIRE response natively in {lang_name}. "
            f"Do NOT write any part of your answer in English. "
            f"Use EXACTLY these native phrases for the footer sections:\n"
            f"- '{official_source_txt}'\n"
            f"- '{follow_up_txt}'"
        )
    else:
        lang_instruction = ""

    docs_raw = _simple_retrieve(message, k=4)
    if docs_raw:
        local_context = "\n\n".join([d["text"][:300] for d in docs_raw[:2]])
        sources_list = [{"source": d["source"], "snippet": d["text"][:200]} for d in docs_raw[:2]]
    else:
        local_context = ""
        sources_list = []
    web_context = _web_search_nysc(message)
    SYSTEM_RULES = (
        "You are NYSC AI — a knowledgeable assistant for the Nigerian National Youth Service Corps (NYSC).\n\n"
        "STRICT RULES:\n"
        "1. Answer ONLY the User question at bottom. Do NOT summarize previous history.\n"
        "2. Use provided context. If not found, say: 'I don't have specific info. Visit `https://www.nysc.gov.ng`'.\n"
        "3. DO NOT repeat yourself. If a loop occurs, break it and move to the next part.\n"
        f"4. Write in formal, professional {lang_name}. No informal slang like 'Omo', 'wàhálà', or 'koko'.\n"
        "5. Numbered details MUST be unique. Do NOT repeat the same information across bullets.\n"
        "6. Structure: direct answer, unique numbered details, official source line.\n"
        "7. No markdown asterisks, no ALL CAPS.\n"
        f"7. After answer, write '{follow_up_txt}' with 2 unique relevant questions.\n"
        f"   {lang_instruction}\n"
        "8. End with:\n"
        f"   {official_source_txt}: {website_txt} – `https://www.nysc.gov.ng`  | {portal_txt} – `https://portal.nysc.gov.ng`\n\n"
        "CRITICAL FACTS:\n"
        "- NYSC monthly allowance is N77,000 per month (effective March 2025).\n"
        "- This replaced the previous N33,000 allowance.\n"
        "- Registration portal: https://portal.nysc.org.ng/nysc1/\n"
    )
    ext_rules = _load_external_prompt()
    if ext_rules:
        SYSTEM_RULES = ext_rules + "\n\n" + SYSTEM_RULES
    if conversation_context:
        prompt = (
            f"{SYSTEM_RULES}\n\n"
            f"=== RECENT CONVERSATION ===\n{conversation_context}\n=== END CONVERSATION ===\n\n"
            f"=== LOCAL CONTEXT ===\n{local_context}\n=== END LOCAL CONTEXT ===\n\n"
            f"=== LIVE WEB CONTEXT ===\n{web_context[:1200]}\n=== END WEB CONTEXT ===\n\n"
            f"User question: {message}\n\n"
            f"Answer:"
        )
    else:
        prompt = (
            f"{SYSTEM_RULES}\n\n"
            f"=== LOCAL CONTEXT ===\n{local_context}\n=== END LOCAL CONTEXT ===\n\n"
            f"=== LIVE WEB CONTEXT ===\n{web_context[:1200]}\n=== END WEB CONTEXT ===\n\n"
            f"User question: {message}\n\n"
            f"Answer:"
        )
    try:
        llm = _make_llm(timeout=20.0, retries=0)
        # Use simple string prompt for direct LLM call
        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        return {"answer": answer, "sources": sources_list}
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"ERROR in _fast_rag_response ({error_type}): {error_msg}")
        traceback.print_exc()
        if "decommissioned" in error_msg.lower() or ("model" in error_msg.lower() and "not" in error_msg.lower()):
            try:
                for alt in ["llama-3.1-8b-instant", "mixtral-8x7b-32768"]:
                    try:
                        llm_alt = _make_llm(timeout=20.0, retries=0, model_override=alt)
                        resp = llm_alt.invoke(prompt)
                        ans = resp.content if hasattr(resp, "content") else str(resp)
                        return {"answer": ans, "sources": sources_list}
                    except Exception:
                        continue
            except Exception:
                pass
        if "401" in error_msg or "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
            return {"answer": "Authentication failed. Check that NYSC (Groq key) or OPENAI_API_KEY is correct in your .env file.", "sources": []}
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            return {"answer": "The AI service is rate-limited. Please wait a moment and try again.", "sources": []}
        if "connection" in error_msg.lower() or "connect" in error_msg.lower() or "network" in error_msg.lower():
            if docs_raw:
                joined = " ".join([t['text'][:300] for t in docs_raw])
                return {"answer": "From NYSC documents: " + joined, "sources": sources_list}
            tmpl = _get_template_response(message)
            if tmpl:
                return tmpl
            return {"answer": "There was a network connection issue. Please try again shortly.", "sources": []}
        if "timeout" in error_msg.lower():
            if docs_raw:
                joined = " ".join([t['text'][:300] for t in docs_raw])
                return {"answer": "From NYSC documents: " + joined, "sources": sources_list}
            tmpl = _get_template_response(message)
            if tmpl:
                return tmpl
            return {"answer": "The request timed out. Please try a simpler question.", "sources": []}
        if "api" in error_msg.lower() or "openai" in error_msg.lower():
            return {"answer": "There was an issue connecting to the AI service. Please check if OPENAI_API_KEY is set correctly in the .env file.", "sources": []}
        return {"answer": f"I encountered an issue processing your question: {error_msg[:100]}. Please try rephrasing your question.", "sources": []}


def _get_template_response(message: str) -> Dict[str, Any]:
    message_lower = message.lower()
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
    if message_lower.strip() in greetings or any(message_lower.startswith(g + " ") for g in greetings):
        return {
            "answer": "Hello! I’m NYSC AI. How can I help today? I can assist with allowances, redeployment, registration and camp questions based on official NYSC documents.",
            "sources": [],
        }
    return None


def _fast_fallback_response(message: str, conversation_context: str = "") -> Dict[str, Any]:
    """
    Fast fallback when timeout occurs - try template first, then minimal retrieval.
    """
    # Try template-based response first (fastest)
    template_response = _get_template_response(message)
    if template_response:
        print("Using template response for common question")
        return template_response
    
    try:
        # Minimal retrieval using local corpus (no external embeddings)
        docs_raw = _simple_retrieve(message, k=4)
        if not docs_raw:
            return {
                "answer": "I couldn't find relevant information. Please try rephrasing your question.",
                "sources": [],
            }
        # Try extractive answer first for speed
        extractive = _extractive_answer(message, docs_raw)
        if extractive:
            return extractive
        # If needed, do a short LLM pass with local context only
        docs = [{"page_content": d["text"], "metadata": {"source": d["source"]}} for d in docs_raw]
        context = "\n\n".join([d["page_content"][:300] for d in docs])
        sources_list = [{"source": d["metadata"].get("source", "unknown"), "snippet": d["page_content"][:200]} for d in docs]
        system_rules = (
            "You are NYSC AI — a helpful and professional assistant focused strictly on NYSC information.\n"
            "Rules:\n"
            "- Use ONLY the provided context; if not found, reply exactly: \"I cannot find this information in official NYSC documents.\" \n"
            "- Start with a clear, direct answer in 1–3 sentences.\n"
            "- Do NOT copy raw document formatting or headers; avoid \"====\" and similar.\n"
            "- Do NOT use all caps; summarize naturally in short paragraphs.\n"
            "- Do NOT use markdown emphasis, asterisks, or decorative characters; write plain text.\n"
            "- Use clean lists with numbering (1., 2., 3.), each item on its own line when helpful.\n"
            "- When relevant, add an 'Official Source:' section at the end with:\n"
            "  NYSC Official Website – https://www.nysc.gov.ng\n"
            "  NYSC Portal – https://portal.nysc.gov.ng\n"
            "- After answering, you may offer 2–3 brief, helpful follow-up suggestions.\n"
            "- Never paste entire documents; if information is unclear, say so without guessing.\n"
            "- If the answer would be longer than ~6 lines, give a short summary first, then offer more details.\n"
        )
        ext_rules2 = _load_external_prompt()
        if ext_rules2:
            system_rules = ext_rules2 + "\n\n" + system_rules
        prompt = f"""{system_rules}

{context}

Q: {message}
A:"""
        llm = _make_llm(timeout=8.0, retries=0)
        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        return {"answer": answer, "sources": sources_list}
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"ERROR in _fast_fallback_response: {error_msg}")
        traceback.print_exc()
        
        # If even fallback fails, try template one more time
        template_response = _get_template_response(message)
        if template_response:
            return template_response
        
        if "timeout" in error_msg.lower():
            return {
                "answer": "I'm experiencing connection issues with the AI service. Here's information compiled directly from NYSC documents.",
                "sources": [],
            }
        
        return {
            "answer": f"I encountered an issue: {error_msg[:100]}. Please try rephrasing your question or check the backend logs.",
            "sources": [],
        }

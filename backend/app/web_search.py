from __future__ import annotations

import html as html_lib
import base64
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse
from xml.etree import ElementTree

import httpx


OFFICIAL_DOMAINS = ("nysc.gov.ng", "portal.nysc.org.ng")


@dataclass(frozen=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str
    source: str
    score: float


def web_search_enabled() -> bool:
    return os.getenv("WEB_SEARCH_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def web_search_timeout() -> float:
    try:
        return max(1.0, min(12.0, float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "5"))))
    except ValueError:
        return 5.0


def web_search_result_count(default: int = 5) -> int:
    try:
        return max(1, min(8, int(os.getenv("WEB_SEARCH_RESULTS", str(default)))))
    except ValueError:
        return default


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html_lib.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def decode_duckduckgo_url(url: str) -> str:
    url = html_lib.unescape(url)
    if url.startswith("//"):
        url = f"https:{url}"
    parsed = urlparse(url)
    if parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return unquote(target)
    return url


def decode_bing_url(url: str) -> str:
    url = html_lib.unescape(url)
    if url.startswith("//"):
        url = f"https:{url}"
    parsed = urlparse(url)
    if "bing.com" not in parsed.netloc.lower() or not parsed.path.startswith("/ck/"):
        return url
    raw = parse_qs(parsed.query).get("u", [""])[0]
    if not raw:
        return url
    if raw.startswith("a1"):
        raw = raw[2:]
    try:
        padded = raw + ("=" * (-len(raw) % 4))
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="ignore")
        return decoded if decoded.startswith(("http://", "https://")) else url
    except Exception:
        return url


def source_name(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return host or "web"


def is_official_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == domain or host.endswith(f".{domain}") for domain in OFFICIAL_DOMAINS)


def is_relevant_result(query: str, result: WebSearchResult) -> bool:
    query_lower = query.lower()
    haystack = " ".join([result.title, result.snippet, result.url, result.source]).lower()
    if "nysc" in query_lower and "nysc" not in haystack and not is_official_url(result.url):
        return False
    if "allowance" in query_lower and not any(term in haystack for term in ("allowance", "allawee", "stipend", "nysc.gov.ng")):
        return False
    return True


def filter_relevant_results(query: str, results: List[WebSearchResult]) -> List[WebSearchResult]:
    return [result for result in results if is_relevant_result(query, result)]


def add_result(
    results: List[WebSearchResult],
    *,
    title: str,
    url: str,
    snippet: str,
    rank: int,
) -> None:
    title = clean_html(title)
    snippet = clean_html(snippet)
    url = decode_bing_url(decode_duckduckgo_url(url)).strip()
    if not title or not url.startswith(("http://", "https://")):
        return
    if any(existing.url == url for existing in results):
        return
    score = max(0.1, 1.0 - (rank * 0.08))
    if is_official_url(url):
        score += 0.35
    results.append(WebSearchResult(title=title, url=url, snippet=snippet, source=source_name(url), score=score))


def serpapi_search(query: str, max_results: int) -> List[WebSearchResult]:
    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        return []

    params: Dict[str, Any] = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": max_results,
        "hl": "en",
        "gl": "ng",
    }
    results: List[WebSearchResult] = []
    with httpx.Client(timeout=web_search_timeout(), follow_redirects=True) as client:
        response = client.get("https://serpapi.com/search.json", params=params)
        response.raise_for_status()
        data = response.json()

    answer_box = data.get("answer_box") or {}
    if isinstance(answer_box, dict):
        title = str(answer_box.get("title") or answer_box.get("answer") or "")
        link = str(answer_box.get("link") or answer_box.get("displayed_link") or "")
        snippet = str(answer_box.get("snippet") or answer_box.get("answer") or "")
        add_result(results, title=title, url=link, snippet=snippet, rank=0)

    for rank, item in enumerate(data.get("organic_results") or [], start=1):
        if len(results) >= max_results:
            break
        if not isinstance(item, dict):
            continue
        add_result(
            results,
            title=str(item.get("title") or ""),
            url=str(item.get("link") or ""),
            snippet=str(item.get("snippet") or ""),
            rank=rank,
        )

    local_results = data.get("local_results") or {}
    for rank, item in enumerate(local_results.get("places") or [], start=len(results) + 1):
        if len(results) >= max_results:
            break
        if not isinstance(item, dict):
            continue
        add_result(
            results,
            title=str(item.get("title") or item.get("name") or ""),
            url=str(item.get("website") or item.get("link") or ""),
            snippet=str(item.get("address") or item.get("description") or ""),
            rank=rank,
        )

    return results[:max_results]


def duckduckgo_html_search(query: str, max_results: int) -> List[WebSearchResult]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NYSCChatbot/1.0; +https://www.nysc.gov.ng)",
    }
    with httpx.Client(timeout=web_search_timeout(), follow_redirects=True, headers=headers) as client:
        response = client.get("https://duckduckgo.com/html/", params={"q": query})
        response.raise_for_status()
        html_text = response.text

    results: List[WebSearchResult] = []
    link_pattern = re.compile(r'<a\b(?=[^>]*\bresult__a\b)([^>]*)>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    href_pattern = re.compile(r'href="([^"]+)"', re.IGNORECASE)
    snippet_pattern = re.compile(
        r'<(?:a|div)[^>]+class="[^"]*\bresult__snippet\b[^"]*"[^>]*>(.*?)</(?:a|div)>',
        re.IGNORECASE | re.DOTALL,
    )

    for rank, match in enumerate(link_pattern.finditer(html_text), start=1):
        if len(results) >= max_results:
            break
        href_match = href_pattern.search(match.group(1))
        if not href_match:
            continue
        snippet_match = snippet_pattern.search(html_text, match.end(), match.end() + 2500)
        add_result(
            results,
            title=match.group(2),
            url=href_match.group(1),
            snippet=snippet_match.group(1) if snippet_match else "",
            rank=rank,
        )
    return results[:max_results]


def bing_html_search(query: str, max_results: int) -> List[WebSearchResult]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NYSCChatbot/1.0; +https://www.nysc.gov.ng)",
    }
    with httpx.Client(timeout=web_search_timeout(), follow_redirects=True, headers=headers) as client:
        response = client.get("https://www.bing.com/search", params={"q": query, "cc": "ng"})
        response.raise_for_status()
        html_text = response.text

    results: List[WebSearchResult] = []
    blocks = re.findall(r'<li class="b_algo"[^>]*>.*?</li>', html_text, re.IGNORECASE | re.DOTALL)
    title_pattern = re.compile(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    snippet_pattern = re.compile(r'<p[^>]*>(.*?)</p>', re.IGNORECASE | re.DOTALL)
    for rank, block in enumerate(blocks, start=1):
        if len(results) >= max_results:
            break
        title_match = title_pattern.search(block)
        if not title_match:
            continue
        snippet_match = snippet_pattern.search(block)
        add_result(
            results,
            title=title_match.group(2),
            url=title_match.group(1),
            snippet=snippet_match.group(1) if snippet_match else "",
            rank=rank,
        )
    return results[:max_results]


def bing_rss_search(query: str, max_results: int) -> List[WebSearchResult]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NYSCChatbot/1.0; +https://www.nysc.gov.ng)",
    }
    with httpx.Client(timeout=web_search_timeout(), follow_redirects=True, headers=headers) as client:
        response = client.get("https://www.bing.com/search", params={"q": query, "format": "rss", "cc": "ng"})
        response.raise_for_status()
        xml_text = response.text

    results: List[WebSearchResult] = []
    root = ElementTree.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []
    for rank, item in enumerate(channel.findall("item"), start=1):
        if len(results) >= max_results:
            break
        add_result(
            results,
            title=item.findtext("title") or "",
            url=item.findtext("link") or "",
            snippet=item.findtext("description") or "",
            rank=rank,
        )
    return results[:max_results]


def duckduckgo_instant_search(query: str, max_results: int) -> List[WebSearchResult]:
    with httpx.Client(timeout=web_search_timeout(), follow_redirects=True) as client:
        response = client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
        )
        response.raise_for_status()
        data = response.json()

    results: List[WebSearchResult] = []
    if data.get("AbstractText") and data.get("AbstractURL"):
        add_result(
            results,
            title=str(data.get("Heading") or "DuckDuckGo result"),
            url=str(data.get("AbstractURL") or ""),
            snippet=str(data.get("AbstractText") or ""),
            rank=1,
        )

    for item in data.get("RelatedTopics") or []:
        if len(results) >= max_results:
            break
        if not isinstance(item, dict):
            continue
        if "Topics" in item:
            iterable = item.get("Topics") or []
        else:
            iterable = [item]
        for related in iterable:
            if len(results) >= max_results:
                break
            if not isinstance(related, dict):
                continue
            add_result(
                results,
                title=str(related.get("Text") or "DuckDuckGo result")[:120],
                url=str(related.get("FirstURL") or ""),
                snippet=str(related.get("Text") or ""),
                rank=len(results) + 1,
            )
    return results[:max_results]


def search_web(query: str, max_results: Optional[int] = None) -> List[WebSearchResult]:
    if not web_search_enabled():
        return []

    limit = web_search_result_count(max_results or 5)
    provider = os.getenv("WEB_SEARCH_PROVIDER", "auto").strip().lower()
    query = re.sub(r"\s+", " ", query).strip()
    if not query:
        return []

    searchers = []
    if provider in {"auto", "serpapi"}:
        searchers.append(serpapi_search)
    if provider in {"auto", "bing"}:
        searchers.extend([bing_rss_search, bing_html_search])
    if provider in {"auto", "duckduckgo", "ddg"}:
        searchers.extend([duckduckgo_html_search, duckduckgo_instant_search])

    errors = []
    for searcher in searchers:
        try:
            results = filter_relevant_results(query, searcher(query, limit))
            if results:
                return results[:limit]
        except Exception as exc:
            errors.append(f"{searcher.__name__}: {type(exc).__name__}")
            continue

    if errors and os.getenv("WEB_SEARCH_DEBUG", "").strip().lower() in {"1", "true", "yes"}:
        print(f"[WEB_SEARCH] No results for '{query}': {'; '.join(errors)}")
    return []

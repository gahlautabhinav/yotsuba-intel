"""
Extract social links, email addresses, and PGP fingerprints from post text.

Applies to both raw HTML (href attributes) and plain body_text.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Optional, TypedDict


# ---------------------------------------------------------------------------
# TypedDicts
# ---------------------------------------------------------------------------

class ExtractedLink(TypedDict):
    platform: str
    raw_url: str
    handle: str
    extraction_confidence: float
    identity_weight: float
    confidence: float   # composite = extraction_confidence * identity_weight


class ExtractedEmail(TypedDict):
    email: str
    source: str   # "name_field" or "body"


class ExtractedPgp(TypedDict):
    fingerprint: str        # 40-char uppercase hex, no spaces
    context_snippet: str    # 50 chars around match


class ExtractedData(TypedDict):
    links: list[ExtractedLink]
    emails: list[ExtractedEmail]
    pgp_fingerprints: list[ExtractedPgp]


# ---------------------------------------------------------------------------
# Identity weights
# ---------------------------------------------------------------------------

IDENTITY_WEIGHT: dict[str, float] = {
    "pgp":       1.00,
    "keybase":   0.98,
    "github":    0.90,
    "twitter":   0.65,
    "instagram": 0.60,
    "telegram":  0.60,
    "youtube":   0.55,
    "steam":     0.70,
    "reddit":    0.45,
    "pastebin":  0.40,
    "discord":   0.20,
    "generic":   0.30,
}

# ---------------------------------------------------------------------------
# Social-link regexes
# ---------------------------------------------------------------------------

TWITTER_RE = re.compile(r'(?:twitter\.com|x\.com)/(?:@?)(\w{1,50})', re.I)
TWITTER_NON_PROFILE = {
    "home", "search", "explore", "settings", "notifications", "login", "i",
    "intent", "share", "messages", "compose", "hashtag", "help", "tos",
    "privacy", "about", "signup", "en", "_", "status",
}

GITHUB_RE = re.compile(r'github\.com/([\w\-]{1,39})(?:/([\w\-\.]+))?', re.I)
GITHUB_NON_PROFILE = {
    "features", "pricing", "about", "contact", "login", "join",
    "organizations", "topics", "trending", "marketplace", "pulls",
    "issues", "notifications", "settings", "explore", "apps",
    "sponsors", "security", "blog",
}

TELEGRAM_RE = re.compile(r't\.me/([\w]{5,32})', re.I)
INSTAGRAM_RE = re.compile(r'instagram\.com/([\w\.]{1,30})/?', re.I)
REDDIT_RE = re.compile(r'reddit\.com/(?:u|user)/([\w\-]{3,20})', re.I)
YOUTUBE_RE = re.compile(r'youtube\.com/(?:@|c/|user/)([\w\-]{3,50})', re.I)
DISCORD_RE = re.compile(r'discord\.gg/([\w]{2,20})', re.I)
KEYBASE_RE = re.compile(r'keybase\.io/([\w]{2,16})', re.I)
PASTEBIN_RE = re.compile(r'pastebin\.com/(?:u/([\w]+)|([a-zA-Z0-9]{8}))', re.I)
STEAM_RE = re.compile(r'steamcommunity\.com/(?:id|profiles)/([\w\-]{2,32})', re.I)
GENERIC_RE = re.compile(r'https?://[\w\-\./\?=&%#@+:~]+', re.I)

PERSONAL_TLDS = {'.dev', '.me', '.io', '.xyz', '.name'}

# ---------------------------------------------------------------------------
# Email regexes / blocklists
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r'[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}')
EMAIL_BLOCKLIST_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply", "admin", "support",
    "info", "contact", "hello", "team", "help", "mail", "email", "webmaster",
}
EMAIL_BLOCKLIST_DOMAINS = {
    "example.com", "test.com", "domain.com", "email.com", "tempmail.com",
    "throwaway.email", "mailinator.com", "guerrillamail.com",
}

# ---------------------------------------------------------------------------
# PGP regexes
# ---------------------------------------------------------------------------

PGP_COMPACT_RE = re.compile(r'\b([0-9A-Fa-f]{40})\b')
PGP_SPACED_RE = re.compile(r'([0-9A-Fa-f]{4}(?:\s[0-9A-Fa-f]{4}){9})')
PGP_CONTEXT_RE = re.compile(
    r'(pgp|gpg|fingerprint|public.?key|key.?id|sign|encrypt)', re.I
)

# ---------------------------------------------------------------------------
# HTML href extractor
# ---------------------------------------------------------------------------

class _HrefExtractor(HTMLParser):
    """Collect all href attribute values from an HTML string."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


def _extract_hrefs(html: str) -> list[str]:
    extractor = _HrefExtractor()
    extractor.feed(html)
    return extractor.hrefs


# ---------------------------------------------------------------------------
# Per-platform matchers
# ---------------------------------------------------------------------------

def _match_twitter(text: str) -> list[tuple[str, str, float]]:
    """Return list of (handle, raw_url_fragment, extraction_confidence)."""
    results = []
    for m in TWITTER_RE.finditer(text):
        handle = m.group(1).lower()
        if handle in TWITTER_NON_PROFILE:
            continue
        results.append((handle, m.group(0), 0.95))
    return results


def _match_github(text: str) -> list[tuple[str, str, float]]:
    results = []
    for m in GITHUB_RE.finditer(text):
        handle = m.group(1).lower()
        if handle in GITHUB_NON_PROFILE:
            continue
        repo_segment = m.group(2)
        # Profile URL (1 segment) → 0.97; repo URL (2 segments) → 0.75
        conf = 0.75 if repo_segment else 0.97
        results.append((handle, m.group(0), conf))
    return results


def _match_telegram(text: str) -> list[tuple[str, str, float]]:
    return [(m.group(1).lower(), m.group(0), 0.95) for m in TELEGRAM_RE.finditer(text)]


def _match_instagram(text: str) -> list[tuple[str, str, float]]:
    return [(m.group(1).lower(), m.group(0), 0.90) for m in INSTAGRAM_RE.finditer(text)]


def _match_reddit(text: str) -> list[tuple[str, str, float]]:
    return [(m.group(1).lower(), m.group(0), 0.90) for m in REDDIT_RE.finditer(text)]


def _match_youtube(text: str) -> list[tuple[str, str, float]]:
    return [(m.group(1).lower(), m.group(0), 0.90) for m in YOUTUBE_RE.finditer(text)]


def _match_discord(text: str) -> list[tuple[str, str, float]]:
    return [(m.group(1).lower(), m.group(0), 0.90) for m in DISCORD_RE.finditer(text)]


def _match_keybase(text: str) -> list[tuple[str, str, float]]:
    return [(m.group(1).lower(), m.group(0), 0.97) for m in KEYBASE_RE.finditer(text)]


def _match_pastebin(text: str) -> list[tuple[str, str, float]]:
    results = []
    for m in PASTEBIN_RE.finditer(text):
        user_handle = m.group(1)   # set if /u/handle form
        paste_key = m.group(2)     # set if 8-char paste key form
        handle = (user_handle or paste_key).lower()
        conf = 0.85 if user_handle else 0.60
        results.append((handle, m.group(0), conf))
    return results


def _match_steam(text: str) -> list[tuple[str, str, float]]:
    return [(m.group(1).lower(), m.group(0), 0.95) for m in STEAM_RE.finditer(text)]


def _match_generic(text: str, already_matched_spans: set[tuple[int, int]]) -> list[tuple[str, str, float]]:
    """Match https?:// URLs not already covered by a specific pattern."""
    results = []
    for m in GENERIC_RE.finditer(text):
        span = (m.start(), m.end())
        # Skip if this span overlaps any already-matched region
        overlaps = any(
            not (span[1] <= s[0] or span[0] >= s[1])
            for s in already_matched_spans
        )
        if overlaps:
            continue
        raw = m.group(0)
        # Determine confidence based on TLD
        tld_match = re.search(r'(\.[a-z]{2,6})(?:/|$|\?)', raw, re.I)
        conf = 0.50
        if tld_match and tld_match.group(1).lower() in PERSONAL_TLDS:
            conf = 0.65
        results.append((raw, raw, conf))
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PLATFORM_MATCHERS = [
    ("twitter",   _match_twitter,   TWITTER_RE),
    ("github",    _match_github,    GITHUB_RE),
    ("telegram",  _match_telegram,  TELEGRAM_RE),
    ("instagram", _match_instagram, INSTAGRAM_RE),
    ("reddit",    _match_reddit,    REDDIT_RE),
    ("youtube",   _match_youtube,   YOUTUBE_RE),
    ("discord",   _match_discord,   DISCORD_RE),
    ("keybase",   _match_keybase,   KEYBASE_RE),
    ("pastebin",  _match_pastebin,  PASTEBIN_RE),
    ("steam",     _match_steam,     STEAM_RE),
]


def _collect_links(text: str) -> list[ExtractedLink]:
    """Run all platform matchers against *text* and collect ExtractedLink entries."""
    links: list[ExtractedLink] = []
    matched_spans: set[tuple[int, int]] = set()

    for platform, matcher, pattern in _PLATFORM_MATCHERS:
        matches = matcher(text)
        iw = IDENTITY_WEIGHT[platform]
        for handle, raw_fragment, ec in matches:
            # Track spans to exclude from generic matching
            for m in pattern.finditer(text):
                matched_spans.add((m.start(), m.end()))
            links.append(ExtractedLink(
                platform=platform,
                raw_url=raw_fragment,
                handle=handle,
                extraction_confidence=ec,
                identity_weight=iw,
                confidence=ec * iw,
            ))

    # Generic URLs
    iw_generic = IDENTITY_WEIGHT["generic"]
    for handle, raw_url, ec in _match_generic(text, matched_spans):
        links.append(ExtractedLink(
            platform="generic",
            raw_url=raw_url,
            handle=handle,
            extraction_confidence=ec,
            identity_weight=iw_generic,
            confidence=ec * iw_generic,
        ))

    return links


def _deduplicate_links(links: list[ExtractedLink]) -> list[ExtractedLink]:
    """Keep one entry per (platform, handle) — the one with highest confidence."""
    best: dict[tuple[str, str], ExtractedLink] = {}
    for link in links:
        key = (link["platform"], link["handle"])
        if key not in best or link["confidence"] > best[key]["confidence"]:
            best[key] = link
    return list(best.values())


def _is_blocked_email(email: str) -> bool:
    local, _, domain = email.partition("@")
    local_lower = local.lower()
    domain_lower = domain.lower()
    if any(local_lower == p or local_lower.startswith(p) for p in EMAIL_BLOCKLIST_PREFIXES):
        return True
    if domain_lower in EMAIL_BLOCKLIST_DOMAINS:
        return True
    return False


def _collect_emails(text: str, source: str) -> list[ExtractedEmail]:
    results = []
    for m in EMAIL_RE.finditer(text):
        email = m.group(0)
        if not _is_blocked_email(email):
            results.append(ExtractedEmail(email=email, source=source))
    return results


def _collect_pgp(text: str) -> list[ExtractedPgp]:
    results = []
    seen: set[str] = set()

    def _try_add(fp_raw: str, match_start: int, match_end: int) -> None:
        fp = fp_raw.replace(" ", "").upper()
        if fp in seen:
            return
        # Must have PGP context keyword within 100 chars
        window_start = max(0, match_start - 100)
        window_end = min(len(text), match_end + 100)
        window = text[window_start:window_end]
        if not PGP_CONTEXT_RE.search(window):
            return
        seen.add(fp)
        # Context snippet: 50 chars around the match
        snip_start = max(0, match_start - 25)
        snip_end = min(len(text), match_end + 25)
        snippet = text[snip_start:snip_end]
        results.append(ExtractedPgp(fingerprint=fp, context_snippet=snippet))

    for m in PGP_COMPACT_RE.finditer(text):
        _try_add(m.group(1), m.start(), m.end())

    for m in PGP_SPACED_RE.finditer(text):
        _try_add(m.group(1), m.start(), m.end())

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_from_post(
    body_html: str,
    body_text: str,
    name_field: str,
) -> ExtractedData:
    """Extract social links, emails, and PGP fingerprints from a post.

    Args:
        body_html:  Raw HTML of the post body (the ``com`` field).
        body_text:  Plain-text version (HTML already stripped).
        name_field: The poster's name field value.

    Returns:
        ExtractedData with links, emails, and pgp_fingerprints.
    """
    all_links: list[ExtractedLink] = []

    # 1. Links from href attributes in body_html
    if body_html:
        for href in _extract_hrefs(body_html):
            all_links.extend(_collect_links(href))

    # 2. Links from plain body_text
    all_links.extend(_collect_links(body_text))

    # 3. Deduplicate
    links = _deduplicate_links(all_links)

    # 4. Emails from body_text and name_field
    emails: list[ExtractedEmail] = []
    emails.extend(_collect_emails(body_text, "body"))
    emails.extend(_collect_emails(name_field, "name_field"))

    # Deduplicate emails by address
    seen_emails: set[str] = set()
    unique_emails: list[ExtractedEmail] = []
    for e in emails:
        if e["email"] not in seen_emails:
            seen_emails.add(e["email"])
            unique_emails.append(e)

    # 5. PGP fingerprints from body_text
    pgp = _collect_pgp(body_text)

    return ExtractedData(links=links, emails=unique_emails, pgp_fingerprints=pgp)

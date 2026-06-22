"""
Unified archive client for 4plebs, desuarchive, and warosu.

Searches archive sites by tripcode, file MD5, or poster name.
Rate-limited to 2 seconds between requests per site.
Never raises — returns partial results on error.
"""
from __future__ import annotations

import time
import urllib.parse
from datetime import datetime
from html.parser import HTMLParser
from typing import Optional, TypedDict

import requests


# ---------------------------------------------------------------------------
# TypedDict
# ---------------------------------------------------------------------------

class ArchivePost(TypedDict):
    source: str          # "4plebs", "desuarchive", "warosu"
    board: str
    thread_no: int
    post_no: int
    posted_at: Optional[datetime]
    name: Optional[str]
    trip: Optional[str]
    poster_id: Optional[str]
    country: Optional[str]
    body_text: Optional[str]
    file_md5: Optional[str]
    filename: Optional[str]
    archive_url: Optional[str]


# ---------------------------------------------------------------------------
# HTML stripping helper
# ---------------------------------------------------------------------------

class _Stripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "br":
            self._parts.append("\n")


def _strip_html(html: str) -> str:
    s = _Stripper()
    s.feed(html)
    return "".join(s._parts).strip()


# ---------------------------------------------------------------------------
# Archive client
# ---------------------------------------------------------------------------

class ArchiveClient:
    RATE_LIMIT = 2.0  # seconds between requests per site

    # Boards supported by each archive
    _4PLEBS_BOARDS = {"pol", "adv", "f", "hr", "o", "s4s", "sp", "tg", "trv", "tv", "x"}
    _DESUARCHIVE_BOARDS = {"a", "c", "w", "m", "cgl", "cm", "f", "n", "jp", "vp", "g", "co", "v", "mu", "mlp", "r9k", "bant"}
    _WAROSU_BOARDS = {"g", "sci", "fa", "ic", "jp", "vr", "cgl", "co", "an", "fit", "ck", "diy", "i", "po"}

    _SOURCES = ["4plebs", "desuarchive", "warosu"]

    def __init__(self) -> None:
        self._last_request: dict[str, float] = {}
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "chan-osint/0.1 (OSINT research tool)"})

    # ------------------------------------------------------------------
    # Public search methods
    # ------------------------------------------------------------------

    def search_by_trip(
        self,
        trip: str,
        sources: list[str] | None = None,
    ) -> list[ArchivePost]:
        """Search all (or specified) archive sites for a tripcode."""
        targets = self._resolve_sources(sources)
        results: list[ArchivePost] = []
        for source in targets:
            results.extend(self._search(source, trip=trip))
        return results

    def search_by_md5(
        self,
        file_md5: str,
        sources: list[str] | None = None,
    ) -> list[ArchivePost]:
        """Search all (or specified) archive sites for a file MD5."""
        targets = self._resolve_sources(sources)
        results: list[ArchivePost] = []
        for source in targets:
            results.extend(self._search(source, md5=file_md5))
        return results

    def search_by_name(
        self,
        name: str,
        board: str | None = None,
        sources: list[str] | None = None,
    ) -> list[ArchivePost]:
        """Search all (or specified) archive sites for a poster name."""
        targets = self._resolve_sources(sources)
        results: list[ArchivePost] = []
        for source in targets:
            results.extend(self._search(source, name=name, board=board))
        return results

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------

    def _resolve_sources(self, sources: list[str] | None) -> list[str]:
        if sources is None:
            return list(self._SOURCES)
        return [s for s in sources if s in self._SOURCES]

    def _search(
        self,
        source: str,
        *,
        trip: str | None = None,
        md5: str | None = None,
        name: str | None = None,
        board: str | None = None,
    ) -> list[ArchivePost]:
        if source == "4plebs":
            return self._search_4plebs(trip=trip, md5=md5, name=name, board=board)
        elif source == "desuarchive":
            return self._search_desuarchive(trip=trip, md5=md5, name=name, board=board)
        elif source == "warosu":
            return self._search_warosu(trip=trip, md5=md5, name=name, board=board)
        return []

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _wait(self, site: str) -> None:
        last = self._last_request.get(site, 0.0)
        elapsed = time.time() - last
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)

    def _mark(self, site: str) -> None:
        self._last_request[site] = time.time()

    # ------------------------------------------------------------------
    # HTTP helper
    # ------------------------------------------------------------------

    def _get_json(self, site: str, url: str, params: dict) -> dict | None:
        self._wait(site)
        try:
            resp = self._session.get(url, params=params, timeout=15)
            self._mark(site)
            if resp.status_code != 200:
                print(f"[archive] Warning: {site} returned HTTP {resp.status_code} for {url}")
                return None
            return resp.json()
        except requests.exceptions.RequestException as exc:
            self._mark(site)
            print(f"[archive] Warning: connection error for {site}: {exc}")
            return None
        except ValueError as exc:
            self._mark(site)
            print(f"[archive] Warning: JSON parse error for {site}: {exc}")
            return None

    # ------------------------------------------------------------------
    # 4plebs
    # ------------------------------------------------------------------

    def _search_4plebs(
        self,
        *,
        trip: str | None,
        md5: str | None,
        name: str | None,
        board: str | None,
    ) -> list[ArchivePost]:
        params: dict = {}
        if trip:
            params["trip"] = trip
        if md5:
            params["md5"] = urllib.parse.quote(md5, safe="")
        if name:
            params["name"] = name
        if board and board in self._4PLEBS_BOARDS:
            params["boards"] = board

        data = self._get_json("4plebs", "https://archive.4plebs.org/_/api/chan/search/", params)
        if data is None:
            return []
        return self._parse_4plebs_response(data, "4plebs", "https://archive.4plebs.org")

    def _search_desuarchive(
        self,
        *,
        trip: str | None,
        md5: str | None,
        name: str | None,
        board: str | None,
    ) -> list[ArchivePost]:
        params: dict = {}
        if trip:
            params["trip"] = trip
        if md5:
            params["md5"] = urllib.parse.quote(md5, safe="")
        if name:
            params["name"] = name
        if board and board in self._DESUARCHIVE_BOARDS:
            params["boards"] = board

        data = self._get_json("desuarchive", "https://desuarchive.org/_/api/chan/search/", params)
        if data is None:
            return []
        return self._parse_4plebs_response(data, "desuarchive", "https://desuarchive.org")

    def _parse_4plebs_response(
        self,
        data: dict,
        source: str,
        base_url: str,
    ) -> list[ArchivePost]:
        """Parse 4plebs/desuarchive-style API response."""
        results: list[ArchivePost] = []

        # No results: data["0"] may be missing, False, or lack "posts"
        top = data.get("0")
        if not top or not isinstance(top, dict):
            return []

        posts_raw = top.get("posts")
        if not posts_raw or not isinstance(posts_raw, dict):
            return []

        for post_val in posts_raw.values():
            if not isinstance(post_val, dict):
                continue
            try:
                board_info = post_val.get("board") or {}
                board = board_info.get("shortname", "") if isinstance(board_info, dict) else str(board_info)
                thread_num = int(post_val.get("thread_num") or 0)
                post_num = int(post_val.get("num") or 0)
                timestamp = post_val.get("timestamp")
                posted_at = datetime.utcfromtimestamp(int(timestamp)) if timestamp else None
                comment = post_val.get("comment") or ""
                body_text = _strip_html(comment) if comment else None

                media = post_val.get("media") or {}
                file_md5: Optional[str] = None
                filename: Optional[str] = None
                if isinstance(media, dict):
                    file_md5 = media.get("media_hash") or None
                    filename = media.get("media_filename") or None

                archive_url: Optional[str] = None
                if board and thread_num and post_num:
                    archive_url = f"{base_url}/{board}/thread/{thread_num}#p{post_num}"

                results.append(ArchivePost(
                    source=source,
                    board=board,
                    thread_no=thread_num,
                    post_no=post_num,
                    posted_at=posted_at,
                    name=post_val.get("name") or None,
                    trip=post_val.get("trip") or None,
                    poster_id=post_val.get("poster_hash") or None,
                    country=post_val.get("country_code") or None,
                    body_text=body_text,
                    file_md5=file_md5,
                    filename=filename,
                    archive_url=archive_url,
                ))
            except Exception as exc:
                print(f"[archive] Warning: failed to parse {source} post: {exc}")
                continue

        return results

    # ------------------------------------------------------------------
    # warosu
    # ------------------------------------------------------------------

    def _search_warosu(
        self,
        *,
        trip: str | None,
        md5: str | None,
        name: str | None,
        board: str | None,
    ) -> list[ArchivePost]:
        # warosu requires a board parameter — iterate all supported boards if none given
        boards_to_search = [board] if (board and board in self._WAROSU_BOARDS) else sorted(self._WAROSU_BOARDS)

        results: list[ArchivePost] = []
        for b in boards_to_search:
            params: dict = {"board": b}
            if trip:
                params["trip"] = trip
            if md5:
                params["md5"] = urllib.parse.quote(md5, safe="")
            if name:
                params["name"] = name

            data = self._get_json("warosu", "https://warosu.org/api/v1/search", params)
            if data is None:
                continue
            results.extend(self._parse_warosu_response(data, b))

        return results

    def _parse_warosu_response(self, data: dict, board: str) -> list[ArchivePost]:
        """Parse warosu API response."""
        results: list[ArchivePost] = []

        posts_raw = data.get("posts")
        # Guard against null or non-list
        if not posts_raw or not isinstance(posts_raw, list):
            return []

        for post_val in posts_raw:
            if not isinstance(post_val, dict):
                continue
            try:
                post_no = int(post_val.get("no") or 0)
                thread_no = int(post_val.get("thread_no") or 0)
                timestamp = post_val.get("time")
                posted_at = datetime.utcfromtimestamp(int(timestamp)) if timestamp else None
                comment = post_val.get("com") or ""
                body_text = _strip_html(comment) if comment else None
                file_md5 = post_val.get("md5") or None
                filename = post_val.get("filename") or None

                archive_url: Optional[str] = None
                if board and thread_no and post_no:
                    archive_url = f"https://warosu.org/{board}/thread/{thread_no}#p{post_no}"

                results.append(ArchivePost(
                    source="warosu",
                    board=board,
                    thread_no=thread_no,
                    post_no=post_no,
                    posted_at=posted_at,
                    name=post_val.get("name") or None,
                    trip=post_val.get("trip") or None,
                    poster_id=None,
                    country=None,
                    body_text=body_text,
                    file_md5=file_md5,
                    filename=filename,
                    archive_url=archive_url,
                ))
            except Exception as exc:
                print(f"[archive] Warning: failed to parse warosu post: {exc}")
                continue

        return results

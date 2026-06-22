"""
Parse raw 4chan thread JSON into typed dicts.

HTML stripping uses stdlib html.parser — no external dependencies.
"""
from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from typing import Optional, TypedDict


# ---------------------------------------------------------------------------
# TypedDicts
# ---------------------------------------------------------------------------

class FileData(TypedDict):
    tim: int          # 4chan timestamp-based filename (no ext)
    filename: str     # original filename (no ext)
    ext: str          # e.g. ".jpg"
    fsize: int
    md5: str          # base64-encoded MD5
    w: int
    h: int


class PostData(TypedDict):
    post_no: int
    resto: int            # 0 = OP
    posted_at: datetime
    name: str
    trip: Optional[str]
    poster_id: Optional[str]
    capcode: Optional[str]
    country: Optional[str]
    country_name: Optional[str]
    body_html: Optional[str]
    body_text: str        # HTML stripped
    has_file: bool
    file: Optional[FileData]


class ThreadData(TypedDict):
    board: str
    thread_no: int
    subject: Optional[str]
    post_count: int
    unique_ips: Optional[int]
    is_archived: bool


# ---------------------------------------------------------------------------
# HTML → plain text converter
# ---------------------------------------------------------------------------

class _HTMLStripper(HTMLParser):
    """Strips HTML tags, converts <br>/<p> to newlines, decodes entities."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("br", "p"):
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "p":
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def _strip_html(html: str) -> str:
    """Strip HTML tags from *html* and return plain text.

    Converts <br> and </p> to newlines.
    Decodes common HTML entities via convert_charrefs=True.
    """
    # Pre-process: normalise self-closing <br/> so the parser sees <br>
    html = html.replace("<br/>", "<br>").replace("<br />", "<br>")
    stripper = _HTMLStripper()
    stripper.feed(html)
    return stripper.get_text()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_thread(board: str, raw_json: dict) -> tuple[ThreadData, list[PostData]]:
    """Convert raw 4chan thread JSON to (ThreadData, list[PostData]).

    Args:
        board:    Board code, e.g. "g"
        raw_json: Parsed JSON from https://a.4cdn.org/{board}/thread/{no}.json

    Returns:
        (thread_data, posts)  where posts[0] is always the OP.
    """
    raw_posts: list[dict] = raw_json["posts"]
    op = raw_posts[0]

    thread_data: ThreadData = {
        "board": board,
        "thread_no": op["no"],
        "subject": op.get("sub") or None,
        # 4chan replies count excludes OP; post_count = replies + 1
        "post_count": (op.get("replies") or 0) + 1,
        "unique_ips": op.get("unique_ips") or None,
        "is_archived": bool(op.get("archived", 0)),
    }

    posts: list[PostData] = [_parse_post(p) for p in raw_posts]
    return thread_data, posts


def _parse_post(raw: dict) -> PostData:
    body_html: Optional[str] = raw.get("com") or None
    body_text: str = _strip_html(body_html) if body_html else ""

    # Trip detection
    trip_raw: Optional[str] = raw.get("trip") or None

    # File data
    has_file = "tim" in raw
    file_data: Optional[FileData] = None
    if has_file:
        file_data = FileData(
            tim=raw["tim"],
            filename=raw.get("filename", ""),
            ext=raw.get("ext", ""),
            fsize=raw.get("fsize", 0),
            md5=raw.get("md5", ""),
            w=raw.get("w", 0),
            h=raw.get("h", 0),
        )

    return PostData(
        post_no=raw["no"],
        resto=raw.get("resto", 0),
        posted_at=datetime.utcfromtimestamp(raw["time"]),
        name=raw.get("name", "Anonymous"),
        trip=trip_raw,
        poster_id=raw.get("id") or None,
        capcode=raw.get("capcode") or None,
        country=raw.get("country") or None,
        country_name=raw.get("country_name") or None,
        body_html=body_html,
        body_text=body_text,
        has_file=has_file,
        file=file_data,
    )

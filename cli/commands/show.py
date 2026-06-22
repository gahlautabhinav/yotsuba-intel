from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def show() -> None:
    """Show stored data."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_tty() -> bool:
    return sys.stdout.isatty()


def _trunc(value: object, n: int) -> str:
    s = str(value) if value is not None else ""
    return s[:n] + "…" if len(s) > n else s


# ---------------------------------------------------------------------------
# chan show threads
# ---------------------------------------------------------------------------

@show.command("threads")
def show_threads() -> None:
    """List all scraped threads."""
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    repo = Repository()
    threads = repo.list_threads()

    if _is_tty():
        table = Table(title="Threads", show_lines=False)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Board", style="magenta")
        table.add_column("Thread#", style="yellow")
        table.add_column("Subject", style="white", max_width=40)
        table.add_column("Posts", style="green")
        table.add_column("Scraped At", style="dim")

        for t in threads:
            table.add_row(
                str(t.id),
                t.board,
                str(t.thread_no),
                _trunc(t.subject or "", 40),
                str(t.post_count or ""),
                str(t.scraped_at or ""),
            )
        console.print(table)
    else:
        data = [
            {
                "id": t.id,
                "board": t.board,
                "thread_no": t.thread_no,
                "subject": t.subject,
                "post_count": t.post_count,
                "scraped_at": t.scraped_at,
            }
            for t in threads
        ]
        print(json.dumps(data, default=str))


# ---------------------------------------------------------------------------
# chan show posts <thread_id>
# ---------------------------------------------------------------------------

@show.command("posts")
@click.argument("thread_id", type=int)
def show_posts(thread_id: int) -> None:
    """List posts in a thread."""
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    repo = Repository()
    posts = repo.get_posts_by_thread(thread_id)

    if _is_tty():
        table = Table(title=f"Posts — Thread #{thread_id}", show_lines=False)
        table.add_column("Post#", style="cyan", no_wrap=True)
        table.add_column("Posted At", style="dim")
        table.add_column("Name", style="magenta")
        table.add_column("Trip", style="yellow")
        table.add_column("Country", style="blue")
        table.add_column("Body", style="white", max_width=60)

        for p in posts:
            table.add_row(
                str(p.post_no),
                str(p.posted_at or ""),
                p.name or "",
                p.trip or "",
                p.country or "",
                _trunc(p.body_text or "", 60),
            )
        console.print(table)
    else:
        data = [
            {
                "id": p.id,
                "post_no": p.post_no,
                "posted_at": p.posted_at,
                "name": p.name,
                "trip": p.trip,
                "country": p.country,
                "body_text": p.body_text,
            }
            for p in posts
        ]
        print(json.dumps(data, default=str))


# ---------------------------------------------------------------------------
# chan show links <thread_id>
# ---------------------------------------------------------------------------

@show.command("links")
@click.argument("thread_id", type=int)
def show_links(thread_id: int) -> None:
    """List social links extracted from a thread."""
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    repo = Repository()
    links = repo.get_links_by_thread(thread_id)

    if _is_tty():
        table = Table(title=f"Links — Thread #{thread_id}", show_lines=False)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Post#", style="yellow")
        table.add_column("Platform", style="magenta")
        table.add_column("Handle", style="white")
        table.add_column("Confidence", style="green")
        table.add_column("Status", style="dim")

        for lk in links:
            # Get pivot status if any
            pivot_status = ""
            if lk.pivot_results:
                pivot_status = lk.pivot_results[-1].status
            table.add_row(
                str(lk.id),
                str(lk.post_id),
                lk.platform,
                lk.handle or "",
                f"{lk.confidence:.2f}",
                pivot_status,
            )
        console.print(table)
    else:
        data = [
            {
                "id": lk.id,
                "post_id": lk.post_id,
                "platform": lk.platform,
                "handle": lk.handle,
                "raw_url": lk.raw_url,
                "confidence": lk.confidence,
            }
            for lk in links
        ]
        print(json.dumps(data, default=str))


# ---------------------------------------------------------------------------
# chan show emails <thread_id>
# ---------------------------------------------------------------------------

@show.command("emails")
@click.argument("thread_id", type=int)
def show_emails(thread_id: int) -> None:
    """List emails extracted from a thread."""
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    repo = Repository()
    emails = repo.get_emails_by_thread(thread_id)

    if _is_tty():
        table = Table(title=f"Emails — Thread #{thread_id}", show_lines=False)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Post#", style="yellow")
        table.add_column("Email", style="white")
        table.add_column("Source", style="magenta")
        table.add_column("Breach Count", style="red")
        table.add_column("Name Hint", style="dim")

        for e in emails:
            table.add_row(
                str(e.id),
                str(e.post_id),
                e.email,
                e.source,
                str(e.breach_count) if e.breach_count is not None else "",
                e.real_name_hint or "",
            )
        console.print(table)
    else:
        data = [
            {
                "id": e.id,
                "post_id": e.post_id,
                "email": e.email,
                "source": e.source,
                "breach_count": e.breach_count,
                "real_name_hint": e.real_name_hint,
            }
            for e in emails
        ]
        print(json.dumps(data, default=str))


# ---------------------------------------------------------------------------
# chan show tripcodes
# ---------------------------------------------------------------------------

@show.command("tripcodes")
def show_tripcodes() -> None:
    """List all known tripcodes."""
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    repo = Repository()
    trips = repo.list_tripcodes()

    if _is_tty():
        table = Table(title="Tripcodes", show_lines=False)
        table.add_column("Trip", style="cyan")
        table.add_column("Strength", style="magenta")
        table.add_column("Posts", style="yellow")
        table.add_column("Boards", style="blue")
        table.add_column("TZ Guess", style="green")
        table.add_column("First Seen", style="dim")
        table.add_column("Last Seen", style="dim")

        for t in trips:
            boards = ""
            if t.boards_seen:
                try:
                    boards = ", ".join(json.loads(t.boards_seen))
                except Exception:
                    boards = t.boards_seen
            table.add_row(
                t.trip,
                t.trip_strength,
                str(t.post_count),
                boards,
                t.timezone_guess or "",
                str(t.first_seen_at or ""),
                str(t.last_seen_at or ""),
            )
        console.print(table)
    else:
        data = [
            {
                "trip": t.trip,
                "trip_strength": t.trip_strength,
                "post_count": t.post_count,
                "boards_seen": t.boards_seen,
                "timezone_guess": t.timezone_guess,
                "first_seen_at": t.first_seen_at,
                "last_seen_at": t.last_seen_at,
            }
            for t in trips
        ]
        print(json.dumps(data, default=str))


# ---------------------------------------------------------------------------
# chan show pivots <thread_id>
# ---------------------------------------------------------------------------

@show.command("pivots")
@click.argument("thread_id", type=int)
def show_pivots(thread_id: int) -> None:
    """List pivot results for links in a thread."""
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    repo = Repository()
    rows = repo.get_pivot_results_by_thread(thread_id)

    if _is_tty():
        table = Table(title=f"Pivots — Thread #{thread_id}", show_lines=False)
        table.add_column("Link ID", style="cyan", no_wrap=True)
        table.add_column("Platform", style="magenta")
        table.add_column("Handle", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Real Name", style="green")
        table.add_column("Email", style="blue")
        table.add_column("Location", style="dim")

        for link, pivot in rows:
            status = pivot.status if pivot else "pending"
            real_name = ""
            email_hint = ""
            location = ""
            if pivot and pivot.profile_data:
                try:
                    pd_dict = json.loads(pivot.profile_data)
                    real_name = pd_dict.get("real_name", "") or ""
                    email_hint = pd_dict.get("email", "") or ""
                    location = pd_dict.get("location", "") or ""
                except Exception:
                    pass
            table.add_row(
                str(link.id),
                link.platform,
                link.handle or "",
                status,
                real_name,
                email_hint,
                location,
            )
        console.print(table)
    else:
        data = [
            {
                "link_id": link.id,
                "platform": link.platform,
                "handle": link.handle,
                "status": pivot.status if pivot else "pending",
                "profile_data": pivot.profile_data if pivot else None,
            }
            for link, pivot in rows
        ]
        print(json.dumps(data, default=str))

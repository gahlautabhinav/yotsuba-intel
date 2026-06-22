from __future__ import annotations

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _trunc(value: object, n: int) -> str:
    s = str(value) if value is not None else ""
    return s[:n] + "…" if len(s) > n else s


@click.command()
@click.option("--trip", "trip", type=str, default=None, help="Tripcode to search (e.g. '!ABC123XYZ')")
@click.option("--md5", "md5", type=str, default=None, help="Base64 file MD5 to search")
@click.option("--name", "name", type=str, default=None, help="Poster name to search")
@click.option(
    "--source",
    "source",
    type=str,
    default=None,
    help="Comma-separated archive sources: 4plebs,desuarchive,warosu (default: all)",
)
@click.option(
    "--board",
    "board",
    type=str,
    default=None,
    help="Board filter (used with warosu; e.g. 'g')",
)
@click.option(
    "--save/--no-save",
    "save",
    default=True,
    help="Save results to database (default: --save)",
)
def archive(
    trip: Optional[str],
    md5: Optional[str],
    name: Optional[str],
    source: Optional[str],
    board: Optional[str],
    save: bool,
) -> None:
    """Search 4chan archives (4plebs, desuarchive, warosu) by trip, MD5, or name."""
    if not trip and not md5 and not name:
        console.print("[red]Error:[/red] at least one of --trip, --md5, or --name is required.")
        raise SystemExit(1)

    from storage.engine import init_db
    from storage.repository import Repository
    from scraper.archive_client import ArchiveClient

    init_db()
    repo = Repository()
    client = ArchiveClient()

    # Parse sources
    sources: Optional[list[str]] = None
    if source:
        sources = [s.strip() for s in source.split(",") if s.strip()]

    # Run search
    if trip:
        console.print(f"[cyan]Searching archives for trip: {trip}...[/cyan]")
        results = client.search_by_trip(trip, sources=sources)
    elif md5:
        console.print(f"[cyan]Searching archives for MD5: {md5}...[/cyan]")
        results = client.search_by_md5(md5, sources=sources)
    else:
        console.print(f"[cyan]Searching archives for name: {name}...[/cyan]")
        results = client.search_by_name(name, board=board, sources=sources)

    console.print(f"[green]Found {len(results)} result(s).[/green]")

    # Save to DB
    if save and results:
        from datetime import datetime, timezone

        saved = 0
        for post in results:
            try:
                fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
                repo.save_archive_post(
                    source=post["source"],
                    board=post["board"],
                    thread_no=post["thread_no"],
                    post_no=post["post_no"],
                    posted_at=post.get("posted_at"),
                    name=post.get("name"),
                    trip=post.get("trip"),
                    poster_id=post.get("poster_id"),
                    country=post.get("country"),
                    body_text=post.get("body_text"),
                    file_md5=post.get("file_md5"),
                    filename=post.get("filename"),
                    archive_url=post.get("archive_url"),
                    fetched_at=fetched_at,
                )
                saved += 1
            except Exception as exc:
                console.print(f"[yellow]Warning:[/yellow] could not save post {post.get('post_no')}: {exc}")
        console.print(f"[dim]Saved {saved} post(s) to database.[/dim]")

    # Display table
    if not results:
        console.print("[dim]No results to display.[/dim]")
        return

    table = Table(title="Archive Search Results", show_lines=False)
    table.add_column("Post#", style="cyan", no_wrap=True)
    table.add_column("Board", style="magenta")
    table.add_column("Source", style="yellow")
    table.add_column("Posted At", style="dim")
    table.add_column("Name", style="white")
    table.add_column("Trip", style="green")
    table.add_column("Body (80)", style="white", max_width=80)

    for post in results:
        table.add_row(
            str(post.get("post_no") or ""),
            post.get("board") or "",
            post.get("source") or "",
            str(post.get("posted_at") or ""),
            post.get("name") or "",
            post.get("trip") or "",
            _trunc(post.get("body_text") or "", 80),
        )

    console.print(table)

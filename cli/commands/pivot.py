from __future__ import annotations

from typing import Optional

import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--thread", "thread_id", type=int, default=None, help="Filter by thread ID")
@click.option(
    "--platform",
    "platforms_str",
    type=str,
    default=None,
    help="Comma-separated platform names: github,reddit,keybase",
)
def pivot(thread_id: Optional[int], platforms_str: Optional[str]) -> None:
    """Run pivot lookups on pending social links."""
    from storage.engine import init_db
    from pivot.resolver import run_pivots

    platforms = [p.strip() for p in platforms_str.split(",")] if platforms_str else None

    if thread_id is not None:
        console.print(f"[cyan]Running pivots for thread {thread_id}...[/cyan]")
    elif platforms:
        console.print(f"[cyan]Running pivots for platforms: {', '.join(platforms)}...[/cyan]")
    else:
        console.print("[cyan]Running all pending pivots...[/cyan]")

    counts = run_pivots(thread_id=thread_id, platforms=platforms)

    console.print(
        f"[green]Done.[/green] "
        f"processed={counts['processed']} "
        f"success={counts['success']} "
        f"failed={counts['failed']} "
        f"skipped={counts['skipped']}"
    )

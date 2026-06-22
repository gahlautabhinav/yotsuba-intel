"""chan correlate — cross-thread image correlation via MD5 reuse analysis."""
from __future__ import annotations

import json
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command()
@click.option("--md5", "md5", type=str, required=True, help="Base64 file MD5 to correlate")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
def correlate(md5: str, fmt: str) -> None:
    """Find all posts that reused a specific image MD5 and score same-person likelihood."""
    from analysis.md5_correlator import correlate_md5, PostRef

    result = correlate_md5(md5)

    if fmt == "json":
        # PostRef dataclasses need manual serialization
        serializable = dict(result)
        serializable["post_refs"] = [
            {
                "source": r.source,
                "board": r.board,
                "thread_no": r.thread_no,
                "post_no": r.post_no,
                "posted_at": str(r.posted_at) if r.posted_at else None,
                "name": r.name,
                "trip": r.trip,
                "archive_url": r.archive_url,
            }
            for r in result["post_refs"]
        ]
        print(json.dumps(serializable, default=str))
        return

    # Rich table of post references
    refs: list[PostRef] = result["post_refs"]
    if refs:
        table = Table(title=f"Posts using MD5: {md5}", show_lines=False)
        table.add_column("Source", style="yellow")
        table.add_column("Board", style="magenta")
        table.add_column("Thread#", style="cyan", no_wrap=True)
        table.add_column("Post#", style="cyan", no_wrap=True)
        table.add_column("Posted At", style="dim")
        table.add_column("Name", style="white")
        table.add_column("Trip", style="green")
        for r in refs:
            table.add_row(
                r.source,
                r.board,
                str(r.thread_no),
                str(r.post_no),
                str(r.posted_at) if r.posted_at else "",
                r.name or "",
                r.trip or "",
            )
        console.print(table)
    else:
        console.print("[dim]No posts found with this MD5.[/dim]")

    # Summary panel
    type_color = {
        "strong": "green",
        "moderate": "yellow",
        "weak": "red",
        "meme_discard": "dim",
    }.get(result["correlation_type"], "white")

    summary_lines = [
        f"[bold]Post count:[/bold]    {result['post_count']}",
        f"[bold]Board count:[/bold]   {result['board_count']}",
        f"[bold]Confidence:[/bold]    {result['confidence'] * 100:.1f}%",
        f"[bold]Type:[/bold]          [{type_color}]{result['correlation_type']}[/{type_color}]",
        f"[bold]Likely meme:[/bold]   {'yes' if result['is_likely_meme'] else 'no'}",
        f"[bold]Trip match:[/bold]    {'yes' if result['has_tripcode_match'] else 'no'}",
    ]

    if result["evidence"]:
        summary_lines.append("")
        summary_lines.append("[bold]Evidence:[/bold]")
        for ev in result["evidence"]:
            summary_lines.append(f"  • {ev}")

    console.print(Panel("\n".join(summary_lines), title="[cyan]Correlation Analysis[/cyan]", expand=False))

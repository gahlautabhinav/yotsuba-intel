"""chan profile — build and display a full identity profile for a tripcode."""
from __future__ import annotations

import json
import dataclasses
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _sparkline(counts: list[int]) -> str:
    bars = "▁▂▃▄▅▆▇█"
    max_c = max(counts) or 1
    return "".join(bars[min(7, int(c / max_c * 7))] for c in counts)


@click.command()
@click.option("--trip", "trip", type=str, required=True, help="Tripcode to profile (e.g. '!ABC123XYZ')")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
def profile(trip: str, fmt: str) -> None:
    """Build and display a full identity profile for a tripcode."""
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    repo = Repository()

    tripcode_obj = repo.get_tripcode(trip)
    if tripcode_obj is None:
        console.print(
            f"[yellow]Tripcode not found locally.[/yellow] "
            f"Run [bold]chan scrape[/bold] first."
        )
        raise SystemExit(0)

    from analysis.tripcode_profiler import profile_trip

    try:
        prof = profile_trip(trip)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1)

    if fmt == "json":
        print(json.dumps(dataclasses.asdict(prof), default=str))
        return

    # --- Rich table display ---

    # Identity panel
    identity_lines = [
        f"[bold]Tripcode:[/bold]     {prof.trip}",
        f"[bold]Strength:[/bold]     {prof.trip_strength}",
        f"[bold]Post count:[/bold]   {prof.post_count} local / {prof.archive_post_count} archive",
        f"[bold]Boards:[/bold]       {', '.join(prof.boards) if prof.boards else 'none'}",
        f"[bold]Countries:[/bold]    {', '.join(prof.countries) if prof.countries else 'none'}",
        f"[bold]First seen:[/bold]   {prof.first_seen or 'unknown'}",
        f"[bold]Last seen:[/bold]    {prof.last_seen or 'unknown'}",
    ]
    console.print(Panel("\n".join(identity_lines), title="[cyan]Identity[/cyan]", expand=False))

    # Timezone panel
    histogram_str = _sparkline(prof.timezone_histogram)
    tz_lines = [
        f"[bold]Timezone guess:[/bold]   {prof.timezone_guess}",
        f"[bold]Confidence:[/bold]       {prof.timezone_confidence * 100:.1f}%",
        f"[bold]Histogram (0h-23h):[/bold]",
        f"  {histogram_str}",
    ]
    if prof.timezone_warning:
        tz_lines.append(f"[yellow]Warning:[/yellow] {prof.timezone_warning}")
    console.print(Panel("\n".join(tz_lines), title="[cyan]Timezone[/cyan]", expand=False))

    # Social links panel
    if prof.social_links:
        links_table = Table(show_header=True, header_style="bold magenta")
        links_table.add_column("Platform")
        links_table.add_column("Handle")
        links_table.add_column("Confidence")
        for lnk in prof.social_links:
            links_table.add_row(
                lnk.get("platform") or "",
                lnk.get("handle") or "",
                f"{lnk.get('confidence', 0):.2f}",
            )
        console.print(Panel(links_table, title="[cyan]Social Links[/cyan]", expand=False))
    else:
        console.print(Panel("[dim]No social links found.[/dim]", title="[cyan]Social Links[/cyan]", expand=False))

    # Emails panel
    if prof.emails:
        emails_str = "\n".join(f"  • {e}" for e in prof.emails)
    else:
        emails_str = "[dim]None found.[/dim]"
    console.print(Panel(emails_str, title="[cyan]Emails[/cyan]", expand=False))

    # Name variants panel
    if prof.name_variants:
        names_str = "\n".join(f"  • {n}" for n in prof.name_variants)
    else:
        names_str = "[dim]None found.[/dim]"
    console.print(Panel(names_str, title="[cyan]Name Variants[/cyan]", expand=False))

    # PGP fingerprints
    if prof.pgp_fingerprints:
        pgp_str = "\n".join(f"  • {fp}" for fp in prof.pgp_fingerprints)
        console.print(Panel(pgp_str, title="[cyan]PGP Fingerprints[/cyan]", expand=False))

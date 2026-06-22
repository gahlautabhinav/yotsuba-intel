from __future__ import annotations

import csv
import json
import sys

import click
from rich.console import Console

console = Console()


def _model_to_dict(obj) -> dict:
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


@click.command()
@click.argument("thread_id", type=int)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["csv", "json"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Output format.",
)
def export(thread_id: int, fmt: str) -> None:
    """Export all data for a thread (posts, links, emails, PGP keys)."""
    from storage.engine import init_db
    from storage.repository import Repository

    init_db()
    repo = Repository()

    thread = repo.get_thread(thread_id)
    if thread is None:
        console.print(f"[red]Thread #{thread_id} not found.[/red]", file=sys.stderr)
        raise SystemExit(1)

    posts = repo.get_posts_by_thread(thread_id)
    links = repo.get_links_by_thread(thread_id)
    emails = repo.get_emails_by_thread(thread_id)
    pgp_keys = repo.get_pgp_keys_by_thread(thread_id)

    thread_dict = _model_to_dict(thread)
    posts_dicts = [_model_to_dict(p) for p in posts]
    links_dicts = [_model_to_dict(lk) for lk in links]
    emails_dicts = [_model_to_dict(e) for e in emails]
    pgp_dicts = [_model_to_dict(k) for k in pgp_keys]

    if fmt == "json":
        payload = {
            "thread": thread_dict,
            "posts": posts_dicts,
            "links": links_dicts,
            "emails": emails_dicts,
            "pgp_keys": pgp_dicts,
        }
        output = json.dumps(payload, default=str)
        sys.stdout.buffer.write(output.encode("utf-8") + b"\n")
        sys.stdout.buffer.flush()

    elif fmt == "csv":
        writer = csv.writer(sys.stdout)

        def _write_section(name: str, rows: list[dict]) -> None:
            if not rows:
                writer.writerow([f"# {name}: (empty)"])
                return
            writer.writerow([f"# {name}"])
            writer.writerow(list(rows[0].keys()))
            for row in rows:
                writer.writerow(list(row.values()))
            writer.writerow([])

        _write_section("thread", [thread_dict])
        _write_section("posts", posts_dicts)
        _write_section("links", links_dicts)
        _write_section("emails", emails_dicts)
        _write_section("pgp_keys", pgp_dicts)

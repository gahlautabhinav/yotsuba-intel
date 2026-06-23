from __future__ import annotations

import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind to")
@click.option("--port", type=int, default=8003, show_default=True, help="Port to listen on")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool):
    """Start the Yotsuba Intel API server."""
    import uvicorn
    console.print(f"[green]Starting API server at http://{host}:{port}[/green]")
    console.print("[dim]Ctrl+C to stop[/dim]")
    uvicorn.run("api.main:app", host=host, port=port, reload=reload)

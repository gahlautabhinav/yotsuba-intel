import click
from rich.console import Console

console = Console()


@click.group()
def cli():
    """Yotsuba Intel — 4chan thread OSINT tool."""
    pass


# Import and register sub-commands here
from cli.commands.scrape import scrape
from cli.commands.show import show
from cli.commands.export import export
from cli.commands.pivot import pivot
from cli.commands.watch import watch
from cli.commands.archive import archive
from cli.commands.profile import profile
from cli.commands.correlate import correlate

cli.add_command(scrape)
cli.add_command(show)
cli.add_command(export)
cli.add_command(pivot)
cli.add_command(watch)
cli.add_command(archive)
cli.add_command(profile)
cli.add_command(correlate)

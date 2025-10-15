"""Main CLI interface for votuderep using rich-click."""

import sys

import rich_click as click
from rich.console import Console

from . import __version__
from .utils.logging import setup_logger
from .utils.validators import VotuDerepError

# Configure rich-click
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "yellow italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."

console = Console(stderr=True)


@click.group()
@click.version_option(version=__version__, prog_name="votuderep")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, verbose: bool):
    """
    [bold blue]votuderep[/bold blue] - A CLI tool for dereplicating and filtering viral contigs.

    Use subcommands to perform specific operations:

    • [bold]derep[/bold]: Dereplicate vOTUs using BLAST and ANI clustering
    • [bold]filter[/bold]: Filter FASTA files using CheckV quality metrics
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Setup logger
    setup_logger(verbose=verbose)


def main():
    """Main entry point for the CLI."""
    try:
        # Import commands here to avoid circular imports
        from .commands.derep import derep
        from .commands.filter import filter_cmd

        # Register commands
        cli.add_command(derep)
        cli.add_command(filter_cmd)

        # Run CLI
        cli(obj={})
    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}", style="red")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            console.print_exception()
        sys.exit(2)


if __name__ == "__main__":
    main()

"""Filter command for filtering FASTA files using CheckV metrics."""

import rich_click as click
from rich.console import Console

from ..core.filtering import filter_by_checkv
from ..utils.logging import get_logger
from ..utils.validators import validate_file_exists, VotuDerepError
from ..utils.io import filter_sequences

console = Console(stderr=True)
logger = get_logger(__name__)


@click.command(name="filter")
@click.argument("fasta", type=click.Path(exists=True, dir_okay=False))
@click.argument("checkv_out", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False),
    default=None,
    help="Output FASTA file (default: STDOUT)",
)
@click.option("-m", "--min-len", type=int, default=0, help="Minimum contig length")
@click.option("--max-len", type=int, default=0, help="Maximum contig length (0 = unlimited)")
@click.option("--provirus", is_flag=True, help="Only select proviruses (provirus == 'Yes')")
@click.option(
    "-c", "--min-completeness", type=float, default=None, help="Minimum completeness percentage"
)
@click.option("--max-contam", type=float, default=None, help="Maximum contamination percentage")
@click.option("--no-warnings", is_flag=True, help="Only keep contigs with no warnings")
@click.option(
    "--exclude-undetermined",
    is_flag=True,
    help="Exclude contigs with checkv_quality == 'Not-determined'",
)
@click.option(
    "--complete", is_flag=True, help="Only keep contigs with checkv_quality == 'Complete'"
)
@click.option(
    "--min-quality",
    type=click.Choice(["low", "medium", "high"], case_sensitive=False),
    default="low",
    help="Minimum quality level: low (includes Low/Medium/High/Complete), medium (Medium/High/Complete), or high (High/Complete)",
)
@click.pass_context
def filter_cmd(
    ctx,
    fasta: str,
    checkv_out: str,
    output: str,
    min_len: int,
    max_len: int,
    provirus: bool,
    min_completeness: float,
    max_contam: float,
    no_warnings: bool,
    exclude_undetermined: bool,
    complete: bool,
    min_quality: str,
):
    """
    Filter FASTA file using CheckV quality metrics.

    \b
    FASTA: Input FASTA file with viral contigs
    CHECKV_OUT: TSV output file from CheckV

    This command filters viral contigs based on various quality metrics from CheckV,
    including sequence length, completeness, contamination, and quality classification.

    \b
    Quality levels (hierarchical):
    • Complete: Highest quality, complete genomes
    • High-quality: High confidence viral sequences
    • Medium-quality: Moderate confidence sequences
    • Low-quality: Lower confidence but valid sequences
    • Not-determined: Quality could not be determined

    \b
    The --min-quality option filters inclusively:
    • low: Keeps Low-quality and above (default)
    • medium: Keeps Medium-quality and above
    • high: Keeps High-quality and above (including Complete)

    Not-determined sequences are included by default unless --exclude-undetermined is used.
    """
    console.print("[bold blue]votuderep filter[/bold blue] - Filter sequences by CheckV metrics\n")

    # Validate input files
    try:
        validate_file_exists(fasta, "Input FASTA file")
        validate_file_exists(checkv_out, "CheckV output file")
    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()

    # Validate numeric parameters
    if min_len < 0:
        console.print("[bold red]Error:[/bold red] --min-len must be >= 0")
        raise click.Abort()

    if max_len < 0:
        console.print("[bold red]Error:[/bold red] --max-len must be >= 0")
        raise click.Abort()

    if min_completeness is not None and not (0 <= min_completeness <= 100):
        console.print("[bold red]Error:[/bold red] --min-completeness must be between 0 and 100")
        raise click.Abort()

    if max_contam is not None and not (0 <= max_contam <= 100):
        console.print("[bold red]Error:[/bold red] --max-contam must be between 0 and 100")
        raise click.Abort()

    try:
        # Apply CheckV filters
        logger.info("Applying CheckV filters")
        passing_ids = filter_by_checkv(
            checkv_file=checkv_out,
            min_len=min_len,
            max_len=max_len,
            provirus_only=provirus,
            min_completeness=min_completeness,
            max_contam=max_contam,
            no_warnings=no_warnings,
            exclude_undetermined=exclude_undetermined,
            complete_only=complete,
            min_quality=min_quality.lower(),
        )

        if len(passing_ids) == 0:
            console.print("[yellow]Warning:[/yellow] No sequences passed the filters")
            if output:
                # Create empty output file
                open(output, "w").close()
            return

        # Filter FASTA file
        logger.info("Filtering FASTA file")
        num_written = filter_sequences(
            file_path=fasta, sequence_ids=passing_ids, output_path=output
        )

        # Success message (to stderr so it doesn't interfere with stdout output)
        console.print("\n[bold green]Success![/bold green]")
        console.print(f"Filtered {num_written} sequences")

        if output:
            console.print(f"Output written to: [bold]{output}[/bold]")
        else:
            console.print("Output written to: [bold]STDOUT[/bold]")

    except VotuDerepError as e:
        console.print(f"\n[bold red]Error during filtering:[/bold red] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error:[/bold red] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
        raise click.Abort()

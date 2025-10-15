"""Derep command for dereplicating vOTUs."""

import os
import shutil
import tempfile

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from ..core.blast import run_makeblastdb, run_blastn
from ..core.dereplication import dereplicate_sequences
from ..utils.logging import get_logger
from ..utils.validators import (
    check_blastn,
    validate_file_exists,
    validate_percentage,
    VotuDerepError,
)
from ..utils.io import filter_sequences

console = Console(stderr=True)
logger = get_logger(__name__)


def get_temp_directory(tmp_arg: str) -> str:
    """
    Determine the temporary directory to use.

    Args:
        tmp_arg: User-provided tmp directory path

    Returns:
        Path to a valid temporary directory

    Raises:
        VotuDerepError: If no valid temp directory found
    """
    # Try user-specified directory
    if tmp_arg and os.path.isdir(tmp_arg):
        return tmp_arg

    # Try common temp directories
    for temp_dir in [os.environ.get("TEMP"), os.environ.get("TMP"), "/tmp", "."]:
        if temp_dir and os.path.isdir(temp_dir):
            return temp_dir

    raise VotuDerepError("Could not find a valid temporary directory")


@click.command(name="derep")
@click.option(
    "-i",
    "--input",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Input FASTA file containing vOTUs",
)
@click.option(
    "-o",
    "--output",
    default="dereplicated_vOTUs.fasta",
    type=click.Path(dir_okay=False),
    help="Output FASTA file with dereplicated vOTUs",
)
@click.option("-t", "--threads", default=2, type=int, help="Number of threads for BLAST")
@click.option(
    "--tmp",
    default="",
    type=str,
    help="Directory for temporary files (default: $TEMP or /tmp or ./)",
)
@click.option(
    "--min-ani", default=95.0, type=float, help="Minimum ANI to consider two vOTUs as the same"
)
@click.option(
    "--min-tcov",
    default=85.0,
    type=float,
    help="Minimum target coverage to consider two vOTUs as the same",
)
@click.option("--keep", is_flag=True, help="Keep the temporary directory after completion")
@click.pass_context
def derep(
    ctx,
    input: str,
    output: str,
    threads: int,
    tmp: str,
    min_ani: float,
    min_tcov: float,
    keep: bool,
):
    """
    Dereplicate vOTUs using BLAST and ANI clustering.

    This command:
    1. Creates a BLAST database from input sequences
    2. Performs all-vs-all BLAST comparison
    3. Calculates ANI and coverage for sequence pairs
    4. Clusters sequences by ANI using greedy algorithm
    5. Outputs cluster representatives (longest sequences)

    The algorithm selects the longest sequence from each cluster as the
    representative, effectively removing shorter redundant sequences.
    """
    console.print("[bold blue]votuderep derep[/bold blue] - Dereplicate vOTUs\n")

    # Validate input
    try:
        validate_file_exists(input, "Input FASTA file")
        validate_percentage(min_ani, "min-ani")
        validate_percentage(min_tcov, "min-tcov")
    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()

    # Check for blastn
    try:
        blastn_path = check_blastn()
        logger.info(f"Using blastn: {blastn_path}")
    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()

    # Get temporary directory base
    try:
        temp_base = get_temp_directory(tmp)
    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(dir=temp_base, prefix="votuderep_")
    logger.info(f"Temporary directory: {temp_dir}")

    if keep:
        console.print(f"[yellow]Temporary files will be kept in:[/yellow] {temp_dir}\n")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            # Step 1: Create BLAST database
            task1 = progress.add_task("[cyan]Creating BLAST database...", total=None)
            db_path = os.path.join(temp_dir, "db")
            run_makeblastdb(input, db_path)
            progress.update(task1, completed=True)

            # Step 2: Run BLAST
            task2 = progress.add_task(f"[cyan]Running BLASTN ({threads} threads)...", total=None)
            blast_output = os.path.join(temp_dir, "blast.tsv")
            run_blastn(query=input, database=db_path, output=blast_output, threads=threads)
            progress.update(task2, completed=True)

            # Step 3: Dereplicate sequences
            task3 = progress.add_task("[cyan]Calculating ANI and clustering...", total=None)
            ani_output = os.path.join(temp_dir, "ani.tsv")
            representative_ids = dereplicate_sequences(
                fasta_file=input,
                blast_file=blast_output,
                output_ani=ani_output,
                min_ani=min_ani,
                min_tcov=min_tcov,
            )
            progress.update(task3, completed=True)

            # Step 4: Write output
            task4 = progress.add_task("[cyan]Writing dereplicated sequences...", total=None)
            num_written = filter_sequences(
                file_path=input, sequence_ids=representative_ids, output_path=output
            )
            progress.update(task4, completed=True)

        # Success message
        console.print("\n[bold green]Success![/bold green]")
        console.print(f"Wrote {num_written} dereplicated sequences to: [bold]{output}[/bold]")

        if keep:
            console.print(f"\nTemporary files saved in: {temp_dir}")
            console.print(f"  • BLAST results: {blast_output}")
            console.print(f"  • ANI results: {ani_output}")

    except Exception as e:
        console.print(f"\n[bold red]Error during dereplication:[/bold red] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
        raise click.Abort()

    finally:
        # Clean up temporary directory
        if not keep and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Removed temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary directory: {e}")

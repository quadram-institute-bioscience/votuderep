"""BRBH command: Best Reciprocal Best Hit search between two nucleotide FASTA files."""

import logging
import os
import shutil
import tempfile
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from ..core.blast import run_blastn, run_makeblastdb
from ..core.brbh import (
    decompress_if_needed,
    find_rbh,
    parse_best_hits,
    validate_nucleotide_fasta,
    write_rbh_table,
)
from ..utils.io import filter_sequences
from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError, check_blastn, validate_file_exists

console = Console(stderr=True)
logger = get_logger(__name__)


@click.command(name="brbh")
@click.argument("query", type=click.Path(exists=True, dir_okay=False))
@click.argument("target", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "-o",
    "--outdir",
    required=True,
    type=click.Path(file_okay=False),
    help="Output directory (created if absent)",
)
@click.option(
    "-b",
    "--basename",
    default="",
    type=str,
    help="Basename for output files [default: <query_stem>_vs_<target_stem>]",
)
@click.option(
    "--tmp",
    default="",
    type=str,
    help="Directory for temporary files [default: $TEMP or /tmp]",
)
@click.option("-t", "--threads", default=2, type=int, help="BLAST threads [default: 2]")
@click.option(
    "--evalue",
    default=1e-5,
    type=float,
    help="Maximum e-value for BLAST hits [default: 1e-5]",
)
@click.option(
    "--min-cov",
    default=50.0,
    type=float,
    help="Minimum coverage of query OR target (%) [default: 50.0]",
)
@click.option("--keep", is_flag=True, help="Keep temporary files after completion")
@click.pass_context
def brbh(
    ctx,
    query: str,
    target: str,
    outdir: str,
    basename: str,
    tmp: str,
    threads: int,
    evalue: float,
    min_cov: float,
    keep: bool,
) -> None:
    """
    Find Best Reciprocal Best Hits (BRBH) between two nucleotide FASTA files.

    A BRBH pair (A, B) is identified when sequence A in QUERY has sequence B
    in TARGET as its best BLASTN hit, and B has A as its best hit in the
    reverse search. This is a standard proxy for orthology in comparative
    genomics (Ward & Moreno-Hagelsieb 2014).

    Both QUERY and TARGET may be gzip-compressed (.gz); they are decompressed
    automatically to the temporary directory.

    \b
    Output files written to OUTDIR:
      {basename}_rbh.tsv      RBH pairs: query, target, %id, bitscore, evalue,
                              qlen, tlen, qcov, tcov, aln_len
      {basename}_query.fasta  QUERY sequences that have a reciprocal hit
      {basename}_target.fasta TARGET sequences that have a reciprocal hit

    \b
    Examples:
      votuderep brbh genome_a.fasta genome_b.fasta -o results/
      votuderep brbh a.fasta.gz b.fasta.gz -o results/ -b a_vs_b -t 8
      votuderep brbh query.fna target.fna -o out/ --evalue 1e-10 --min-cov 70
    """
    console.print("[bold blue]votuderep brbh[/bold blue] - Best Reciprocal Best Hits\n")

    verbose = ctx.obj.get("verbose", False)

    # --- Input validation ---
    try:
        validate_file_exists(query, "Query FASTA")
        validate_file_exists(target, "Target FASTA")
        if not 0.0 <= min_cov <= 100.0:
            raise VotuDerepError(f"--min-cov must be between 0 and 100, got {min_cov}")
        if evalue <= 0:
            raise VotuDerepError(f"--evalue must be positive, got {evalue}")
    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()

    # --- Check BLAST ---
    try:
        blastn_path = check_blastn()
        if verbose:
            console.print(f"[dim]Using blastn: {blastn_path}[/dim]")
    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()

    # --- Output directory ---
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)

    # --- Basename ---
    if not basename:
        q_stem = Path(query).name
        t_stem = Path(target).name
        for suffix in (".gz", ".fasta", ".fna", ".fa", ".fsa"):
            q_stem = q_stem.removesuffix(suffix)
            t_stem = t_stem.removesuffix(suffix)
        basename = f"{q_stem}_vs_{t_stem}"

    # --- Temporary directory ---
    tmp_base = (
        tmp
        if (tmp and os.path.isdir(tmp))
        else (os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp")
    )
    if not os.path.isdir(tmp_base):
        tmp_base = "."
    temp_dir = tempfile.mkdtemp(dir=tmp_base, prefix="votuderep_brbh_")
    if verbose:
        console.print(f"[dim]Temporary directory: {temp_dir}[/dim]")
    if keep:
        console.print(f"[yellow]Temporary files will be kept in:[/yellow] {temp_dir}\n")

    try:
        if not verbose:
            root_logger = logging.getLogger("votuderep")
            original_level = root_logger.level
            root_logger.setLevel(logging.WARNING)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:

            # Step 1: Decompress inputs if gzip
            task = progress.add_task("[cyan]Preparing input files...", total=None)
            query_path = decompress_if_needed(query, temp_dir)
            target_path = decompress_if_needed(target, temp_dir)
            progress.remove_task(task)

            # Step 2: Validate nucleotide content
            task = progress.add_task("[cyan]Validating nucleotide sequences...", total=None)
            try:
                validate_nucleotide_fasta(query_path)
                validate_nucleotide_fasta(target_path)
            except VotuDerepError as e:
                progress.remove_task(task)
                if not verbose:
                    root_logger.setLevel(original_level)
                console.print(f"[bold red]Error:[/bold red] {e}")
                raise click.Abort()
            progress.remove_task(task)

            # Step 3: Build BLAST databases
            task = progress.add_task("[cyan]Building BLAST databases...", total=None)
            db_query = os.path.join(temp_dir, "db_query")
            db_target = os.path.join(temp_dir, "db_target")
            run_makeblastdb(query_path, db_query)
            run_makeblastdb(target_path, db_target)
            progress.remove_task(task)

            # Step 4: Forward BLAST — query sequences against target DB
            task = progress.add_task(
                f"[cyan]Forward BLAST: query → target ({threads} threads)...", total=None
            )
            blast_fwd = os.path.join(temp_dir, "blast_fwd.tsv")
            run_blastn(
                query=query_path,
                database=db_target,
                output=blast_fwd,
                threads=threads,
                evalue=evalue,
            )
            progress.remove_task(task)

            # Step 5: Reverse BLAST — target sequences against query DB
            task = progress.add_task(
                f"[cyan]Reverse BLAST: target → query ({threads} threads)...", total=None
            )
            blast_rev = os.path.join(temp_dir, "blast_rev.tsv")
            run_blastn(
                query=target_path,
                database=db_query,
                output=blast_rev,
                threads=threads,
                evalue=evalue,
            )
            progress.remove_task(task)

            # Step 6: Find RBHs
            task = progress.add_task("[cyan]Finding reciprocal best hits...", total=None)
            fwd_hits = parse_best_hits(blast_fwd, min_cov=min_cov, evalue=evalue)
            rev_hits = parse_best_hits(blast_rev, min_cov=min_cov, evalue=evalue)
            rbh_list = find_rbh(fwd_hits, rev_hits)
            progress.remove_task(task)

            # Step 7: Write outputs
            task = progress.add_task("[cyan]Writing output files...", total=None)

            tsv_out = outdir_path / f"{basename}_rbh.tsv"
            query_out = outdir_path / f"{basename}_query.fasta"
            target_out = outdir_path / f"{basename}_target.fasta"

            write_rbh_table(rbh_list, str(tsv_out))

            query_ids = {r.qname for r in rbh_list}
            target_ids = {r.tname for r in rbh_list}
            n_query = filter_sequences(query_path, query_ids, str(query_out))
            n_target = filter_sequences(target_path, target_ids, str(target_out))

            progress.remove_task(task)

        if not verbose:
            root_logger.setLevel(original_level)

        console.print("\n[bold green]Success![/bold green]")
        console.print(f"Found [bold]{len(rbh_list)}[/bold] reciprocal best hits\n")
        console.print(f"  RBH table:      [bold]{tsv_out}[/bold]")
        console.print(f"  Query FASTA:    [bold]{query_out}[/bold] ({n_query} sequences)")
        console.print(f"  Target FASTA:   [bold]{target_out}[/bold] ({n_target} sequences)")

        if keep:
            console.print(f"\nTemporary files saved in: {temp_dir}")
            console.print(f"  • Forward BLAST: {blast_fwd}")
            console.print(f"  • Reverse BLAST: {blast_rev}")

    except click.Abort:
        raise
    except Exception as e:
        console.print(f"\n[bold red]Error during BRBH:[/bold red] {e}")
        if ctx.obj.get("verbose"):
            console.print_exception()
        raise click.Abort()

    finally:
        if not keep and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Removed temporary directory: {temp_dir}")
            except Exception as exc:
                logger.warning(f"Failed to remove temporary directory: {exc}")

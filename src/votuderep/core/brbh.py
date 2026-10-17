"""Best Reciprocal Best Hit (BRBH) analysis for nucleotide sequences."""

import gzip
import os
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError

logger = get_logger(__name__)

# Standard IUPAC nucleotide characters (DNA/RNA + ambiguity codes + gap)
_NUCLEOTIDE_CHARS = set("ACGTUNacgtunRYSWKMBDHVryswkmbdhv-")


@dataclass
class BlastHit:
    qname: str
    tname: str
    pident: float
    aln_len: int
    qstart: int
    qend: int
    tstart: int
    tend: int
    evalue: float
    bitscore: float
    qlen: int
    tlen: int

    @property
    def qcov(self) -> float:
        return round(100.0 * (self.qend - self.qstart + 1) / self.qlen, 2)

    @property
    def tcov(self) -> float:
        return round(100.0 * (self.tend - self.tstart + 1) / self.tlen, 2)


@dataclass
class RBH:
    qname: str
    tname: str
    pident: float
    bitscore: float
    evalue: float
    qlen: int
    tlen: int
    qcov: float
    tcov: float
    aln_len: int


def decompress_if_needed(fasta_path: str, tmpdir: str) -> str:
    """
    Decompress a gzip-compressed FASTA to tmpdir if needed.

    Returns the original path unchanged for non-.gz files.
    """
    if not fasta_path.endswith(".gz"):
        return fasta_path

    basename = os.path.basename(fasta_path[:-3])  # strip .gz
    dest = os.path.join(tmpdir, basename)
    logger.info(f"Decompressing {fasta_path} → {dest}")

    with gzip.open(fasta_path, "rb") as src, open(dest, "wb") as dst:
        shutil.copyfileobj(src, dst)

    return dest


def validate_nucleotide_fasta(fasta_path: str, sample_seqs: int = 10) -> None:
    """
    Verify that a FASTA file contains nucleotide sequences.

    Samples the first `sample_seqs` sequences (up to 500 bp each) and raises
    VotuDerepError if non-nucleotide characters exceed 10% of sampled bases.
    """
    from ..utils.io import read_fasta

    total, non_nuc = 0, 0
    checked = 0

    for _, seq in read_fasta(fasta_path):
        for ch in seq[:500]:
            total += 1
            if ch not in _NUCLEOTIDE_CHARS:
                non_nuc += 1
        checked += 1
        if checked >= sample_seqs:
            break

    if total == 0:
        raise VotuDerepError(f"FASTA file appears empty: {fasta_path}")

    non_nuc_pct = 100.0 * non_nuc / total
    if non_nuc_pct > 10.0:
        raise VotuDerepError(
            f"{fasta_path} does not appear to be a nucleotide FASTA "
            f"({non_nuc_pct:.1f}% non-nucleotide characters). "
            "Expected DNA/RNA sequences (ACGTN + IUPAC ambiguity codes)."
        )

    logger.debug(f"Nucleotide check passed for {fasta_path} ({non_nuc_pct:.2f}% non-nucleotide)")


def _parse_blast_line(line: str) -> Optional[BlastHit]:
    """
    Parse one BLAST tabular line (format '6 std qlen slen', 14 fields).

    Returns None if the line is malformed rather than raising.
    """
    fields = line.strip().split("\t")
    if len(fields) < 14:
        return None
    try:
        return BlastHit(
            qname=fields[0],
            tname=fields[1],
            pident=float(fields[2]),
            aln_len=int(fields[3]),
            qstart=int(fields[6]),
            qend=int(fields[7]),
            tstart=int(fields[8]),
            tend=int(fields[9]),
            evalue=float(fields[10]),
            bitscore=float(fields[11]),
            qlen=int(fields[12]),
            tlen=int(fields[13]),
        )
    except (ValueError, IndexError):
        return None


def parse_best_hits(
    blast_file: str,
    min_cov: float = 50.0,
    evalue: float = 1e-5,
) -> Dict[str, BlastHit]:
    """
    Parse a BLAST file and return the best hit per query sequence.

    Best hit = highest bitscore; ties broken by lowest evalue.
    Filters applied:
      - evalue <= threshold
      - qcov >= min_cov OR tcov >= min_cov (either sequence sufficiently covered)
      - self-hits discarded

    Args:
        blast_file: Path to BLAST output (format '6 std qlen slen')
        min_cov: Minimum coverage of query or target (%)
        evalue: Maximum e-value threshold

    Returns:
        Dict mapping query name → best BlastHit
    """
    best: Dict[str, BlastHit] = {}

    with open(blast_file) as fh:
        for line in fh:
            if not line.strip():
                continue
            hit = _parse_blast_line(line)
            if hit is None:
                continue
            if hit.qname == hit.tname:
                continue
            if hit.evalue > evalue:
                continue
            if hit.qcov < min_cov and hit.tcov < min_cov:
                continue

            prev = best.get(hit.qname)
            if (
                prev is None
                or hit.bitscore > prev.bitscore
                or (hit.bitscore == prev.bitscore and hit.evalue < prev.evalue)
            ):
                best[hit.qname] = hit

    logger.info(f"Parsed {len(best)} best hits from {blast_file}")
    return best


def find_rbh(
    forward_hits: Dict[str, BlastHit],
    reverse_hits: Dict[str, BlastHit],
) -> List[RBH]:
    """
    Find reciprocal best hits from two directed best-hit dictionaries.

    A pair (A, B) is an RBH when:
      - A's best hit in target is B  (forward)
      - B's best hit in query  is A  (reverse)

    Args:
        forward_hits: Best hits query→target (A→B)
        reverse_hits: Best hits target→query (B→A)

    Returns:
        List of RBH records sorted by bitscore descending
    """
    rbh_list: List[RBH] = []

    for qname, fwd in forward_hits.items():
        tname = fwd.tname
        rev = reverse_hits.get(tname)
        if rev is not None and rev.tname == qname:
            rbh_list.append(
                RBH(
                    qname=qname,
                    tname=tname,
                    pident=fwd.pident,
                    bitscore=fwd.bitscore,
                    evalue=fwd.evalue,
                    qlen=fwd.qlen,
                    tlen=fwd.tlen,
                    qcov=fwd.qcov,
                    tcov=fwd.tcov,
                    aln_len=fwd.aln_len,
                )
            )

    rbh_list.sort(key=lambda r: r.bitscore, reverse=True)
    logger.info(f"Found {len(rbh_list)} reciprocal best hits")
    return rbh_list


RBH_HEADER = "\t".join(
    ["query", "target", "pident", "bitscore", "evalue", "qlen", "tlen", "qcov", "tcov", "aln_len"]
)


def write_rbh_table(rbh_list: List[RBH], output_path: str) -> None:
    """Write RBH results to a TSV file."""
    with open(output_path, "w") as fh:
        fh.write(RBH_HEADER + "\n")
        for r in rbh_list:
            row = [
                r.qname,
                r.tname,
                f"{r.pident:.2f}",
                f"{r.bitscore:.1f}",
                f"{r.evalue:.2e}",
                str(r.qlen),
                str(r.tlen),
                f"{r.qcov:.2f}",
                f"{r.tcov:.2f}",
                str(r.aln_len),
            ]
            fh.write("\t".join(row) + "\n")
    logger.info(f"Wrote {len(rbh_list)} RBH records to {output_path}")

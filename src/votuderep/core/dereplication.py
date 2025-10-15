"""ANI calculation and clustering for vOTU dereplication."""

import gzip
from typing import Iterator, Dict, List, Tuple, Set


from ..utils.logging import get_logger
from ..utils.io import read_fasta

logger = get_logger(__name__)


def parse_blast_line(line: str) -> Dict:
    """
    Parse a single BLAST output line (format: '6 std qlen slen').

    Args:
        line: BLAST output line

    Returns:
        Dictionary with parsed BLAST fields
    """
    fields = line.strip().split("\t")
    return {
        "qname": fields[0],
        "tname": fields[1],
        "pid": float(fields[2]),
        "len": float(fields[3]),
        "qcoords": sorted([int(fields[6]), int(fields[7])]),
        "tcoords": sorted([int(fields[8]), int(fields[9])]),
        "qlen": float(fields[12]),
        "tlen": float(fields[13]),
        "evalue": float(fields[10]),
    }


def yield_alignment_blocks(blast_file: str) -> Iterator[List[Dict]]:
    """
    Group BLAST alignments by query-target pair.

    Args:
        blast_file: Path to BLAST output file

    Yields:
        List of alignments for each query-target pair
    """
    handle = gzip.open(blast_file, "rt") if blast_file.endswith(".gz") else open(blast_file)

    try:
        # Initialize with first record
        first_line = next(handle)
        first_aln = parse_blast_line(first_line)
        key = (first_aln["qname"], first_aln["tname"])
        alns = [first_aln]

        # Loop over remaining records
        for line in handle:
            aln = parse_blast_line(line)
            current_key = (aln["qname"], aln["tname"])

            # Extend current block
            if current_key == key:
                alns.append(aln)
            # Yield current block and start new one
            else:
                yield alns
                key = current_key
                alns = [aln]

        # Yield last block
        if alns:
            yield alns
    finally:
        handle.close()


def prune_alignments(alns: List[Dict], min_length: int = 0, min_evalue: float = 1e-3) -> List[Dict]:
    """
    Remove low-quality alignments and those beyond query coverage.

    Args:
        alns: List of alignments for a query-target pair
        min_length: Minimum alignment length
        min_evalue: Maximum E-value

    Returns:
        Pruned list of alignments
    """
    keep = []
    cur_aln = 0
    qry_len = alns[0]["qlen"]

    for aln in alns:
        qcoords = aln["qcoords"]
        aln_len = max(qcoords) - min(qcoords) + 1

        # Filter by length and e-value
        if aln_len < min_length or aln["evalue"] > min_evalue:
            continue

        # Stop if we've covered the query or exceeded 110% of query length
        if cur_aln >= qry_len or aln_len + cur_aln >= 1.10 * qry_len:
            break

        keep.append(aln)
        cur_aln += aln_len

    return keep


def compute_ani(alns: List[Dict]) -> float:
    """
    Compute average nucleotide identity (ANI) from alignments.

    Args:
        alns: List of alignments

    Returns:
        ANI as a percentage (0-100)
    """
    weighted_sum = sum(a["len"] * a["pid"] for a in alns)
    total_len = sum(a["len"] for a in alns)
    return round(weighted_sum / total_len, 2) if total_len > 0 else 0.0


def compute_coverage(alns: List[Dict]) -> Tuple[float, float]:
    """
    Compute query and target coverage from alignments.

    Args:
        alns: List of alignments

    Returns:
        Tuple of (query_coverage, target_coverage) as percentages
    """
    # Merge query coordinates
    qcoords = sorted([a["qcoords"] for a in alns])
    nr_qcoords = [qcoords[0][:]]  # Copy first coord pair

    for start, stop in qcoords[1:]:
        # Overlapping, update stop coord
        if start <= nr_qcoords[-1][1] + 1:
            nr_qcoords[-1][1] = max(nr_qcoords[-1][1], stop)
        # Non-overlapping, append
        else:
            nr_qcoords.append([start, stop])

    # Compute query coverage
    qlen = sum(stop - start + 1 for start, stop in nr_qcoords)
    qcov = round(100.0 * qlen / alns[0]["qlen"], 2)

    # Merge target coordinates
    tcoords = sorted([a["tcoords"] for a in alns])
    nr_tcoords = [tcoords[0][:]]  # Copy first coord pair

    for start, stop in tcoords[1:]:
        # Overlapping, update stop coord
        if start <= nr_tcoords[-1][1] + 1:
            nr_tcoords[-1][1] = max(nr_tcoords[-1][1], stop)
        # Non-overlapping, append
        else:
            nr_tcoords.append([start, stop])

    # Compute target coverage
    tlen = sum(stop - start + 1 for start, stop in nr_tcoords)
    tcov = round(100.0 * tlen / alns[0]["tlen"], 2)

    return qcov, tcov


def calculate_ani(blast_file: str, output_file: str, min_length: int = 0) -> None:
    """
    Calculate ANI and coverage from BLAST results.

    Args:
        blast_file: Path to BLAST output file
        output_file: Path to output ANI file
        min_length: Minimum alignment length to keep

    Creates a TSV file with columns: qname, tname, num_alns, pid, qcov, tcov
    """
    logger.info("Calculating ANI from BLAST results")

    handle = gzip.open(output_file, "wt") if output_file.endswith(".gz") else open(output_file, "w")

    try:
        # Write header
        fields = ["qname", "tname", "num_alns", "pid", "qcov", "tcov"]
        handle.write("\t".join(fields) + "\n")

        count = 0
        for alns in yield_alignment_blocks(blast_file):
            alns = prune_alignments(alns, min_length=min_length)

            if len(alns) == 0:
                continue

            qname, tname = alns[0]["qname"], alns[0]["tname"]
            ani = compute_ani(alns)
            qcov, tcov = compute_coverage(alns)

            row = [qname, tname, len(alns), ani, qcov, tcov]
            handle.write("\t".join(str(x) for x in row) + "\n")
            count += 1

        logger.info(f"Calculated ANI for {count} sequence pairs")
    finally:
        handle.close()


def cluster_by_ani(
    fasta_file: str,
    ani_file: str,
    min_ani: float = 95.0,
    min_qcov: float = 0.0,
    min_tcov: float = 85.0,
    min_length: int = 1,
) -> Dict[str, List[str]]:
    """
    Cluster sequences by ANI using centroid-based clustering.

    Args:
        fasta_file: Path to input FASTA file
        ani_file: Path to ANI file from calculate_ani
        min_ani: Minimum ANI threshold (0-100)
        min_qcov: Minimum query coverage (0-100)
        min_tcov: Minimum target coverage (0-100)
        min_length: Minimum sequence length

    Returns:
        Dictionary mapping centroid IDs to lists of member IDs
    """
    logger.info("Clustering sequences by ANI")

    # Read sequences, sorted by length (longest first)
    logger.debug("Reading sequences")
    seqs = {}
    for seq_id, seq in read_fasta(fasta_file):
        if len(seq) >= min_length:
            seqs[seq_id] = len(seq)

    # Sort by length descending
    sorted_seqs = [x[0] for x in sorted(seqs.items(), key=lambda x: x[1], reverse=True)]
    logger.info(f"Loaded {len(sorted_seqs)} sequences")

    # Build edges from ANI file
    logger.debug("Building edges from ANI comparisons")
    edges = {seq_id: [] for seq_id in sorted_seqs}
    num_edges = 0

    handle = gzip.open(ani_file, "rt") if ani_file.endswith(".gz") else open(ani_file)

    try:
        # Skip header
        next(handle)

        for line in handle:
            fields = line.strip().split("\t")
            qname, tname = fields[0], fields[1]
            ani, qcov, tcov = (
                float(fields[3]),
                float(fields[4]),
                float(fields[5]),
            )

            # Skip self-matches
            if qname == tname:
                continue

            # Skip if not in our sequence set
            if qname not in edges or tname not in edges:
                continue

            # Apply thresholds
            if qcov < min_qcov or tcov < min_tcov or ani < min_ani:
                continue

            edges[qname].append(tname)
            num_edges += 1
    finally:
        handle.close()

    logger.info(f"Loaded {num_edges} edges passing thresholds")

    # Perform greedy clustering
    logger.debug("Performing greedy clustering")
    clust_to_seqs = {}
    seq_to_clust = {}

    for seq_id in sorted_seqs:
        # Already assigned to a cluster
        if seq_id in seq_to_clust:
            continue

        # Create new cluster with seq_id as centroid
        clust_to_seqs[seq_id] = [seq_id]
        seq_to_clust[seq_id] = seq_id

        # Add cluster members
        for member_id in edges[seq_id]:
            if member_id not in seq_to_clust:
                clust_to_seqs[seq_id].append(member_id)
                seq_to_clust[member_id] = seq_id

    logger.info(f"Created {len(clust_to_seqs)} clusters")

    return clust_to_seqs


def dereplicate_sequences(
    fasta_file: str, blast_file: str, output_ani: str, min_ani: float = 95.0, min_tcov: float = 85.0
) -> Set[str]:
    """
    Dereplicate sequences by ANI clustering.

    Args:
        fasta_file: Path to input FASTA file
        blast_file: Path to BLAST output file
        output_ani: Path to output ANI file
        min_ani: Minimum ANI threshold (0-100)
        min_tcov: Minimum target coverage (0-100)

    Returns:
        Set of sequence IDs representing cluster centroids (to keep)
    """
    # Calculate ANI
    calculate_ani(blast_file, output_ani)

    # Cluster sequences
    clusters = cluster_by_ani(fasta_file, output_ani, min_ani=min_ani, min_tcov=min_tcov)

    # Return centroid IDs
    return set(clusters.keys())

"""Tests for BRBH (Best Reciprocal Best Hit) functionality."""

import gzip
import pytest
from pathlib import Path
from click.testing import CliRunner

from votuderep.core.brbh import (
    BlastHit,
    RBH,
    decompress_if_needed,
    find_rbh,
    parse_best_hits,
    validate_nucleotide_fasta,
    write_rbh_table,
)
from votuderep.cli import cli
from votuderep.commands.brbh import brbh

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hit(
    qname,
    tname,
    bitscore=500.0,
    evalue=1e-10,
    pident=95.0,
    qstart=1,
    qend=400,
    tstart=1,
    tend=400,
    qlen=400,
    tlen=400,
    aln_len=400,
):
    return BlastHit(
        qname=qname,
        tname=tname,
        pident=pident,
        aln_len=aln_len,
        qstart=qstart,
        qend=qend,
        tstart=tstart,
        tend=tend,
        evalue=evalue,
        bitscore=bitscore,
        qlen=qlen,
        tlen=tlen,
    )


def _blast_line(
    qname,
    tname,
    pident=95.0,
    aln_len=400,
    qstart=1,
    qend=400,
    sstart=1,
    send=400,
    evalue=1e-10,
    bitscore=500.0,
    qlen=400,
    tlen=400,
):
    fields = [
        qname,
        tname,
        str(pident),
        str(aln_len),
        "5",
        "0",  # mismatch, gapopen
        str(qstart),
        str(qend),
        str(sstart),
        str(send),
        str(evalue),
        str(bitscore),
        str(qlen),
        str(tlen),
    ]
    return "\t".join(fields) + "\n"


NUCLEOTIDE_SEQ = "ATCGATCG" * 50  # 400 bp
PROTEIN_SEQ = "MKVLILACLVVVSQA" * 10  # obviously amino-acid


# ---------------------------------------------------------------------------
# decompress_if_needed
# ---------------------------------------------------------------------------


class TestDecompressIfNeeded:
    def test_plain_file_returned_unchanged(self, tmp_path):
        fasta = tmp_path / "seq.fasta"
        fasta.write_text(">s1\nATCG\n")
        result = decompress_if_needed(str(fasta), str(tmp_path))
        assert result == str(fasta)

    def test_gz_file_is_decompressed(self, tmp_path):
        content = b">s1\nATCGATCG\n"
        gz_path = tmp_path / "seq.fasta.gz"
        with gzip.open(gz_path, "wb") as fh:
            fh.write(content)

        result = decompress_if_needed(str(gz_path), str(tmp_path))
        assert result != str(gz_path)
        assert result.endswith("seq.fasta")
        assert Path(result).read_text() == content.decode()


# ---------------------------------------------------------------------------
# validate_nucleotide_fasta
# ---------------------------------------------------------------------------


class TestValidateNucleotideFasta:
    def test_valid_nucleotide_passes(self, tmp_path):
        fasta = tmp_path / "nuc.fasta"
        fasta.write_text(f">s1\n{NUCLEOTIDE_SEQ}\n")
        validate_nucleotide_fasta(str(fasta))  # should not raise

    def test_protein_fasta_raises(self, tmp_path):
        from votuderep.utils.validators import VotuDerepError

        fasta = tmp_path / "prot.fasta"
        fasta.write_text(f">s1\n{PROTEIN_SEQ}\n")
        with pytest.raises(VotuDerepError, match="nucleotide"):
            validate_nucleotide_fasta(str(fasta))

    def test_empty_fasta_raises(self, tmp_path):
        from votuderep.utils.validators import VotuDerepError

        fasta = tmp_path / "empty.fasta"
        fasta.write_text("")
        with pytest.raises((VotuDerepError, FileNotFoundError, Exception)):
            validate_nucleotide_fasta(str(fasta))

    def test_iupac_ambiguity_codes_accepted(self, tmp_path):
        seq = "ATCGRYSWKMBDHVN" * 20
        fasta = tmp_path / "iupac.fasta"
        fasta.write_text(f">s1\n{seq}\n")
        validate_nucleotide_fasta(str(fasta))  # should not raise


# ---------------------------------------------------------------------------
# parse_best_hits
# ---------------------------------------------------------------------------


class TestParseBestHits:
    def test_basic_best_hit(self, tmp_path):
        blast = tmp_path / "blast.tsv"
        blast.write_text(
            _blast_line("qA", "tB", bitscore=800.0) + _blast_line("qA", "tC", bitscore=400.0)
        )
        hits = parse_best_hits(str(blast), min_cov=50.0, evalue=1e-3)
        assert "qA" in hits
        assert hits["qA"].tname == "tB"

    def test_self_hits_skipped(self, tmp_path):
        blast = tmp_path / "blast.tsv"
        blast.write_text(_blast_line("qA", "qA"))
        hits = parse_best_hits(str(blast), min_cov=0.0, evalue=1.0)
        assert hits == {}

    def test_evalue_filter(self, tmp_path):
        blast = tmp_path / "blast.tsv"
        blast.write_text(
            _blast_line("qA", "tB", evalue=1e-2)  # filtered out
            + _blast_line("qA", "tC", evalue=1e-10)  # kept
        )
        hits = parse_best_hits(str(blast), min_cov=50.0, evalue=1e-5)
        assert "qA" in hits
        assert hits["qA"].tname == "tC"

    def test_coverage_filter(self, tmp_path):
        blast = tmp_path / "blast.tsv"
        # qcov = (50-1+1)/400 = 12.5%, tcov = 12.5% — both below 50%
        blast.write_text(_blast_line("qA", "tB", qstart=1, qend=50, sstart=1, send=50))
        hits = parse_best_hits(str(blast), min_cov=50.0, evalue=1e-3)
        assert hits == {}

    def test_tiebreak_by_evalue(self, tmp_path):
        blast = tmp_path / "blast.tsv"
        blast.write_text(
            _blast_line("qA", "tB", bitscore=500.0, evalue=1e-20)
            + _blast_line("qA", "tC", bitscore=500.0, evalue=1e-5)
        )
        hits = parse_best_hits(str(blast), min_cov=50.0, evalue=1e-3)
        assert hits["qA"].tname == "tB"  # lower evalue wins

    def test_empty_blast_file(self, tmp_path):
        blast = tmp_path / "blast.tsv"
        blast.write_text("")
        hits = parse_best_hits(str(blast))
        assert hits == {}

    def test_malformed_lines_skipped(self, tmp_path):
        blast = tmp_path / "blast.tsv"
        blast.write_text("not\tenough\tfields\n" + _blast_line("qA", "tB"))
        hits = parse_best_hits(str(blast), min_cov=50.0, evalue=1e-3)
        assert "qA" in hits


# ---------------------------------------------------------------------------
# find_rbh
# ---------------------------------------------------------------------------


class TestFindRBH:
    def test_simple_reciprocal_pair(self):
        fwd = {"seqA": _hit("seqA", "seqB")}
        rev = {"seqB": _hit("seqB", "seqA")}
        rbh = find_rbh(fwd, rev)
        assert len(rbh) == 1
        assert rbh[0].qname == "seqA"
        assert rbh[0].tname == "seqB"

    def test_non_reciprocal_excluded(self):
        # seqA → seqB, seqB → seqC (not seqA)
        fwd = {"seqA": _hit("seqA", "seqB")}
        rev = {"seqB": _hit("seqB", "seqC")}
        rbh = find_rbh(fwd, rev)
        assert rbh == []

    def test_empty_hits(self):
        assert find_rbh({}, {}) == []

    def test_multiple_rbh_sorted_by_bitscore(self):
        fwd = {
            "seqA": _hit("seqA", "seqX", bitscore=900.0),
            "seqB": _hit("seqB", "seqY", bitscore=300.0),
        }
        rev = {
            "seqX": _hit("seqX", "seqA"),
            "seqY": _hit("seqY", "seqB"),
        }
        rbh = find_rbh(fwd, rev)
        assert len(rbh) == 2
        assert rbh[0].bitscore >= rbh[1].bitscore

    def test_no_match_in_reverse(self):
        fwd = {"seqA": _hit("seqA", "seqB")}
        rbh = find_rbh(fwd, {})  # seqB not in reverse
        assert rbh == []


# ---------------------------------------------------------------------------
# write_rbh_table
# ---------------------------------------------------------------------------


class TestWriteRBHTable:
    def test_header_and_rows(self, tmp_path):
        rbh_list = [
            RBH(
                qname="seqA",
                tname="seqB",
                pident=95.0,
                bitscore=500.0,
                evalue=1e-10,
                qlen=400,
                tlen=400,
                qcov=100.0,
                tcov=100.0,
                aln_len=400,
            )
        ]
        out = tmp_path / "rbh.tsv"
        write_rbh_table(rbh_list, str(out))
        lines = out.read_text().splitlines()
        assert lines[0].startswith("query\ttarget")
        assert "seqA" in lines[1]
        assert "seqB" in lines[1]

    def test_empty_list_writes_only_header(self, tmp_path):
        out = tmp_path / "rbh.tsv"
        write_rbh_table([], str(out))
        lines = out.read_text().splitlines()
        assert len(lines) == 1
        assert lines[0].startswith("query\ttarget")


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def _make_cli():
    if "brbh" not in cli.commands:
        cli.add_command(brbh)
    return cli


class TestBRBHCLI:
    def test_brbh_help(self):
        runner = CliRunner()
        result = runner.invoke(_make_cli(), ["brbh", "--help"], obj={})
        assert result.exit_code == 0
        assert "--min-cov" in result.output
        assert "--evalue" in result.output
        assert "--outdir" in result.output or "-o" in result.output

    def test_brbh_missing_blastn(self, tmp_path):
        import os

        fasta = tmp_path / "seq.fasta"
        fasta.write_text(f">s1\n{NUCLEOTIDE_SEQ}\n")

        runner = CliRunner()
        env = {k: v for k, v in os.environ.items()}
        env["PATH"] = str(tmp_path)  # no blastn
        result = runner.invoke(
            _make_cli(),
            ["brbh", str(fasta), str(fasta), "-o", str(tmp_path / "out")],
            env=env,
            obj={},
        )
        assert result.exit_code != 0

    def test_brbh_missing_query(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(
            _make_cli(),
            [
                "brbh",
                str(tmp_path / "nope.fasta"),
                str(tmp_path / "also_nope.fasta"),
                "-o",
                str(tmp_path / "out"),
            ],
            obj={},
        )
        assert result.exit_code != 0

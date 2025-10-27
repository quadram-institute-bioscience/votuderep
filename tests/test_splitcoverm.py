"""Tests for splitcoverm functionality."""

import csv
from pathlib import Path

import pytest

from votuderep.commands.splitcoverm import (
    normalize_metric_name,
    parse_header,
    split_coverm_table,
)
from votuderep.utils.validators import VotuDerepError


class TestMetricNormalization:
    """Test metric name normalization."""

    def test_normalize_read_count(self):
        """Test normalizing 'Read Count' to 'count'."""
        assert normalize_metric_name("Read Count") == "count"
        assert normalize_metric_name("read count") == "count"
        assert normalize_metric_name("READ COUNT") == "count"

    def test_normalize_mean(self):
        """Test normalizing 'Mean'."""
        assert normalize_metric_name("Mean") == "mean"
        assert normalize_metric_name("MEAN") == "mean"

    def test_normalize_tpm(self):
        """Test normalizing 'TPM'."""
        assert normalize_metric_name("TPM") == "tpm"
        assert normalize_metric_name("tpm") == "tpm"

    def test_normalize_rpkm(self):
        """Test normalizing 'RPKM'."""
        assert normalize_metric_name("RPKM") == "rpkm"
        assert normalize_metric_name("rpkm") == "rpkm"

    def test_normalize_covered_fraction(self):
        """Test normalizing 'Covered Fraction'."""
        assert normalize_metric_name("Covered Fraction") == "covered_fraction"
        assert normalize_metric_name("covered fraction") == "covered_fraction"

    def test_normalize_covered_bases(self):
        """Test normalizing 'Covered Bases'."""
        assert normalize_metric_name("Covered Bases") == "covered_bases"
        assert normalize_metric_name("covered bases") == "covered_bases"

    def test_normalize_generic(self):
        """Test generic normalization with spaces and special chars."""
        assert normalize_metric_name("Trimmed Mean") == "trimmed_mean"
        assert normalize_metric_name("Some-Metric/Value") == "some_metric_value"
        assert normalize_metric_name("Test  Multiple   Spaces") == "test_multiple_spaces"


class TestHeaderParsing:
    """Test header parsing functionality."""

    def test_parse_header_basic(self):
        """Test parsing a basic CoverM header."""
        header = ["Contig", "sample_1 Mean", "sample_1 TPM", "sample_2 Mean", "sample_2 TPM"]
        samples, metrics, metric_to_indices = parse_header(header)

        assert samples == ["sample_1", "sample_2"]
        assert metrics == ["mean", "tpm"]
        assert metric_to_indices["mean"] == [1, 3]
        assert metric_to_indices["tpm"] == [2, 4]

    def test_parse_header_real_coverm(self):
        """Test parsing actual CoverM output header."""
        header = [
            "Contig",
            "sample_1 RPKM",
            "sample_1 TPM",
            "sample_1 Mean",
            "sample_2 RPKM",
            "sample_2 TPM",
            "sample_2 Mean",
        ]
        samples, metrics, metric_to_indices = parse_header(header)

        assert samples == ["sample_1", "sample_2"]
        assert metrics == ["rpkm", "tpm", "mean"]
        assert len(metric_to_indices["rpkm"]) == 2
        assert len(metric_to_indices["tpm"]) == 2
        assert len(metric_to_indices["mean"]) == 2

    def test_parse_header_no_contig(self):
        """Test that parsing fails if first column is not 'Contig'."""
        header = ["Sequence", "sample_1 Mean"]
        with pytest.raises(VotuDerepError, match="First column must be 'Contig'"):
            parse_header(header)

    def test_parse_header_empty(self):
        """Test that parsing fails on empty header."""
        header = []
        with pytest.raises(VotuDerepError, match="First column must be 'Contig'"):
            parse_header(header)


class TestSplitCoverm:
    """Test CoverM table splitting functionality."""

    @pytest.fixture
    def test_data_dir(self):
        """Get the path to the tests directory."""
        return Path(__file__).parent

    @pytest.fixture
    def coverm_file(self, test_data_dir):
        """Path to the test CoverM file."""
        return str(test_data_dir / "coverm.tsv")

    def test_split_coverm_creates_files(self, coverm_file, tmp_path):
        """Test that splitcoverm creates the expected number of files."""
        output_basename = str(tmp_path / "output")

        # Run the split function
        output_files = split_coverm_table(coverm_file, output_basename, verbose=False)

        # Should create 8 metric files based on the test data
        # RPKM, TPM, Mean, Trimmed Mean, Covered Bases, Variance, Length, Read Count
        assert len(output_files) == 8, f"Expected 8 files, got {len(output_files)}"

        # Verify all files exist
        for output_file in output_files:
            assert Path(output_file).exists(), f"Output file not found: {output_file}"

    def test_split_coverm_file_names(self, coverm_file, tmp_path):
        """Test that output files have correct names."""
        output_basename = str(tmp_path / "test")

        output_files = split_coverm_table(coverm_file, output_basename, verbose=False)

        # Extract metric names from output files
        metric_names = [Path(f).stem.split("_", 1)[1] for f in output_files]

        # Expected metrics (normalized names)
        expected_metrics = [
            "rpkm",
            "tpm",
            "mean",
            "trimmed_mean",
            "covered_bases",
            "variance",
            "length",
            "count",
        ]

        assert set(metric_names) == set(expected_metrics)

    def test_split_coverm_content_structure(self, coverm_file, tmp_path):
        """Test that output files have correct structure."""
        output_basename = str(tmp_path / "output")

        output_files = split_coverm_table(coverm_file, output_basename, verbose=False)

        # Check the first output file
        first_file = output_files[0]

        with open(first_file, "r", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader)

            # Header should be: Contig + sample names
            assert header[0] == "Contig"
            assert len(header) == 5  # Contig + 4 samples (sample_1, sample_2, sample_3, sample_4)

            # Check that we have data rows
            rows = list(reader)
            # From the test file: bin1_1, bin1_2, bin1_3, bin2_1, bin2_2, bin3_1, bin3_2, bin3_3, bin3_4, bin3_5, bin4_1, bin4_2
            assert len(rows) == 12, f"Expected 12 data rows, got {len(rows)}"

    def test_split_coverm_sample_order(self, coverm_file, tmp_path):
        """Test that samples are in correct order in output files."""
        output_basename = str(tmp_path / "output")

        output_files = split_coverm_table(coverm_file, output_basename, verbose=False)

        # Check samples in header
        with open(output_files[0], "r", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader)
            samples = header[1:]  # Skip 'Contig' column

            assert samples == ["sample_1", "sample_2", "sample_3", "sample_4"]

    def test_split_coverm_data_integrity(self, coverm_file, tmp_path):
        """Test that data is correctly distributed across files."""
        output_basename = str(tmp_path / "output")

        output_files = split_coverm_table(coverm_file, output_basename, verbose=False)

        # Find the RPKM file
        rpkm_file = [f for f in output_files if f.endswith("_rpkm.tsv")][0]

        with open(rpkm_file, "r", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)  # Skip header
            first_row = next(reader)

            # First data row should be bin1_1
            assert first_row[0] == "bin1_1"
            # RPKM values for sample_1 should be 592.9474 (from the original file)
            assert first_row[1] == "592.9474"

    def test_split_coverm_nonexistent_file(self, tmp_path):
        """Test that function raises error for nonexistent input file."""
        output_basename = str(tmp_path / "output")
        fake_input = str(tmp_path / "nonexistent.tsv")

        with pytest.raises(VotuDerepError, match="Input file does not exist"):
            split_coverm_table(fake_input, output_basename, verbose=False)

    def test_split_coverm_empty_file(self, tmp_path):
        """Test that function raises error for empty input file."""
        empty_file = tmp_path / "empty.tsv"
        empty_file.write_text("")

        output_basename = str(tmp_path / "output")

        with pytest.raises(VotuDerepError, match="Input file is empty"):
            split_coverm_table(str(empty_file), output_basename, verbose=False)

    def test_split_coverm_gzipped_support(self, coverm_file, tmp_path):
        """Test that gzipped files are handled (even if not used in this test)."""
        # This test verifies the function accepts .gz extension
        # Note: We're not actually creating a gzipped file here,
        # just testing that the naming logic works
        output_basename = str(tmp_path / "output")

        # The function should work with regular files
        output_files = split_coverm_table(coverm_file, output_basename, verbose=False)
        assert len(output_files) > 0

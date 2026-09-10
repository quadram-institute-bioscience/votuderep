"""Tests for training data download helpers."""

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from votuderep.commands import trainingdata as trainingdata_module
from votuderep.commands.trainingdata import (
    DownloadItem,
    build_download_command,
    compute_md5,
    download_item,
    select_download_tool,
    trainingdata,
    verify_md5,
)
from votuderep.utils.validators import VotuDerepError


def test_select_download_tool_prefers_curl(monkeypatch):
    """Auto-selection should use curl first when both tools are present."""
    monkeypatch.setattr(trainingdata_module.shutil, "which", lambda tool: f"/bin/{tool}")

    assert select_download_tool("auto") == "curl"


def test_select_download_tool_falls_back_to_wget(monkeypatch):
    """Auto-selection should use wget if curl is absent."""
    monkeypatch.setattr(
        trainingdata_module.shutil,
        "which",
        lambda tool: f"/bin/{tool}" if tool == "wget" else None,
    )

    assert select_download_tool("auto") == "wget"


def test_select_download_tool_requires_one_tool(monkeypatch):
    """Preflight should fail before downloads start if no downloader exists."""
    monkeypatch.setattr(trainingdata_module.shutil, "which", lambda tool: None)

    with pytest.raises(VotuDerepError, match="curl or wget"):
        select_download_tool("auto")


def test_build_curl_command_fails_on_error_pages(tmp_path):
    """curl must be configured to reject HTTP error responses."""
    command = build_download_command("curl", "https://example.test/file", tmp_path / "file")

    assert "--fail" in command
    assert "--location" in command
    assert "--output" in command


def test_build_wget_command_uses_fresh_output_file(tmp_path):
    """wget should write to the requested path without enabling resume."""
    command = build_download_command("wget", "https://example.test/file", tmp_path / "file")

    assert "--output-document" in command
    assert "--continue" not in command
    assert "-c" not in command


def test_verify_md5_accepts_matching_file(tmp_path):
    """Matching checksums should pass."""
    path = tmp_path / "sample.txt"
    path.write_bytes(b"training data")

    verify_md5(path, compute_md5(path))


def test_verify_md5_rejects_mismatching_file(tmp_path):
    """Checksum mismatches should be reported as user-facing errors."""
    path = tmp_path / "sample.txt"
    path.write_bytes(b"training data")

    with pytest.raises(VotuDerepError, match="MD5 mismatch"):
        verify_md5(path, "00000000000000000000000000000000")


def test_download_item_removes_stale_partial_before_start(tmp_path, monkeypatch):
    """A stale partial file should never be resumed."""
    item = DownloadItem(
        url="https://example.test/file",
        relative_path=Path("reads/sample_R1.fastq.gz"),
        md5="",
        label="sample_R1",
    )
    partial_path = tmp_path / "reads" / "sample_R1.fastq.gz.part"
    partial_path.parent.mkdir()
    partial_path.write_bytes(b"old partial")

    def fake_run_download(tool, url, output_path):
        assert not output_path.exists()
        output_path.write_bytes(b"fresh file")

    monkeypatch.setattr(trainingdata_module, "run_download_command", fake_run_download)

    output_path = download_item(item, tmp_path, "curl", max_retry=1, skip_md5=True)

    assert output_path.read_bytes() == b"fresh file"
    assert not partial_path.exists()


def test_download_item_retries_without_reusing_partial(tmp_path, monkeypatch):
    """Retry attempts should start from a clean partial path."""
    item = DownloadItem(
        url="https://example.test/file",
        relative_path=Path("sample.fastq.gz"),
        md5="",
        label="sample",
    )
    calls = []

    def fake_run_download(tool, url, output_path):
        calls.append(output_path.exists())
        output_path.write_bytes(f"attempt {len(calls)}".encode())
        if len(calls) == 1:
            raise subprocess.CalledProcessError(22, ["curl"], stderr="server error")

    monkeypatch.setattr(trainingdata_module, "run_download_command", fake_run_download)

    output_path = download_item(item, tmp_path, "curl", max_retry=2, skip_md5=True)

    assert calls == [False, False]
    assert output_path.read_bytes() == b"attempt 2"
    assert not (tmp_path / "sample.fastq.gz.part").exists()


def test_download_item_skips_existing_verified_file(tmp_path, monkeypatch):
    """A complete existing file should not be downloaded again."""
    output_path = tmp_path / "sample.fastq.gz"
    output_path.write_bytes(b"already complete")
    partial_path = tmp_path / "sample.fastq.gz.part"
    partial_path.write_bytes(b"old partial")
    item = DownloadItem(
        url="https://example.test/file",
        relative_path=Path("sample.fastq.gz"),
        md5=compute_md5(output_path),
        label="sample",
    )

    def fake_run_download(tool, url, output_path):
        raise AssertionError("existing verified files should be skipped")

    monkeypatch.setattr(trainingdata_module, "run_download_command", fake_run_download)

    result_path = download_item(item, tmp_path, "curl", max_retry=1, skip_md5=False)

    assert result_path == output_path
    assert output_path.read_bytes() == b"already complete"
    assert not partial_path.exists()


def test_download_item_skips_existing_file_when_md5_is_disabled(tmp_path, monkeypatch):
    """--skip-md5 should trust and reuse an existing final file."""
    output_path = tmp_path / "sample.fastq.gz"
    output_path.write_bytes(b"already present")
    item = DownloadItem(
        url="https://example.test/file",
        relative_path=Path("sample.fastq.gz"),
        md5="00000000000000000000000000000000",
        label="sample",
    )

    def fake_run_download(tool, url, output_path):
        raise AssertionError("existing files should be skipped when MD5 is disabled")

    monkeypatch.setattr(trainingdata_module, "run_download_command", fake_run_download)

    result_path = download_item(item, tmp_path, "curl", max_retry=1, skip_md5=True)

    assert result_path == output_path
    assert output_path.read_bytes() == b"already present"


def test_download_item_replaces_existing_file_with_bad_md5(tmp_path, monkeypatch):
    """An existing corrupt final file should be redownloaded."""
    output_path = tmp_path / "sample.fastq.gz"
    output_path.write_bytes(b"corrupt")
    replacement = b"fresh replacement"
    expected_path = tmp_path / "expected.fastq.gz"
    expected_path.write_bytes(replacement)
    item = DownloadItem(
        url="https://example.test/file",
        relative_path=Path("sample.fastq.gz"),
        md5=compute_md5(expected_path),
        label="sample",
    )

    def fake_run_download(tool, url, partial_path):
        partial_path.write_bytes(replacement)

    monkeypatch.setattr(trainingdata_module, "run_download_command", fake_run_download)

    result_path = download_item(item, tmp_path, "curl", max_retry=1, skip_md5=False)

    assert result_path == output_path
    assert output_path.read_bytes() == replacement


def test_download_item_removes_bad_checksum_partial(tmp_path, monkeypatch):
    """A failed checksum should leave no final or partial file behind."""
    item = DownloadItem(
        url="https://example.test/file",
        relative_path=Path("sample.fastq.gz"),
        md5="00000000000000000000000000000000",
        label="sample",
    )

    def fake_run_download(tool, url, output_path):
        output_path.write_bytes(b"not the expected checksum")

    monkeypatch.setattr(trainingdata_module, "run_download_command", fake_run_download)

    with pytest.raises(VotuDerepError, match="Failed to download sample"):
        download_item(item, tmp_path, "curl", max_retry=1, skip_md5=False)

    assert not (tmp_path / "sample.fastq.gz").exists()
    assert not (tmp_path / "sample.fastq.gz.part").exists()


def test_trainingdata_cli_forwards_retry_and_md5_options(tmp_path, monkeypatch):
    """The CLI should pass retry and MD5 settings into the downloader."""
    item = DownloadItem(
        url="https://example.test/file",
        relative_path=Path("sample.fastq.gz"),
        md5="",
        label="sample",
    )
    calls = []

    monkeypatch.setattr(trainingdata_module, "TRAINING_DATASET", [item])
    monkeypatch.setattr(trainingdata_module, "select_download_tool", lambda requested: "wget")

    def fake_download_item(item, outdir, tool, max_retry, skip_md5):
        calls.append((item.label, outdir, tool, max_retry, skip_md5))

    monkeypatch.setattr(trainingdata_module, "download_item", fake_download_item)

    result = CliRunner().invoke(
        trainingdata,
        [
            "--outdir",
            str(tmp_path),
            "--download-tool",
            "auto",
            "--skip-md5",
            "--max-retry",
            "2",
        ],
        obj={"verbose": False},
    )

    assert result.exit_code == 0
    assert calls == [("sample", tmp_path, "wget", 2, True)]

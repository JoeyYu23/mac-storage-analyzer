"""Tests for scanner module."""

import os
from unittest.mock import patch, MagicMock

import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import (
    _run,
    _du_kb,
    _du_kb_list,
    kb_to_gb,
    _parse_docker_size,
    scan_disk_overview,
    scan_docker,
    scan_node_modules,
    scan_python_venvs,
    scan_ml_models,
    scan_top_projects,
    run_scan,
)


class TestKbToGb:
    def test_zero(self):
        assert kb_to_gb(0) == 0.0

    def test_one_gb(self):
        assert kb_to_gb(1024 * 1024) == 1.0

    def test_fractional(self):
        assert abs(kb_to_gb(512 * 1024) - 0.5) < 0.001


class TestParseDockerSize:
    def test_zero(self):
        assert _parse_docker_size("0B") == 0

    def test_empty(self):
        assert _parse_docker_size("") == 0

    def test_gb(self):
        result = _parse_docker_size("8.2GB")
        assert abs(result - 8.2 * 1024 * 1024) < 1

    def test_mb(self):
        result = _parse_docker_size("512MB")
        assert result == 512 * 1024

    def test_kb(self):
        assert _parse_docker_size("100KB") == 100

    def test_tb(self):
        result = _parse_docker_size("1TB")
        assert result == 1024 * 1024 * 1024

    def test_invalid(self):
        assert _parse_docker_size("not-a-size") == 0

    def test_bad_number(self):
        assert _parse_docker_size("abcGB") == 0


class TestRun:
    def test_success(self):
        result = _run(["echo", "hello"])
        assert result.strip() == "hello"

    def test_timeout(self):
        result = _run(["sleep", "10"], timeout=1)
        assert result is None

    def test_missing_command(self):
        result = _run(["nonexistent_command_xyz"])
        assert result is None


class TestDuKb:
    def test_nonexistent_path(self):
        assert _du_kb("/nonexistent/path/xyz") == 0

    @patch("os.path.exists", return_value=True)
    @patch("scanner._run")
    def test_valid_output(self, mock_run, mock_exists):
        mock_run.return_value = "12345\t/some/path\n"
        assert _du_kb("/some/path") == 12345

    @patch("scanner._run")
    def test_empty_output(self, mock_run):
        mock_run.return_value = None
        assert _du_kb("/some/path") == 0

    @patch("scanner._run")
    def test_malformed_output(self, mock_run):
        mock_run.return_value = "not a number\n"
        assert _du_kb("/some/path") == 0


class TestDuKbList:
    @patch("scanner._du_kb")
    def test_sums_correctly(self, mock_du):
        mock_du.side_effect = [100, 200, 300]
        result = _du_kb_list(["/a", "/b", "/c"])
        assert result == 600

    @patch("scanner._du_kb")
    def test_empty_list(self, mock_du):
        assert _du_kb_list([]) == 0


class TestScanDiskOverview:
    @patch("scanner._run")
    def test_parses_df_output(self, mock_run):
        mock_run.return_value = (
            "Filesystem  1024-blocks      Used Available Capacity iused ifree %iused Mounted on\n"
            "/dev/disk1  976562500 488281250 488281250    50% 1000 999000  0%   /\n"
        )
        result = scan_disk_overview()
        assert result["total_gb"] == pytest.approx(976562500 / (1024 * 1024), rel=0.01)
        assert result["used_pct"] == pytest.approx(50.0, abs=0.1)

    @patch("scanner._run")
    def test_handles_failure(self, mock_run):
        mock_run.return_value = None
        result = scan_disk_overview()
        assert result["total_gb"] == 0


class TestScanDocker:
    @patch("scanner._run")
    def test_docker_not_installed(self, mock_run):
        mock_run.return_value = None
        result = scan_docker()
        assert result["available"] is False
        assert result["total_kb"] == 0

    @patch("scanner._run")
    def test_parses_docker_output(self, mock_run):
        mock_run.return_value = (
            '{"Type":"Images","TotalCount":"5","Active":"2","Size":"2.5GB","Reclaimable":"1.2GB (48%)"}\n'
            '{"Type":"Containers","TotalCount":"3","Active":"1","Size":"500MB","Reclaimable":"200MB (40%)"}\n'
        )
        result = scan_docker()
        assert result["available"] is True
        assert result["total_kb"] > 0
        assert "Images" in result["details"]
        assert "Containers" in result["details"]


class TestScanNodeModules:
    @patch("scanner._du_kb")
    @patch("scanner._run")
    def test_finds_modules(self, mock_run, mock_du):
        mock_run.return_value = "/project1/node_modules\n/project2/node_modules\n"
        mock_du.side_effect = [500000, 300000]
        result = scan_node_modules("/fake/base")
        assert len(result) == 2
        assert result[0]["size_kb"] >= result[1]["size_kb"]

    @patch("scanner._run")
    def test_no_modules_found(self, mock_run):
        mock_run.return_value = ""
        result = scan_node_modules("/fake/base")
        assert result == []


class TestScanPythonVenvs:
    @patch("scanner._du_kb")
    @patch("scanner._run")
    def test_finds_venvs(self, mock_run, mock_du):
        mock_run.return_value = "/project1/.venv/pyvenv.cfg\n/project2/venv/pyvenv.cfg\n"
        mock_du.side_effect = [200000, 150000]
        result = scan_python_venvs("/fake/base")
        assert len(result) == 2

    @patch("scanner._run")
    def test_deduplicates(self, mock_run):
        mock_run.return_value = ""
        result = scan_python_venvs("/fake/base")
        assert result == []


class TestScanMlModels:
    @patch("scanner._run")
    def test_no_models(self, mock_run):
        mock_run.return_value = None
        result = scan_ml_models("/fake/base")
        assert result == []


class TestScanTopProjects:
    def test_nonexistent_dir(self):
        result = scan_top_projects("/nonexistent/dir/xyz")
        assert result == []

    @patch("scanner._du_kb")
    @patch("os.listdir")
    @patch("os.path.isdir")
    @patch("os.path.exists")
    def test_returns_sorted(self, mock_exists, mock_isdir, mock_listdir, mock_du):
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = ["proj_a", "proj_b", "proj_c"]
        mock_du.side_effect = [100, 300, 200]
        result = scan_top_projects("/fake/projects", top_n=2)
        assert len(result) == 2
        assert result[0]["size_kb"] >= result[1]["size_kb"]


class TestRunScan:
    @patch("scanner.scan_top_projects")
    @patch("scanner.scan_ml_models")
    @patch("scanner.scan_python_venvs")
    @patch("scanner.scan_node_modules")
    @patch("scanner.scan_docker")
    @patch("scanner.scan_disk_overview")
    @patch("scanner._du_kb")
    def test_returns_all_categories(
        self, mock_du, mock_disk, mock_docker, mock_node, mock_venv, mock_ml, mock_proj
    ):
        mock_disk.return_value = {"total_gb": 500, "used_gb": 250, "free_gb": 250, "used_pct": 50}
        mock_docker.return_value = {"available": False, "total_kb": 0, "reclaimable_kb": 0, "details": {}}
        mock_node.return_value = []
        mock_venv.return_value = []
        mock_ml.return_value = []
        mock_proj.return_value = []
        mock_du.return_value = 0

        result = run_scan("/fake/home")
        assert "disk" in result
        assert "docker" in result
        assert "node_modules" in result
        assert "python_venv" in result
        assert "ml_models" in result
        assert "caches" in result
        assert "trash" in result
        assert "downloads" in result
        assert "projects" in result

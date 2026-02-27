"""Tests for recommender module."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recommender import generate_recommendations


def _make_scan_results(**overrides):
    """Create minimal scan results for testing."""
    base = {
        "caches": {"total_kb": 0},
        "docker": {"available": False, "total_kb": 0, "reclaimable_kb": 0},
        "node_modules": {"total_kb": 0},
        "python_venv": {"total_kb": 0},
        "xcode_dev": {"total_kb": 0},
        "logs": {"total_kb": 0},
        "trash": {"total_kb": 0},
        "ml_models": {"total_kb": 0},
        "downloads": {"total_kb": 0},
        "projects": {"total_kb": 0},
    }
    base.update(overrides)
    return base


class TestGenerateRecommendations:
    def test_empty_scan(self):
        results = _make_scan_results()
        recs = generate_recommendations(results)
        assert recs == []

    def test_sorted_by_size(self):
        results = _make_scan_results(
            caches={"total_kb": 1024 * 1024},       # 1 GB
            trash={"total_kb": 2 * 1024 * 1024},     # 2 GB
            logs={"total_kb": 512 * 1024},            # 0.5 GB
        )
        recs = generate_recommendations(results)
        sizes = [r["size_gb"] for r in recs]
        assert sizes == sorted(sizes, reverse=True)

    def test_safe_flag_on_caches(self):
        results = _make_scan_results(caches={"total_kb": 1024 * 1024})
        recs = generate_recommendations(results)
        cache_rec = next(r for r in recs if r["category"] == "caches")
        assert cache_rec["safe"] is True

    def test_safe_flag_on_trash(self):
        results = _make_scan_results(trash={"total_kb": 1024 * 1024})
        recs = generate_recommendations(results)
        trash_rec = next(r for r in recs if r["category"] == "trash")
        assert trash_rec["safe"] is True

    def test_unsafe_flag_on_ml_models(self):
        results = _make_scan_results(ml_models={"total_kb": 5 * 1024 * 1024})
        recs = generate_recommendations(results)
        ml_rec = next(r for r in recs if r["category"] == "ml_models")
        assert ml_rec["safe"] is False

    def test_unsafe_flag_on_downloads(self):
        results = _make_scan_results(downloads={"total_kb": 1024 * 1024})
        recs = generate_recommendations(results)
        dl_rec = next(r for r in recs if r["category"] == "downloads")
        assert dl_rec["safe"] is False

    def test_docker_uses_reclaimable(self):
        results = _make_scan_results(
            docker={"available": True, "total_kb": 10 * 1024 * 1024, "reclaimable_kb": 3 * 1024 * 1024}
        )
        recs = generate_recommendations(results)
        docker_rec = next(r for r in recs if r["category"] == "docker")
        assert docker_rec["size_gb"] == 3.0
        assert docker_rec["safe"] is True

    def test_docker_falls_back_to_total(self):
        results = _make_scan_results(
            docker={"available": True, "total_kb": 5 * 1024 * 1024, "reclaimable_kb": 0}
        )
        recs = generate_recommendations(results)
        docker_rec = next(r for r in recs if r["category"] == "docker")
        assert docker_rec["size_gb"] == 5.0

    def test_docker_unavailable_skipped(self):
        results = _make_scan_results(
            docker={"available": False, "total_kb": 0, "reclaimable_kb": 0}
        )
        recs = generate_recommendations(results)
        docker_recs = [r for r in recs if r["category"] == "docker"]
        assert docker_recs == []

    def test_zero_size_excluded(self):
        results = _make_scan_results(
            caches={"total_kb": 0},
            trash={"total_kb": 1024 * 1024},
        )
        recs = generate_recommendations(results)
        categories = [r["category"] for r in recs]
        assert "caches" not in categories
        assert "trash" in categories

    def test_all_recs_have_required_fields(self):
        results = _make_scan_results(
            caches={"total_kb": 1024 * 1024},
            trash={"total_kb": 512 * 1024},
            node_modules={"total_kb": 2 * 1024 * 1024},
        )
        recs = generate_recommendations(results)
        for rec in recs:
            assert "category" in rec
            assert "label" in rec
            assert "size_gb" in rec
            assert "action" in rec
            assert "command" in rec
            assert "safe" in rec
            assert isinstance(rec["safe"], bool)
            assert isinstance(rec["size_gb"], float)

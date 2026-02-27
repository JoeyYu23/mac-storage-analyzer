"""
Disk scanning engine for Mac Storage Analyzer.
Collects sizes for all tracked categories using du, find, and subprocess.
"""

import os
import subprocess
import json
from typing import Optional

HOME = os.path.expanduser("~")


def _run(cmd: list[str], timeout: int = 30) -> Optional[str]:
    """Run a subprocess command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        return None


def _du_kb(path: str) -> int:
    """Return size of path in kilobytes using du -sk. Returns 0 on error."""
    if not os.path.exists(path):
        return 0
    out = _run(["du", "-sk", path], timeout=60)
    if not out:
        return 0
    try:
        return int(out.split()[0])
    except (IndexError, ValueError):
        return 0


def _du_kb_list(paths: list[str]) -> int:
    """Sum du -sk sizes for a list of paths."""
    total = 0
    for p in paths:
        total += _du_kb(p)
    return total


def kb_to_gb(kb: int) -> float:
    """Convert kilobytes to gigabytes."""
    return kb / (1024 * 1024)


def scan_disk_overview() -> dict:
    """Get overall disk usage via df -h /."""
    out = _run(["df", "-k", "/"])
    if not out:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "used_pct": 0}

    lines = out.strip().splitlines()
    if len(lines) < 2:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "used_pct": 0}

    # df -k fields: Filesystem 1024-blocks Used Available Capacity iused ifree %iused Mounted
    parts = lines[1].split()
    try:
        total_kb = int(parts[1])
        used_kb = int(parts[2])
        free_kb = int(parts[3])
        used_pct = round(used_kb / total_kb * 100, 1) if total_kb > 0 else 0
        return {
            "total_gb": kb_to_gb(total_kb),
            "used_gb": kb_to_gb(used_kb),
            "free_gb": kb_to_gb(free_kb),
            "used_pct": used_pct,
        }
    except (IndexError, ValueError):
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "used_pct": 0}


def scan_docker() -> dict:
    """Scan Docker disk usage via docker system df."""
    out = _run(["docker", "system", "df", "--format", "{{json .}}"], timeout=15)
    if out is None:
        return {"available": False, "total_kb": 0, "reclaimable_kb": 0, "details": {}}

    # docker system df --format json outputs one JSON object per line (not a JSON array)
    total_kb = 0
    reclaimable_kb = 0
    details = {}

    for line in out.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            type_name = item.get("Type", "")
            size_str = item.get("Size", "0B")
            reclaimable_str = item.get("Reclaimable", "0B")
            size_kb = _parse_docker_size(size_str)
            reclaimable_raw = reclaimable_str.split(" ")[0]  # "5.2GB (30%)" -> "5.2GB"
            reclaimable_item_kb = _parse_docker_size(reclaimable_raw)
            total_kb += size_kb
            reclaimable_kb += reclaimable_item_kb
            details[type_name] = {
                "size_kb": size_kb,
                "reclaimable_kb": reclaimable_item_kb,
            }
        except (json.JSONDecodeError, KeyError):
            continue

    return {
        "available": True,
        "total_kb": total_kb,
        "reclaimable_kb": reclaimable_kb,
        "details": details,
    }


def _parse_docker_size(size_str: str) -> int:
    """Parse Docker size strings like '8.2GB', '512MB', '1.5TB' to KB."""
    size_str = size_str.strip()
    if not size_str or size_str == "0B":
        return 0
    # Check longest suffixes first to avoid "GB".endswith("B") matching "B"
    multipliers = [
        ("TB", 1024 * 1024 * 1024),
        ("GB", 1024 * 1024),
        ("MB", 1024),
        ("KB", 1),
        ("kB", 1),
        ("B", 1 / 1024),
    ]
    for suffix, mult in multipliers:
        if size_str.endswith(suffix):
            try:
                value = float(size_str[: -len(suffix)])
                return int(value * mult)
            except ValueError:
                return 0
    return 0


def scan_node_modules(base_path: str) -> list[dict]:
    """Find node_modules directories up to depth 6."""
    out = _run(
        [
            "find",
            base_path,
            "-name",
            "node_modules",
            "-type",
            "d",
            "-prune",
            "-maxdepth",
            "6",
        ],
        timeout=60,
    )
    if not out:
        return []

    results = []
    for path in out.strip().splitlines():
        path = path.strip()
        if not path:
            continue
        size_kb = _du_kb(path)
        results.append({"path": path, "size_kb": size_kb})

    return sorted(results, key=lambda x: x["size_kb"], reverse=True)


def scan_python_venvs(base_path: str) -> list[dict]:
    """Find Python virtual environments by locating pyvenv.cfg files."""
    out = _run(
        [
            "find",
            base_path,
            "-name",
            "pyvenv.cfg",
            "-maxdepth",
            "8",
        ],
        timeout=60,
    )
    if not out:
        return []

    results = []
    seen = set()
    for cfg_path in out.strip().splitlines():
        cfg_path = cfg_path.strip()
        if not cfg_path:
            continue
        venv_dir = os.path.dirname(cfg_path)
        if venv_dir in seen:
            continue
        seen.add(venv_dir)
        size_kb = _du_kb(venv_dir)
        results.append({"path": venv_dir, "size_kb": size_kb})

    return sorted(results, key=lambda x: x["size_kb"], reverse=True)


def scan_ml_models(base_path: str) -> list[dict]:
    """Find large ML model files (>100MB) with common extensions."""
    extensions = [".pt", ".pkl", ".h5", ".ckpt", ".safetensors", ".bin"]
    results = []

    for ext in extensions:
        out = _run(
            [
                "find",
                base_path,
                "-name",
                f"*{ext}",
                "-type",
                "f",
                "-size",
                "+100M",
                "-maxdepth",
                "10",
            ],
            timeout=60,
        )
        if not out:
            continue
        for path in out.strip().splitlines():
            path = path.strip()
            if not path or not os.path.exists(path):
                continue
            try:
                size_kb = os.path.getsize(path) // 1024
            except OSError:
                size_kb = 0
            results.append({"path": path, "size_kb": size_kb, "ext": ext})

    return sorted(results, key=lambda x: x["size_kb"], reverse=True)


def scan_path(path: str) -> int:
    """Return total size in KB for a single path."""
    return _du_kb(path)


def scan_top_projects(projects_dir: str, top_n: int = 10) -> list[dict]:
    """Return the top N largest subdirectories under projects_dir."""
    if not os.path.exists(projects_dir):
        return []

    try:
        entries = [
            os.path.join(projects_dir, e)
            for e in os.listdir(projects_dir)
            if os.path.isdir(os.path.join(projects_dir, e))
        ]
    except PermissionError:
        return []

    results = []
    for entry in entries:
        size_kb = _du_kb(entry)
        results.append({"path": entry, "name": os.path.basename(entry), "size_kb": size_kb})

    return sorted(results, key=lambda x: x["size_kb"], reverse=True)[:top_n]


def run_scan(base_path: str = HOME) -> dict:
    """
    Run a full storage scan and return structured results.

    Returns a dict with keys for each category and disk overview.
    """
    results = {
        "base_path": base_path,
        "disk": scan_disk_overview(),
        "docker": scan_docker(),
        "node_modules": {
            "items": scan_node_modules(base_path),
            "total_kb": 0,
        },
        "python_venv": {
            "items": scan_python_venvs(base_path),
            "total_kb": 0,
        },
        "ml_models": {
            "items": scan_ml_models(base_path),
            "total_kb": 0,
        },
        "caches": {
            "total_kb": 0,
            "breakdown": {},
        },
        "xcode_dev": {
            "total_kb": 0,
        },
        "logs": {
            "total_kb": 0,
        },
        "trash": {
            "total_kb": 0,
        },
        "downloads": {
            "total_kb": 0,
        },
        "projects": {
            "items": [],
            "total_kb": 0,
        },
        "app_support": {
            "total_kb": 0,
        },
    }

    # Aggregate node_modules total
    results["node_modules"]["total_kb"] = sum(
        i["size_kb"] for i in results["node_modules"]["items"]
    )

    # Aggregate python venv total
    results["python_venv"]["total_kb"] = sum(
        i["size_kb"] for i in results["python_venv"]["items"]
    )

    # Aggregate ML models total
    results["ml_models"]["total_kb"] = sum(
        i["size_kb"] for i in results["ml_models"]["items"]
    )

    # Caches breakdown
    cache_paths = {
        "general": os.path.join(HOME, "Library", "Caches"),
        "npm": os.path.join(HOME, ".npm"),
        "pip": os.path.join(HOME, "Library", "Caches", "pip"),
        "homebrew": os.path.join(HOME, "Library", "Caches", "Homebrew"),
    }
    cache_total = 0
    # Scan general caches first, then individual sub-caches
    general_kb = _du_kb(cache_paths["general"])
    npm_kb = _du_kb(cache_paths["npm"])

    results["caches"]["breakdown"] = {
        "general": {"path": cache_paths["general"], "size_kb": general_kb},
        "npm": {"path": cache_paths["npm"], "size_kb": npm_kb},
    }
    cache_total = general_kb + npm_kb
    results["caches"]["total_kb"] = cache_total

    # Xcode / Developer
    xcode_path = os.path.join(HOME, "Library", "Developer")
    results["xcode_dev"]["total_kb"] = _du_kb(xcode_path)

    # Logs
    logs_path = os.path.join(HOME, "Library", "Logs")
    results["logs"]["total_kb"] = _du_kb(logs_path)

    # Trash
    trash_path = os.path.join(HOME, ".Trash")
    results["trash"]["total_kb"] = _du_kb(trash_path)

    # Downloads
    downloads_path = os.path.join(HOME, "Downloads")
    results["downloads"]["total_kb"] = _du_kb(downloads_path)

    # Projects
    projects_path = os.path.join(HOME, "Projects")
    project_items = scan_top_projects(projects_path)
    results["projects"]["items"] = project_items
    results["projects"]["total_kb"] = sum(i["size_kb"] for i in project_items)

    # App Support
    app_support_path = os.path.join(HOME, "Library", "Application Support")
    results["app_support"]["total_kb"] = _du_kb(app_support_path)

    return results

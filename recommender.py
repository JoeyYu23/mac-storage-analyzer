"""
Recommendation engine for Mac Storage Analyzer.
Generates actionable recommendations sorted by potential storage savings.
"""

from scanner import kb_to_gb


def generate_recommendations(scan_results: dict) -> list[dict]:
    """
    Given scan results, produce a sorted list of recommendations.

    Each recommendation is a dict with:
      - category: str
      - label: str
      - size_gb: float
      - action: str
      - command: str
      - safe: bool  (True = safe to delete without review)
    """
    recs = []

    # Caches (safe)
    cache_kb = scan_results.get("caches", {}).get("total_kb", 0)
    if cache_kb > 0:
        recs.append({
            "category": "caches",
            "label": "Clear all caches",
            "size_gb": kb_to_gb(cache_kb),
            "action": "Delete ~/Library/Caches and npm/pip/Homebrew caches",
            "command": "rm -rf ~/Library/Caches/* && npm cache clean --force && pip cache purge && brew cleanup",
            "safe": True,
        })

    # Docker (safe)
    docker = scan_results.get("docker", {})
    if docker.get("available") and docker.get("reclaimable_kb", 0) > 0:
        recs.append({
            "category": "docker",
            "label": "Prune Docker",
            "size_gb": kb_to_gb(docker["reclaimable_kb"]),
            "action": "Remove unused Docker images, containers, and build cache",
            "command": "docker system prune -a",
            "safe": True,
        })
    elif docker.get("available") and docker.get("total_kb", 0) > 0:
        recs.append({
            "category": "docker",
            "label": "Prune Docker",
            "size_gb": kb_to_gb(docker["total_kb"]),
            "action": "Remove unused Docker images, containers, and build cache",
            "command": "docker system prune -a",
            "safe": True,
        })

    # node_modules (safe — can restore with npm install)
    node_kb = scan_results.get("node_modules", {}).get("total_kb", 0)
    if node_kb > 0:
        recs.append({
            "category": "node_modules",
            "label": "Delete node_modules in old projects",
            "size_gb": kb_to_gb(node_kb),
            "action": "Remove node_modules directories; restore with 'npm install'",
            "command": "find ~/Projects -name node_modules -type d -prune -exec rm -rf {} +",
            "safe": True,
        })

    # Python venvs (safe — can recreate)
    venv_kb = scan_results.get("python_venv", {}).get("total_kb", 0)
    if venv_kb > 0:
        recs.append({
            "category": "python_venv",
            "label": "Remove unused Python virtual environments",
            "size_gb": kb_to_gb(venv_kb),
            "action": "Delete venv directories; recreate with 'python -m venv'",
            "command": "# Manually identify and delete: rm -rf <venv_path>",
            "safe": True,
        })

    # Xcode/Developer (review first — may need simulators)
    xcode_kb = scan_results.get("xcode_dev", {}).get("total_kb", 0)
    if xcode_kb > 0:
        recs.append({
            "category": "xcode_dev",
            "label": "Clean Xcode derived data and simulators",
            "size_gb": kb_to_gb(xcode_kb),
            "action": "Delete DerivedData; remove unused simulators via Xcode",
            "command": "rm -rf ~/Library/Developer/Xcode/DerivedData",
            "safe": False,
        })

    # Logs (safe)
    logs_kb = scan_results.get("logs", {}).get("total_kb", 0)
    if logs_kb > 0:
        recs.append({
            "category": "logs",
            "label": "Clear application logs",
            "size_gb": kb_to_gb(logs_kb),
            "action": "Delete old log files in ~/Library/Logs",
            "command": "rm -rf ~/Library/Logs/*",
            "safe": True,
        })

    # Trash (safe)
    trash_kb = scan_results.get("trash", {}).get("total_kb", 0)
    if trash_kb > 0:
        recs.append({
            "category": "trash",
            "label": "Empty the Trash",
            "size_gb": kb_to_gb(trash_kb),
            "action": "Permanently delete files in ~/.Trash",
            "command": "rm -rf ~/.Trash/*",
            "safe": True,
        })

    # ML models (review — may not be re-downloadable)
    ml_kb = scan_results.get("ml_models", {}).get("total_kb", 0)
    if ml_kb > 0:
        recs.append({
            "category": "ml_models",
            "label": "Review large ML model files",
            "size_gb": kb_to_gb(ml_kb),
            "action": "Check and delete unused model weights/checkpoints",
            "command": "# Manually review model files before deleting",
            "safe": False,
        })

    # Downloads (review)
    downloads_kb = scan_results.get("downloads", {}).get("total_kb", 0)
    if downloads_kb > 0:
        recs.append({
            "category": "downloads",
            "label": "Clean up Downloads folder",
            "size_gb": kb_to_gb(downloads_kb),
            "action": "Review and delete files in ~/Downloads",
            "command": "# Manually review ~/Downloads",
            "safe": False,
        })

    # Projects (review)
    projects_kb = scan_results.get("projects", {}).get("total_kb", 0)
    if projects_kb > 0:
        recs.append({
            "category": "projects",
            "label": "Archive or delete old projects",
            "size_gb": kb_to_gb(projects_kb),
            "action": "Review ~/Projects and remove projects no longer in use",
            "command": "# Manually review ~/Projects subdirectories",
            "safe": False,
        })

    # Sort by size descending (biggest savings first)
    return sorted(recs, key=lambda r: r["size_gb"], reverse=True)

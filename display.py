"""
Terminal display module using Rich for colored output.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text
from rich import box

from scanner import kb_to_gb

console = Console()


def _fmt_gb(gb: float) -> str:
    """Format a GB value to a human-readable string."""
    if gb < 0.1:
        return "< 0.1 GB"
    return f"{gb:.1f} GB"


def _disk_bar(used_gb: float, total_gb: float, width: int = 40) -> str:
    """Return an ASCII progress bar string for disk usage."""
    if total_gb <= 0:
        return "[" + "-" * width + "]"
    ratio = min(used_gb / total_gb, 1.0)
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    return bar


def render_disk_overview(disk: dict) -> None:
    """Render the disk overview panel."""
    used = disk["used_gb"]
    total = disk["total_gb"]
    free = disk["free_gb"]
    pct = disk["used_pct"]

    bar = _disk_bar(used, total, width=36)

    # Color the bar: green < 60%, yellow 60-80%, red > 80%
    if pct < 60:
        bar_style = "green"
    elif pct < 80:
        bar_style = "yellow"
    else:
        bar_style = "red"

    text = Text()
    text.append(f"  Disk Usage: ", style="bold")
    text.append(f"{_fmt_gb(used)}", style="bold white")
    text.append(f" used of ", style="dim")
    text.append(f"{_fmt_gb(total)}", style="bold white")
    text.append(f" total\n", style="dim")
    text.append(f"  Free: ", style="bold")
    text.append(f"{_fmt_gb(free)}", style="bold green")
    text.append(f"  ({100 - pct:.0f}% free)\n\n", style="dim")
    text.append(f"  [", style="dim")
    text.append(bar, style=bar_style)
    text.append(f"]  {pct:.0f}% used", style="dim")

    console.print(
        Panel(
            text,
            title="[bold cyan]Mac Storage Analyzer[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
    )


def render_category_table(scan_results: dict) -> None:
    """Render a table of storage categories and their sizes."""
    table = Table(
        title="[bold]Category Breakdown[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        border_style="bright_black",
        padding=(0, 1),
    )
    table.add_column("Category", style="bold", min_width=20)
    table.add_column("Size", justify="right", min_width=10)
    table.add_column("Status", min_width=12)
    table.add_column("Recommendation", min_width=38)

    rows = _build_category_rows(scan_results)

    for row in rows:
        size_gb = row["size_gb"]
        if size_gb < 0.05:
            continue  # Skip near-zero entries

        size_str = _fmt_gb(size_gb)
        if row["safe"]:
            status = Text("SAFE", style="bold red")
            size_style = "red"
        elif row["can_delete"]:
            status = Text("REVIEW", style="bold yellow")
            size_style = "yellow"
        else:
            status = Text("KEEP", style="bold green")
            size_style = "green"

        table.add_row(
            f"{row['emoji']} {row['name']}",
            Text(size_str, style=size_style),
            status,
            row["recommendation"],
        )

    console.print()
    console.print(table)


def _build_category_rows(scan_results: dict) -> list[dict]:
    """Extract display rows from scan results."""
    rows = []

    # Docker
    docker = scan_results.get("docker", {})
    if docker.get("available"):
        rows.append({
            "name": "Docker",
            "emoji": "🐳",
            "size_gb": kb_to_gb(docker.get("total_kb", 0)),
            "safe": True,
            "can_delete": True,
            "recommendation": "docker system prune -a",
        })

    # node_modules
    node_kb = scan_results.get("node_modules", {}).get("total_kb", 0)
    rows.append({
        "name": "node_modules",
        "emoji": "📦",
        "size_gb": kb_to_gb(node_kb),
        "safe": True,
        "can_delete": True,
        "recommendation": "find & delete, restore with npm install",
    })

    # Python venvs
    venv_kb = scan_results.get("python_venv", {}).get("total_kb", 0)
    rows.append({
        "name": "Python venvs",
        "emoji": "🐍",
        "size_gb": kb_to_gb(venv_kb),
        "safe": True,
        "can_delete": True,
        "recommendation": "remove unused venvs",
    })

    # ML Models
    ml_kb = scan_results.get("ml_models", {}).get("total_kb", 0)
    rows.append({
        "name": "ML Models",
        "emoji": "🤖",
        "size_gb": kb_to_gb(ml_kb),
        "safe": False,
        "can_delete": False,
        "recommendation": "review model files before deleting",
    })

    # Caches
    cache_kb = scan_results.get("caches", {}).get("total_kb", 0)
    rows.append({
        "name": "Caches",
        "emoji": "💾",
        "size_gb": kb_to_gb(cache_kb),
        "safe": True,
        "can_delete": True,
        "recommendation": "rm -rf ~/Library/Caches/*",
    })

    # Xcode/Dev
    xcode_kb = scan_results.get("xcode_dev", {}).get("total_kb", 0)
    rows.append({
        "name": "Xcode/Dev",
        "emoji": "🛠",
        "size_gb": kb_to_gb(xcode_kb),
        "safe": False,
        "can_delete": False,
        "recommendation": "Xcode > Settings > Platforms",
    })

    # App Support
    app_kb = scan_results.get("app_support", {}).get("total_kb", 0)
    rows.append({
        "name": "App Support",
        "emoji": "🔧",
        "size_gb": kb_to_gb(app_kb),
        "safe": False,
        "can_delete": False,
        "recommendation": "review uninstalled app data",
    })

    # Logs
    logs_kb = scan_results.get("logs", {}).get("total_kb", 0)
    rows.append({
        "name": "Logs",
        "emoji": "📋",
        "size_gb": kb_to_gb(logs_kb),
        "safe": True,
        "can_delete": True,
        "recommendation": "rm -rf ~/Library/Logs/*",
    })

    # Trash
    trash_kb = scan_results.get("trash", {}).get("total_kb", 0)
    rows.append({
        "name": "Trash",
        "emoji": "🗑",
        "size_gb": kb_to_gb(trash_kb),
        "safe": True,
        "can_delete": True,
        "recommendation": "Empty Trash in Finder",
    })

    # Downloads
    downloads_kb = scan_results.get("downloads", {}).get("total_kb", 0)
    rows.append({
        "name": "Downloads",
        "emoji": "⬇️",
        "size_gb": kb_to_gb(downloads_kb),
        "safe": False,
        "can_delete": False,
        "recommendation": "review ~/Downloads manually",
    })

    # Projects
    projects_kb = scan_results.get("projects", {}).get("total_kb", 0)
    rows.append({
        "name": "Projects",
        "emoji": "🗂",
        "size_gb": kb_to_gb(projects_kb),
        "safe": False,
        "can_delete": False,
        "recommendation": "archive or delete old projects",
    })

    # Sort by size descending
    return sorted(rows, key=lambda r: r["size_gb"], reverse=True)


def render_top_projects(scan_results: dict) -> None:
    """Render top projects by size."""
    items = scan_results.get("projects", {}).get("items", [])
    if not items:
        return

    table = Table(
        title="[bold]Top Projects by Size[/bold]",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold blue",
        border_style="bright_black",
        padding=(0, 1),
    )
    table.add_column("#", justify="right", min_width=3)
    table.add_column("Project", min_width=30)
    table.add_column("Size", justify="right", min_width=10)

    for i, item in enumerate(items[:10], start=1):
        size_gb = kb_to_gb(item["size_kb"])
        table.add_row(str(i), item["name"], _fmt_gb(size_gb))

    console.print()
    console.print(table)


def render_node_modules(scan_results: dict) -> None:
    """Render found node_modules directories."""
    items = scan_results.get("node_modules", {}).get("items", [])
    if not items:
        return

    table = Table(
        title="[bold]node_modules Directories[/bold]",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold blue",
        border_style="bright_black",
        padding=(0, 1),
    )
    table.add_column("Path", min_width=50)
    table.add_column("Size", justify="right", min_width=10)

    for item in items[:15]:
        size_gb = kb_to_gb(item["size_kb"])
        table.add_row(item["path"], _fmt_gb(size_gb))

    console.print()
    console.print(table)


def render_recommendations(recommendations: list[dict]) -> None:
    """Render prioritized recommendations."""
    if not recommendations:
        console.print("\n[green]No major cleanup recommendations.[/green]")
        return

    total_safe_gb = sum(r["size_gb"] for r in recommendations if r["safe"])
    total_review_gb = sum(r["size_gb"] for r in recommendations if not r["safe"])

    console.print()
    console.print(
        Panel(
            f"[bold]Potential savings:[/bold]  "
            f"[red]{_fmt_gb(total_safe_gb)} safe to delete[/red]  +  "
            f"[yellow]{_fmt_gb(total_review_gb)} after review[/yellow]  "
            f"= [bold white]{_fmt_gb(total_safe_gb + total_review_gb)} total[/bold white]",
            title="[bold yellow]Recommendations (by savings)[/bold yellow]",
            border_style="yellow",
        )
    )

    for i, rec in enumerate(recommendations, start=1):
        if rec["safe"]:
            tag = Text("[SAFE] ", style="bold red")
            cmd_style = "red"
        else:
            tag = Text("[REVIEW] ", style="bold yellow")
            cmd_style = "yellow"

        console.print()
        line = Text()
        line.append(f"{i}. ", style="bold white")
        line.append_text(tag)
        line.append(rec["label"], style="bold")
        line.append(f": saves {_fmt_gb(rec['size_gb'])}", style="dim")
        console.print(line)
        console.print(f"   [dim]{rec['action']}[/dim]")
        console.print(f"   [bold {cmd_style}]→ {rec['command']}[/bold {cmd_style}]")


def render_legend() -> None:
    """Print color legend."""
    console.print()
    legend = Text()
    legend.append("Legend:  ", style="dim")
    legend.append("■ SAFE", style="bold red")
    legend.append(" = safe to delete now   ", style="dim")
    legend.append("■ REVIEW", style="bold yellow")
    legend.append(" = check before deleting   ", style="dim")
    legend.append("■ KEEP", style="bold green")
    legend.append(" = do not delete", style="dim")
    console.print(legend)


def render_full_report(scan_results: dict, recommendations: list[dict]) -> None:
    """Render the complete report to the terminal."""
    render_disk_overview(scan_results["disk"])
    render_category_table(scan_results)
    render_top_projects(scan_results)
    render_node_modules(scan_results)
    render_recommendations(recommendations)
    render_legend()
    console.print()

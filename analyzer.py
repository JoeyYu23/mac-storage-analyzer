#!/usr/bin/env python3
"""
Mac Storage Analyzer — main CLI entry point.

Usage:
  python analyzer.py scan                   # Full scan with colored report
  python analyzer.py scan --path ~/Projects # Scan specific directory
  python analyzer.py scan --json            # Output JSON
  python analyzer.py report                 # Alias for scan
"""

import argparse
import json
import sys
import os


def cmd_scan(args: argparse.Namespace) -> None:
    """Run a full storage scan and display results."""
    base_path = os.path.expanduser(args.path)

    if not os.path.isdir(base_path):
        print(f"Error: '{base_path}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    if not args.json:
        from rich.console import Console
        from rich.spinner import Spinner
        from rich.live import Live
        import time

        console = Console()
        console.print(
            f"\n[cyan]Scanning [bold]{base_path}[/bold] — this may take a minute...[/cyan]\n"
        )

    from scanner import run_scan
    scan_results = run_scan(base_path)

    from recommender import generate_recommendations
    recommendations = generate_recommendations(scan_results)

    if args.json:
        # Build JSON-serializable output
        output = {
            "scan_path": base_path,
            "disk": scan_results["disk"],
            "categories": {
                "docker": {
                    "available": scan_results["docker"].get("available", False),
                    "total_gb": scan_results["docker"].get("total_kb", 0) / (1024 * 1024),
                },
                "node_modules": {
                    "total_gb": scan_results["node_modules"]["total_kb"] / (1024 * 1024),
                    "count": len(scan_results["node_modules"]["items"]),
                },
                "python_venv": {
                    "total_gb": scan_results["python_venv"]["total_kb"] / (1024 * 1024),
                    "count": len(scan_results["python_venv"]["items"]),
                },
                "ml_models": {
                    "total_gb": scan_results["ml_models"]["total_kb"] / (1024 * 1024),
                    "count": len(scan_results["ml_models"]["items"]),
                },
                "caches_gb": scan_results["caches"]["total_kb"] / (1024 * 1024),
                "xcode_dev_gb": scan_results["xcode_dev"]["total_kb"] / (1024 * 1024),
                "logs_gb": scan_results["logs"]["total_kb"] / (1024 * 1024),
                "trash_gb": scan_results["trash"]["total_kb"] / (1024 * 1024),
                "downloads_gb": scan_results["downloads"]["total_kb"] / (1024 * 1024),
                "projects_gb": scan_results["projects"]["total_kb"] / (1024 * 1024),
                "app_support_gb": scan_results["app_support"]["total_kb"] / (1024 * 1024),
            },
            "recommendations": recommendations,
        }
        print(json.dumps(output, indent=2))
    else:
        from display import render_full_report
        render_full_report(scan_results, recommendations)


def cmd_report(args: argparse.Namespace) -> None:
    """Alias for scan — display the storage report."""
    cmd_scan(args)


def cmd_clean(args: argparse.Namespace) -> None:
    """Print cleanup commands for safe categories."""
    base_path = os.path.expanduser(args.path)

    from rich.console import Console
    console = Console()
    console.print("\n[yellow]Generating safe cleanup commands...[/yellow]\n")

    from scanner import run_scan
    scan_results = run_scan(base_path)

    from recommender import generate_recommendations
    recommendations = generate_recommendations(scan_results)

    safe_recs = [r for r in recommendations if r["safe"]]

    if not safe_recs:
        console.print("[green]Nothing safe to clean up![/green]")
        return

    console.print("[bold]Safe cleanup commands (review before running):[/bold]\n")
    for i, rec in enumerate(safe_recs, start=1):
        from scanner import kb_to_gb
        size = kb_to_gb(0)  # placeholder
        console.print(f"[bold]{i}. {rec['label']}[/bold] ({rec['size_gb']:.1f} GB)")
        console.print(f"   [red]{rec['command']}[/red]\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="analyzer",
        description="Mac Storage Analyzer — find and reclaim disk space",
    )
    parser.add_argument(
        "--path",
        default="~",
        help="Root path to scan (default: ~)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON instead of rich terminal display",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan disk and show report")
    scan_parser.add_argument(
        "--path",
        default="~",
        help="Root path to scan (default: ~)",
    )
    scan_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON",
    )

    # report command (alias)
    report_parser = subparsers.add_parser("report", help="Alias for scan")
    report_parser.add_argument(
        "--path",
        default="~",
        help="Root path to scan (default: ~)",
    )
    report_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON",
    )

    # clean command
    clean_parser = subparsers.add_parser(
        "clean", help="Show safe cleanup commands"
    )
    clean_parser.add_argument(
        "--path",
        default="~",
        help="Root path to scan (default: ~)",
    )

    args = parser.parse_args()

    if args.command in ("scan", None):
        cmd_scan(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "clean":
        cmd_clean(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

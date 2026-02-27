# CLAUDE.md

## Project

Mac Storage Analyzer — CLI tool that scans macOS disk usage by developer-specific categories and gives actionable cleanup recommendations.

## Architecture

```
analyzer.py      CLI entry point (argparse → cmd_scan/cmd_report/cmd_clean)
scanner.py       Disk scanning engine (du, find, docker system df)
display.py       Rich terminal output (tables, panels, progress bars)
recommender.py   Recommendation engine (sorted by savings, safe/review labels)
```

## Key Patterns

- All sizes stored as kilobytes (int) internally, converted to GB at display time
- `scanner.run_scan()` returns a dict with all category data
- `recommender.generate_recommendations()` takes scan results, returns sorted list
- Subprocess calls use `_run()` wrapper with timeout and error handling
- Two output modes: Rich terminal (default) and JSON (`--json` flag)

## Commands

```bash
python analyzer.py scan              # Full scan
python analyzer.py scan --json       # JSON output
python analyzer.py scan --path ~/X   # Scan specific path
python analyzer.py clean             # Show safe cleanup commands
```

## Testing

```bash
python -m pytest tests/ -v
```

## Dependencies

- Python 3.10+
- rich>=13.0.0
- macOS (uses du, find, df, optionally docker)

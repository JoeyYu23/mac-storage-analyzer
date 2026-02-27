# mac-storage-analyzer

A developer-aware Mac storage analyzer. Identifies what's eating your disk and gives actionable cleanup recommendations — Docker layers, node_modules, Python venvs, ML checkpoints, caches, and more.

## Features

- Categorizes storage by developer-specific types (Docker, npm, venv, models, caches, Xcode)
- Gives specific, actionable recommendations per category
- Ranks by potential savings — biggest wins first
- Fast CLI with colored output + JSON mode for scripting

## Usage

```bash
python analyzer.py scan              # Full disk scan with colored report
python analyzer.py scan --json       # JSON output (for scripts / AI consumption)
python analyzer.py scan --path ~/Projects  # Scan specific directory
python analyzer.py clean             # Show safe cleanup commands
python analyzer.py report            # Alias for scan
```

## Install

```bash
git clone https://github.com/JoeyYu23/mac-storage-analyzer
cd mac-storage-analyzer
pip install -e .
```

Or without packaging:

```bash
pip install -r requirements.txt
python analyzer.py scan
```

## Architecture

```
analyzer.py      CLI entry point (argparse)
scanner.py       Disk scanning engine (du, find, docker, df)
display.py       Rich terminal output (tables, panels, bars)
recommender.py   Recommendation engine (ranked by savings)
```

## Requirements

- Python 3.10+
- macOS (uses `du`, `find`, `df` commands)
- Optional: Docker CLI (for Docker storage scanning)

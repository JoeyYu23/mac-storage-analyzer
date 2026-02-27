# mac-storage-analyzer

A developer-aware Mac storage analyzer. Identifies what's eating your disk and gives actionable cleanup recommendations — Docker layers, node_modules, Python venvs, ML checkpoints, caches, and more.

## Features

- Categorizes storage by developer-specific types (Docker, npm, venv, models, caches, git)
- Gives specific, actionable recommendations per category
- Fast CLI with colored output + JSON mode
- Optional web dashboard

## Usage

```bash
python analyzer.py scan          # Full disk scan
python analyzer.py scan --json   # JSON output
python analyzer.py clean docker  # Show Docker cleanup commands
python analyzer.py report        # Summary with recommendations
```

## Install

```bash
git clone https://github.com/JoeyYu23/mac-storage-analyzer
cd mac-storage-analyzer
pip install -r requirements.txt
```

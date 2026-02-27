"""
Category definitions for Mac storage types.
Each category has metadata about what it is and how to handle it.
"""

import os

HOME = os.path.expanduser("~")

CATEGORIES = {
    "docker": {
        "name": "Docker",
        "emoji": "🐳",
        "description": "Docker images, containers, volumes, and build cache",
        "paths": [],  # Scanned via docker system df
        "can_delete": True,
        "recommendation": "Run 'docker system prune -a' to remove unused images and containers",
        "command": "docker system prune -a",
    },
    "node_modules": {
        "name": "node_modules",
        "emoji": "📦",
        "description": "Node.js dependency directories from JavaScript/TypeScript projects",
        "paths": [],  # Discovered by find
        "can_delete": True,
        "recommendation": "Delete node_modules in old projects; restore with 'npm install'",
        "command": "find ~/Projects -name node_modules -type d -prune -exec rm -rf {} +",
    },
    "python_venv": {
        "name": "Python venvs",
        "emoji": "🐍",
        "description": "Python virtual environments (venv, virtualenv, conda envs)",
        "paths": [],  # Discovered by find pyvenv.cfg
        "can_delete": True,
        "recommendation": "Remove unused Python virtual environments; recreate with 'python -m venv'",
        "command": "# Manually review and delete unused venv directories",
    },
    "ml_models": {
        "name": "ML Models",
        "emoji": "🤖",
        "description": "Machine learning model weights and checkpoints (.pt, .pkl, .h5, .ckpt, .safetensors, .bin)",
        "paths": [],  # Discovered by find
        "can_delete": False,
        "recommendation": "Review large model files; re-download from HuggingFace/PyTorch Hub if needed",
        "command": "# Review model files before deleting — may not be re-downloadable",
    },
    "caches": {
        "name": "Caches",
        "emoji": "💾",
        "description": "Application caches, npm cache, pip cache, Homebrew cache",
        "paths": [
            os.path.join(HOME, "Library", "Caches"),
            os.path.join(HOME, ".npm"),
            os.path.join(HOME, "Library", "Caches", "pip"),
            os.path.join(HOME, "Library", "Caches", "Homebrew"),
        ],
        "can_delete": True,
        "recommendation": "Clear caches — apps will rebuild them as needed",
        "command": "rm -rf ~/Library/Caches/* && npm cache clean --force && pip cache purge && brew cleanup",
    },
    "xcode_dev": {
        "name": "Xcode/Dev",
        "emoji": "🛠",
        "description": "Xcode derived data, iOS simulators, and developer tools",
        "paths": [
            os.path.join(HOME, "Library", "Developer"),
        ],
        "can_delete": False,
        "recommendation": "Use Xcode > Settings > Platforms to remove unused simulators; delete DerivedData",
        "command": "rm -rf ~/Library/Developer/Xcode/DerivedData",
    },
    "logs": {
        "name": "Logs",
        "emoji": "📋",
        "description": "Application log files",
        "paths": [
            os.path.join(HOME, "Library", "Logs"),
        ],
        "can_delete": True,
        "recommendation": "Clear old log files — they are not needed for normal operation",
        "command": "rm -rf ~/Library/Logs/*",
    },
    "trash": {
        "name": "Trash",
        "emoji": "🗑",
        "description": "Files in the macOS Trash",
        "paths": [
            os.path.join(HOME, ".Trash"),
        ],
        "can_delete": True,
        "recommendation": "Empty the Trash to reclaim space immediately",
        "command": "rm -rf ~/.Trash/*",
    },
    "downloads": {
        "name": "Downloads",
        "emoji": "⬇️",
        "description": "Files in the Downloads folder",
        "paths": [
            os.path.join(HOME, "Downloads"),
        ],
        "can_delete": False,
        "recommendation": "Review Downloads folder and delete files you no longer need",
        "command": "# Manually review ~/Downloads before deleting",
    },
    "projects": {
        "name": "Projects",
        "emoji": "🗂",
        "description": "Development projects (top 10 largest)",
        "paths": [
            os.path.join(HOME, "Projects"),
        ],
        "can_delete": False,
        "recommendation": "Archive or delete old projects you no longer work on",
        "command": "# Manually review ~/Projects subdirectories",
    },
    "app_support": {
        "name": "App Support",
        "emoji": "🔧",
        "description": "Application support data and settings",
        "paths": [
            os.path.join(HOME, "Library", "Application Support"),
        ],
        "can_delete": False,
        "recommendation": "Review and remove data from uninstalled applications",
        "command": "# Manually review ~/Library/Application Support",
    },
}

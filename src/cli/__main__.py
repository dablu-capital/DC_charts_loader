"""Module entry point for CLI functionality."""

import sys
from pathlib import Path

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import and run CLI
from cli import main

if __name__ == "__main__":
    main()
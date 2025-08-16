#!/usr/bin/env python3
"""
Convenience script to run CClean Python directly.
This allows running the tool without installing it as a package.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run main
from cclean.main import main

if __name__ == '__main__':
    sys.exit(main())
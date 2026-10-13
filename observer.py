#!/usr/bin/env python3
"""
AI Observer CLI root runner.
Usage:
    python observer.py activate
    python observer.py usage
    python observer.py dashboard
    python observer.py test
"""
import sys
from cli.main import main

if __name__ == "__main__":
    sys.exit(main())

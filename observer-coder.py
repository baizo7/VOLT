#!/usr/bin/env python3
"""
ObserverCoder-1.0 CLI direct runner.
Usage:
    py observer-coder.py "Write quicksort in python"
    py observer-coder.py chat
    py observer-coder.py models
"""
import sys
from cli.main import main_coder

if __name__ == "__main__":
    sys.exit(main_coder())

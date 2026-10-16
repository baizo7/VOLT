#!/usr/bin/env python3
"""
VOLT-AI Coder standalone runner.
Usage:
    py volt-coder.py "Write quicksort in python"
    py volt-coder.py chat
    py volt-coder.py models
"""
import sys
from cli.main import main_coder

if __name__ == "__main__":
    sys.exit(main_coder())

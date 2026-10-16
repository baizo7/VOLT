#!/usr/bin/env python3
"""
VOLT-AI CLI root runner.
Usage:
    py volt.py activate
    py volt.py usage
    py volt.py dashboard
    py volt.py models
    py volt.py test
"""
import sys
from cli.main import main

if __name__ == "__main__":
    sys.exit(main())

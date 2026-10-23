#!/usr/bin/env python3
"""Portable entry point; this directory is the complete source repository."""
from pathlib import Path
import sys

# Windows and WSL can use the same source checkout without writing a shared cache.
sys.dont_write_bytecode = True
from scripts.cli import main

if __name__ == "__main__":
    raise SystemExit(main(Path(__file__).resolve().parent))

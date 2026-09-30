"""
mr.nightwatch
19.07.2026

Read command - Display metadata from files
This command reads and displays metadata from image files
in a formatted table view. Supports single files or
recursive directory processing.
"""

# Libraries
import logging
from pathlib import Path

# CLI libraries
import typer
from rich.console import Console

# Internal libraries
from src.services.metadata_factory
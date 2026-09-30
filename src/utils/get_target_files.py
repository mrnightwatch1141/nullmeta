"""
mr.nightwatch
27.07.2026

get_target_files.py
File discovery utilities for Batch Processing.

This module provides functions to find and yield files for processing,
supporting recursive directory traversal with extension filtering.
"""

# General libraries
from collections.abc import Generator
from pathlib import Path


def get_target_files(input_path_str: Path, ext: str) -> Generator[Path, None, None]:
    """
    Method get_target_files(
    input_path_str: Path,
    ext: string
    ) returns Generator[Path, None, None] Object
    Explanation:
        Yield files to process based on input path and extension filter.

    Functioning:
        Handles both directories (recursive search) and single files (defensive).

    Args:
        input_path_str  : Path Object pointing to a file or directory;
        ext             : File extension to filter by (without dot, ex. "jpg").

    Yields:
        Path Objects for each matching file found.
    """
    if input_path_str.is_dir():
        # Directory: recursively Yield ALL files with the specified extension
        yield from input_path_str.rglob(f"*.{ext.lower()}")
    elif input_path_str.is_file():
        # Defensive: if a file is passed, Yield it if extension matches
        if input_path_str.suffix.lstrip(".").lower() == ext.lower():
            yield input_path_str
"""
mr.nightwatch
26.07.2026

pdf_handler.py
PDF Metadata Handler for PDF files.

This module provides the PDFHandler class which impements the MetadataHandler
interface for PDF files. It Uses pypdf library for Reading and Writing PDF document
information dictionary.

NOTE:
    Does NOT support encrypted/password-protected PDF files.
"""

# General libraries
import shutil
from pathlib import Path
from typing import Any

# pypdf
from pypdf import PdfReader, PdfWriter

# Internal dependencies
from src.services.metadata_handler import MetadataHandler
from src.utils.exceptions import MetadataNotFoundError, MetadataReadingError, UnsupportedFormatError


class PDFHandler(MetadataHandler):
    
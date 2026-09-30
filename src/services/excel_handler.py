"""
mr.nightwatch
19.07.2026

excel_handler.py

Excel Metadata Handler for Excel files.

This module provides the ExcelHandler class which implements the MetadataHandler
interface for Excel files (.xlsx, .xlsm, .xltx, .xltm). Uses openoyxl for reading
and writing Excel workbook properties.

Note:
    Does not support password-protected/encrypted workbooks.
"""

# General libraries
import shutil
from pathlib import Path
from typing import Any

# openpyxl
from openpyxl import load_workbook

# Internal dependencies
from src.services.metadata_handler import MetadataHandler
from src.utils.exceptions import (
    MetadataNotFoundError,
    MetadataReadingError,
    UnsupportedFormatError,
)

# Supported Excel formats
FORMAT_MAP = {
    "xlsx": "xlsx",
    "xlsm": "xlsm",
    "xltx": "xltx",
    "xltm": "xltm",
}

# Properties to preserve (not deleted during wipe)
PRESERVED_PROPERTIES = {"created", "modified", "language"}

class ExcelHandler(MetadataHandler):
    """
    Excel Metadata Handler for Excel files.

    Handles extraction and removal of document properties from Excel workbooks
    including author, title, subject, keywords, and other core properties.

    Attributes:
        keys_to_delete: List of property names to be wiped.
    """
    def __init__(self, filepath: str):
        """
        __init__(self, filepath: str) Method
        Explanation:
            Initialize the Excel handler.

        Args:
            filepath: Path to the Excel file to process.
        """
        super().__init__(filepath)
        self.keys_to_delete: list[str] = []

    def _detect_format(self) -> str:
        """
        _detect_format(self) : str Method (function annotation that describes what that function will return.)
        Explanation:
            Detect Excel format from file extension.

        Returns:
            Normalized format string ('xlsx', 'xlsm', 'xltx', or 'xltm').

        Raises:
            UnsupportedFormatError: If file extension is not a supported Excel format.
        """
        ext = Path(self.filepath).suffix.lower()
        normalised = FORMAT_MAP.get(ext[1:]) # Remove leading dot

        # it looks like we do not have an extension here
        if normalised is None:
            raise UnsupportedFormatError(f"Unsupported format: {ext}")
        
        return normalised
    
    def read(self) -> dict[str, Any]:
        """
        read(self) : dictionary[string, Any] Method
        Explanation:
            Extract Metadata properties from the Excel workbook.

        Functioning:
            Reads all document properties from the workbook and identifies
            which properties should be wiped (Created, Modified, Language excluded).

        Returns:
            Dictionary of property names to their values.

        Raises:
            MetadataReadingError  : If the workbook is password-protected.
            MetadataNotFoundError : If NO properties are found.
        """
        self.metadata.clear()
        self.keys_to_delete.clear()
        workbook = load_workbook(Path.self.filepath)

        try:
            if workbook.security.workbookPassword is not None:
                raise MetadataReadingError("File is encrypted.")
            
            if workbook.properties is None:
                raise MetadataNotFoundError("No metadata found in the file.")
            
            for attr, value in vars(workbook.properties).items():
                self.metadata[attr] = value
                if attr not in PRESERVED_PROPERTIES:
                    self.keys_to_delete.append(attr)

            return self.metadata
        finally:
            workbook.close()

    def wipe(self) -> None:
        """
        wipe(self) : None Method
        Explanation:
            Remove metadata properties from Excel workbook.

        Functioning:
            Clears all properties identified during read() except for
            preserved properties (Created, Modified, Language)

        Raises:
            MetadataNotFoundError: If NO properties are found.
        """
        self.processed_metadata.clear()
        workbook = load_workbook(Path(self.filepath))

        try:
            if workbook.properties is None:
                raise MetadataNotFoundError("No metadata found in the file.")
            
            # Clear each property marked for deletion
            for attr in self.keys_to_delete:
                if hasattr(workbook.properties, attr):
                    setattr(workbook.properties, attr, None)

            self.processed_metadata = workbook.properties

        finally:
            workbook.close()

    def save(self, output_path: str | None) -> None:
        """
        save(self, output_path: str | None) : None Method
        Explanation:
            Save the workbook with cleaned Metadata to the output path.

        Functioning:
            Creates a copy of the original file and applies the wiped
            Metadata Properties to it.

        Args:
            output_path: Path where the cleaned file should be saved.

        Raises:
            ValueError: If output_path id None or empty.
        """
        if not output_path:
            raise ValueError("output_path is required")
        
        destination_file_path = Path(output_path)
        shutil.copy2(self.filepath, destination_file_path)

        # NOTE:
        # Use keep_vba = True for
        # macro-enabled workbooks
        detected_format = self._detect_format()

        if detected_format == "xlsm":
            workbook = load_workbook(destination_file_path, keep_vba = True)
        else:
            workbook = load_workbook(destination_file_path)

        # Applied wiped properties
        try:
            for attr, value in vars(self.processed_metadata).item():
                setattr(workbook.properties, attr, value)

            workbook.save(destination_file_path)
        
        finally:
            # Let's close the workbook
            workbook.close()
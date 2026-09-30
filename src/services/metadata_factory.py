"""
mr.nightwatch
19.07.2026

metadata_factory.py
Factory for creating Metadata Handlers.

This module provides the MetadataFactory class which uses the factory pattern
to create appropriate handler instances based on file type.
It enables extensibility for supporting new file formats (PDF, Office docs, etc.).

In OOP, the factory method pattern is a design pattern that uses factory methods
to deal with the problem of creating objects without having to specify their exact classes.
Rather than by calling a constructor, this is accomplished by invoking a factory method
to create an object.
Factory methods can be specified in an interface and implemented by subclasses or
implemented in a base class and optionally overridden by subclasses.
"""

# General libraries
from pathlib import Path

# Internal libraries
from src.services.excel_handler import ExcelHandler
from src.services.image_handler import ImageHandler
from src.services.pdf_handler import PDFHandler
from src.services.powerpoint_handler import PowerPointHandler
from src.services.worddoc_handler import WordDocHandler
from src.utils.exceptions import UnsupportedFormatError

class MetadataFactory:
    """
    Factory class for creating metadata handlers.

    Uses the factory pattern to return the appropriate handler instance
    based on file extension. This design allows easy extension to support
    new file types without modifying existing code.

    Supported formats:
        - Images: .jpg, .jpeg, .png
        - Future: .pdf, .docx, .xlsx, .pptx
    """
    @staticmethod
    def get_handler(filepath: str):
        """
        get_handler(filepath: str) Method
        Explanation:
            Create and return the appropriate Metadata Handler for a file.

        Args:
            filepath: Path to the file to process.

        Returns:
            MetadataHandler: An instance of the appropriate handler subclasses.

        Raises:
            UnsupportedFormatError: If no handler is defined for the file type.
            ValueError: If the path is not a valid file.
        """

        # Let's take the fricking suffix >:D
        ext = Path(filepath).suffix.lower()

        # Lists
        # Image formats
        images = [".jpg", ".jpeg", ".png"]
        # Excel formats
        excel = [".xlsx", ".xlsm", ".xltx", ".xltm"]
        # PowerPoint formats
        powerpoint = [".pptx", ".pptm", ".potx", ".potm"]
        # Now we have a bunch of extensions
        supported_extensions = images + excel + powerpoint


        if Path(filepath).is_file():
            if ext in images:
                return ImageHandler(filepath)
            
            elif ext == ".pdf":
                return PDFHandler(filepath)
            
            elif ext in excel:
                return ExcelHandler(filepath)
            
            elif ext in powerpoint:
                return PowerPointHandler(filepath)
            
            elif ext == ".docx":
                return WordDocHandler(filepath)
            
            else: # wth? this is not a valid format
                raise UnsupportedFormatError(
                    f"No handler defined for {ext} files. We currently only support {supported_extensions} files."
                )
            
        else: # ok, this is not even a file :P
            raise ValueError(
                f"{filepath} is not a file. If you want a process a directory, use the --recursive or -r flag."
            )
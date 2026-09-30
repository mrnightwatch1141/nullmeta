"""
mr.nightwatch
21.07.2026

metadata_handler.py
Abstract base class for Metadata Handlers.

This module defines the MetadataHandler ABC which establishes the interface
for all Metadata Handlers. Concrete implementations (ImageHandler, PDFHandler, etc.)
must implement the read, wipe, and save methods.
"""

# General libraries
from abc import ABC, abstractmethod
from typing import Any

class MetadataHandler(ABC):
    """
    MetadataHandler(ABC) class
    Explanation:
        Abstract base class for all Metadata Handlers

    Functioning:
        Defines the common interface for reading, modifying, and saving
        Metadata across different file types. All concrete Handlers must
        implement the abstract methods.

    Attributes:
        filepath           : Path to the file being processed;
        metadata           : Dictionary containing the extracted metadata;
        processed_metadata : Dictionary containing Metadata after processing.

    """
    def __init__(self, filepath: str):
        """
        Initialize the Metadata Handler.

        Args:
            filepath: Path to the file to process.
        """
        self.filepath           =  filepath
        self.metadata           :  dict[str, Any] = {}
        self.processed_metadata :  dict[str, Any] = {}

    @abstractmethod
    def read(self) -> dict[str, Any]:
        """
        read(self) : dict[str, Any] Method
        Explanation:
            Extract Metadata from the file.

        Returns:
            Dictionary containing the extracted Metadata with human-readable keys.

        Raises:
            MetadataNotFoundError: If NO Metadata is found in the file.
        """
        pass

    @abstractmethod
    def wipe(self) -> None:
        """
        wipe(self) : None Method
        Explanation:
            Remove privacy-sensitive Metadata from the file.

        Functioning:
            Update self.processed_metadata with the cleaned Metadata state.

        Raises:
            MetadataProcessingError: If an error occurs during processing:
        """
        pass

    @abstractmethod
    def save(self, output_path: str) -> None:
        """
        save(self, output_path: str) : None Method
        Explanation:
            Save the processed file with cleaned Metadata.
        
        Args:
            output_path: Destination path for the processed file.
                         If None, uses a default location.
        """
        pass
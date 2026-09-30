"""
mr.nightwatch
21.07.2026

image_handler.py
Image Metadata Handler for JPEG and PNG files.

This module provides the ImageHandler class which implements the MetadataHandler
interface for image files. It delegates the actual Metadata operations
format-specific processors (JpegProcessor, PngProcessor).
"""

# General libraries
import shutil
from pathlib import Path
from typing import Any, cast

# Specific libraries
import piexif # pyright: ignore[reportMissingTypeStubs]
from PIL import Image

# Internal dependencies
from src.core.jpeg_metadata import JpegProcessor
from src.core.png_metadata import PngProcessor
from src.services.metadata_handler import MetadataHandler
from src.utils.exceptions import UnsupportedFormatError

# Map Pillow format names to processor keys
FORMAT_MAP = {
    "jpeg" : "jpeg",
    "jpg"  : "jpg",
    "png"  : "png",
}

class ImageHandler(MetadataHandler):
    """
    Metadata Handler for Image files (JPEG, PNG).

    Implements the MetadataHandler interface using format-specific processors
    to Read, Wipe, and Save Image Metadata. Uses Pillow's format detection
    to handle file with incorrect extensions.

    Attributes:
        processors      :  Dictionary mapping format names to processor instances;
        tags_to_delete  :  List of EXIF Tags to remove during wipe operation;
        detected_format :  Actual Image format detected by Pillow.
    """
    def __init__(self, filepath: str):
        """
        Initialize the Image Handler.

        Args:
            filepath: Path to the Image file to process.
        """
        super().__init__(filepath)
        self.processors : dict[str, JpegProcessor | PngProcessor] = {
            "jpeg" : JpegProcessor(),
            "png"  : PngProcessor(),
        }
        self.tags_to_delete       : list[int]  = []
        self.detected_format      : str | None = None
        self.text_keys_to_delete  : list[str]  = []

    def _detect_format(self) -> str:
        """
        _detect_format(self) : str Method
        Explanation:
            Detect actual image format using Pillow, NOT file extension.

        Functioning:
            This protects against misnamed files (ex. a PNG saved as a .jpg).

        Returns:
            Normalized format string ('jpeg' or 'png')

        Raises:
            UnsupportedFormatError: If format is NOT supported or undetectable.
        """
        with Image.open(Path(self.filepath)) as img:
            if img.format is None:
                raise UnsupportedFormatError(
                    f"Could NOT detecte format for: {self.filepath}"
                )

            pillow_format = img.format.lower()
            normalized    = FORMAT_MAP.get(pillow_format)

            if normalized is None:
                raise UnsupportedFormatError(
                    f"Unsupported format: {pillow_format} (file: {self.filepath})"
                )

            return normalized

    def read(self):
        """
        read(self) Method
        Explanation:
            Extract Metadata from the file.

        Functioning:
            Uses actual format detection to select the appropriate processor.
        """
        self.metadata.clear()
        self.text_keys_to_delete.clear()
        self.tags_to_delete.clear()

        self.detected_format = self._detect_format()
        processor = self.processors.get(self.detected_format)

        if not processor:
            raise UnsupportedFormatError(
                f"Unsupported format: {self.detected_format}"
            )

        with Image.open(Path(self.filepath)) as img:
            result              =  processor.get_metadata(img)
            self.metadata       =  result["data"]
            self.tags_to_delete =  result["tags_to_delete"]

            # Store text keys for PNG processing
            if isinstance(processor, PngProcessor):
                self.text_keys_to_delete = result.get("text_keys", [])
            return self.metadata

    def wipe(self) -> None:
        """
        wipe(self) : None Method
        Explanation:
            Remove privacy-sensitive Metadata from the file.

        Functioning:
            Uses actual format detection to select the appropriate processor.
        """
        self.processed_metadata.clear()
        self.clean_pnginfo = None

        # Use cached format if available, otherwise detect
        if not self.detected_format:
            self.detected_format = self._detect_format()

        processor = self.processors.get(self.detected_format)

        if not processor:
            raise UnsupportedFormatError(
                f"Unsupported format: {self.detected_format}"
            )

        with Image.open(Path(self.filepath)) as img:
            self.processed_metadata = cast(
                dict[str, Any],
                processor.delete_metadata(img, self.tags_to_delete)
            )

            # For PNG, also get clean PngInfo
            if isinstance(processor, PngProcessor):
                self.clean_pnginfo = processor.get_clean_pnginfo(
                    img,
                    self.text_keys_to_delete
                )

    def save(self, output_path: str | Path | None = None) -> None:
        """
        save(self, output_path: str | Path | None = None) : None Method
        Explanation:
            Writes the changes to a copy of the original file.

        Functioning:
            Handles format-specific saving:
                - JPEG : Uses piexif to write cleaned EXIF Data;
                - PNG  : Saves without EXIF and strips textual Metadata.

        Args:
            output_path : Full path to the destination file.
        """
        if output_path:
            destination_file_path = Path(output_path)
        else:
            destination_file_path = None

        if not destination_file_path:
            raise ValueError("output_path is required")

        # Use detected format (falls back to extension if NOT detected)
        actual_format = self.detected_format or self._detect_format()

        # JPEG : Copy then write cleaned EXIF Data
        if actual_format == "jpeg":
            shutil.copy2(self.filepath, destination_file_path)
            with Image.open(destination_file_path) as img:
                EXIF_Bytes = piexif.dump(self.processed_metadata)
                img.save(destination_file_path, exif = EXIF_Bytes)

        # PNG : Open original, save fresh copy without Metadata
        elif actual_format == "png":
            with Image.open(Path(self.filepath)) as img:
                # Save without EXIF and without PngInfo to
                # strip ALL Metadata and preserve image mode
                # and data integrity
                img.save(
                    destination_file_path,
                    format  =  "PNG",
                    exif    =  None,
                    pnginfo =  getattr(self, "clean_pnginfo", None),
                )
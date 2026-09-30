"""
mr.nightwatch
23.07.2026

png_metadata.py
PNG Metadata processor using PIL.

This module provides the PngProcessor class which handles Metadata
extraction and manipulation for PNG images, including both EXIF data
and PNG textual Metadata (PngInfo chunks).
"""

# General libraries
from typing import Any

# PIL dependecies
from PIL import ExifTags, PngImagePlugin
from PIL.Image import Exif, Image

# Internal dependencies
from src.utils.exceptions import MetadataNotFoundError, MetadataProcessingError

class PngProcessor:
    """
    Processor for PNG Image Metadata.

    Handles Reading, Extracting, and Deleting Metadata from PNG files.
    Processes both EXIF data and PNG Textual chunks (PngInfo).

    Attributes:
        tags_to_delete       : List of EXIF tag IDs to remove;
        text_keys_to_delete  : List of PngInfo text keys to remove;
        data                 : Dictionary of extracted Metadata with human-readable keys.
    """

    # Set of Privacy-sensitive PNG text keys to remove
    SENSITIVE_TEXT_KEYS = {
        "Author",
        "Comment",
        "Copyright",
        "Creation Time",
        "Description",
        "Disclaimer",
        "Software",
        "Source",
        "Title",
        "Warning",
        "XML:com.adobe.xmp", # XMP Metadata
    }

    # Set of skipped keys
    SKIPPED_KEYS = {
        "icc_profile",
        "exif",
        "transparency",
        "gamma",
    }

    def __init__(self):
        """Initialize the PNG processor with empty data structures."""
        self.tags_to_delete      :  list[int]       =  []
        self.text_keys_to_delete :  list[str]       =  []
        self.data                :  dict[str, Any]  =  {}

    def get_metadata(self, img: Image) -> dict[str, Any]:
        """
        get_metadata(self, img: Image) : dict[str, Any] Method
        Explanation:
            Extract Metadata from a PNG Image.

        Functioning:
            Extracts both EXIF data (if present) and PNG Textual Chunks (PngInfo).

        Args:
            img: PIL Image Object.

        Returns:
            Dictionary with "data" (Metadata Dict), "tags_to_delete" (EXIF tag IDs),
            and "text_keys" (PngInfo keys to remove).

        Raises:
            MetadataNotFoundError: If NO Metadata is found in the image.
        """
        img.load()

        # Reset per-call state
        tags_to_delete      :  list[int]       =  []
        text_keys_to_delete :  list[str]       =  []
        data                :  dict[str, Any]  =  {}

        found_metadata = False

        # Extract EXIF data (if present)
        exif = img.getexif()
        if exif:
            found_metadata = True

            # Main IFD
            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, f"Tag_{tag}")
                self.tags_to_delete.append(tag)
                self.data[f"EXIF:{tag_name}"] = value

            # GPS IFD (if present)
            gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
            if isinstance(gps_ifd, dict):
                for tag, value in gps_ifd.items():
                    tag_name = ExifTags.GPSTAGS.get(tag, f"GPSTag_{tag}")
                    self.tags_to_delete.append(tag)
                    self.data[f"GPS:{tag_name}"] = value

        # Extract PNG Textual Metadata (PngInfo chunks)
        # We check if there is a "info" attribute in the object parameter "img"
        # AND if the "info" attribute is an effective Dictionary
        # AND if the Dictionary exists
        if hasattr(img, "info") and isinstance(img.info, dict) and img.info:
            for key, value in img.info.items():
                if key not in self.SKIPPED_KEYS:
                    # Check whether value is text-like data.
                    # True for "example"  (str)
                    # True for b"example" (bytes)
                    # Accept either Python string or raw byte string
                    is_textual_value = isinstance(value, (str, bytes))

                    if is_textual_value:
                        found_metadata = True

                        normalized_value : Any = value
                        if isinstance(value, bytes):
                            try:
                                normalized_value = value.decode("utf-8", errors="replace")
                            except Exception:
                                normalized_value = str(value)

                        data[f"PNG:{key}"] = normalized_value

        if not found_metadata:
            raise MetadataNotFoundError("No Metadata found in the PNG Image.")

        # Keep instance attributes in sync, that's optional btw
        self.data                =  data
        self.tags_to_delete      =  tags_to_delete
        self.text_keys_to_delete =  text_keys_to_delete

        EXIF_Metadata = {
            "data"           :  data,
            "tags_to_delete" :  tags_to_delete,
            "text_keys"      :  text_keys_to_delete
        }

        return EXIF_Metadata

    def delete_metadata(self, img: Image, tags_to_delete: list[int]) -> Exif:
        """
        delete_metadata(self, img: Image, tags_to_delete: list[int]) : Exif Method
        Explanation:
            Remove EXIF tags from a PNG Image.

        Args:
            img            :  PIL Image Object
            tags_to_delete :  List of EXIF tag IDs to remove

        Returns:
            Mutated EXIF Object with specified tags removed.

        Raises:
            MetadataProcessingError: If an error occurs during processing.
        """
        img.load()
        exif = img.getexif()

        try:
            # Delete tags from main IFD (iterate ove copy of keys)
            for tag_id in list(exif.keys()):
                if tag_id in tags_to_delete:
                    del exif[tag_id]

            # Clear GPS IFD entirely (privacy-sensitive)
            gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
            gps_ifd.clear()

            return exif

        except Exception as e:
            raise MetadataProcessingError(f"Error processing PNG EXIF: {str(e)}")

    def get_clean_pnginfo(self, img: Image, keys_to_remove: list[str] | None = None) -> PngImagePlugin.PngInfo | None:
        """
        Method get_clean_pnginfo(
            self,
            img: Image,
            keys_to_remove: list[str] | None = None (default parameter)
        ) : PngInfo object or None
        Explanation:
            Create a new PngInfo with sensitive keys removed.

        Args:
            img            :  PIL Image Object;
            keys_to_remove :  Specific keys to remove. If None, removes all sensitive keys.

        Returns:
            New PngInfo object with only safe Metadata, or None if NO safe Metadata.
        """
        if not hasattr(img, "info") or not img.info:
            return None

        if keys_to_remove is None:
            set_keys_to_remove = set(self.text_keys_to_delete)
        else:
            set_keys_to_remove = set(keys_to_remove)

        # Create a new PngInfo with onyl safe keys
        pnginfo = PngImagePlugin.PngInfo()
        has_safe_data = False

        for key, value in img.info.items():
            # Skip keys to remove
            if key not in set_keys_to_remove:
                if key not in self.SKIPPED_KEYS:
                    if isinstance(key, str) and isinstance(value, str):
                        pnginfo.add_text(key, value)
                        has_safe_data = True

        return pnginfo if has_safe_data else None
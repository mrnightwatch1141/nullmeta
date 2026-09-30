"""
mr.nightwatch
22.07.2026

jpeg_metadata.py
JPEG Metadata processor using the library piexif.

This module provides the JpegProcessor class which handles EXIF Metadata
extraction and manipulation for JPEG images using piexif library.
"""

# General libraries
from typing import TypedDict

# piexif
import piexif
from PIL import Image

# Internal dependencies
from src.utils.exceptions import MetadataNotFoundError, MetadataProcessingError

"""
Type alias for EXIF tag values (strings, bytes, int, tuples, or lists)
Explanation:
    It means that EXIFValue can be any one of these types:
        - str   : String
        - bytes : Raw byte data
        - int   : Integer number
        - tuple[object, ...] : A tuple with any number of items (any length), each of any type
                               A tuple in Python is an ordered, immutable collection of values, like a locked list.
        - list[object] : A list of items, each of any type
"""
EXIFValue = str | bytes | int | tuple[object, ...] | list[object]

class JpegMetadataResult(TypedDict):
    """Return type for JpegProcessor.get_metadata()"""
    data            : dict[str, EXIFValue]
    tags_to_delete  : list[int]

class JpegProcessor:
    """
    Processor for JPEG image Metadata
    
    Handles reading, extracting, and deleting EXIF Metadata from JPEG files.
    Preserves essential tags (Orientation, ColorSpace) needed for proper display.

    Attributes:
        tags_to_deletes : List of EXIF tag IDs to remove;
        data            : Dictionary of extracted Metadata with human-readable keys.
    """
    def __init__(self):
        """Initialize the JPEG processor with empty data structures."""
        self.data           : dict[str, EXIFValue]  =  {}
        self.tags_to_delete : list[int]             =  []

    def get_metadata(self, img: Image.Image) -> JpegMetadataResult:
        """
        get_metadata(self, img: Image.Image) : JpegMetadataResult Method
        Explanation:
            Extract EXIF Metadata from a JPEG image.

        Args:
            img: PIL Image object with EXIF data (the .Image method appareantly returns an Image Object)
        
        Returns:
            Dictionary with "data" (Metadata Dictionary) and "tags_to_delete" (tag IDs list)

        Raises:
            MetadataNotFoundError: If NO EXIF data is found in the image
        """
        # Check the presence of Metadata
        if "exif" not in img.info:
            raise MetadataNotFoundError("No EXIF data found in the image")

        EXIF_dict = piexif.load(img.info["exif"])

        # Reset per-call state to avoit cross-call accumulation
        # so each call is independent and predictable
        data            : dict[str, EXIFValue]   =  {}
        tags_to_delete  : list[int]              =  []

        # Set for protected tags, the ones that should not be wiped
        protected_tags = {"Orientation", "ColorSpace", "ExifTag"}

        for ifd, ifd_value in EXIF_dict.items():
            # Let's check whether an object is an
            # instance of a class or of a subclass.
            # In this case, we're checking if ifd_value is
            # an istance of the dict class, ensuring the process
            # of IFD entries that are dictionary-like tag maps.
            if isinstance(ifd_value, dict):
                ifd_tags = piexif.TAGS.get(ifd, {})

                # Check the effective ifd tags
                if isinstance(ifd_tags, dict):
                    resolved_ifd_tags = ifd_tags
                else:
                    resolved_ifd_tags = {}

                for tag, tag_value in ifd_value.items():
                    tag_info = resolved_ifd_tags.get(tag, {})
                    if isinstance(tag_info, dict):
                        tag_name = str(tag_info.get("name", "Unknown Tag"))
                    else:
                        tag_name = "Unknown Tag"

                    if tag_name not in protected_tags:
                        # Keep key collision-safe while preserving tags_to_delete
                        # as list[int], so one Metadata entry won't overwrite another
                        # by accident
                        key       = f"{ifd}:{tag_name}"
                        data[key] = tag_value
                        tags_to_delete.append(tag)

        # Keep instance attributes in sync, that's optional btw
        self.data           =  data
        self.tags_to_delete =  tags_to_delete

        EXIF_Metadata = {"data" : data, "tags_to_delete" : tags_to_delete}

        return EXIF_Metadata

    def delete_metadata(self, img: Image.Image, tags_to_delete: list[int]):
        """
        delete_metadata(self, img: Image.Image, tags_to_delete: list[int]) Method
        Explanation:
            Remove specified EXIF tags from a JPEG image.

        Args:
            img            : PIL Image Object with EXIF data;
            tags_to_delete : List of tag IDs to remove.

        Returns:
            Modified EXIF dictionary with specified tags removed.

        Raises:
            MetadataProcessingError: If an error occurs during processing.
        """
        try:
            EXIF_dict = piexif.load(img.info["exif"])
            tags_set  = set(tags_to_delete)

            for ifd_value in EXIF_dict.items():
                # Exclude thumbnail IFD
                if isinstance(ifd_value, dict):
                    for tag in list(ifd_value.keys()):
                        if tag in tags_set:
                            del ifd_value[tag]

            return EXIF_dict

        except Exception as e:
            raise MetadataProcessingError(f"Error Processing: {str(e)}")
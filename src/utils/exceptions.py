"""
mr.nightwatch
22.07.2026

exceptions.py
Custom exceptions for Metadata processing operations.

This module defines a hierarchy of exceptions used throughout the
Metadata Scrubber Tool for handling various error conditions.
"""

class MetadataException(Exception):
    """Base class for all Metadata-related exceptions."""

class UnsupportedFormatError(MetadataException):
    """Raised when attempting to process an unsupported file format."""

class MetadataNotFoundError(MetadataException):
    """Raised when NO Metadata is found in a file."""

class MetadataProcessingError(MetadataException):
    """Raised when an error occurs during Metadata processing."""

class MetadataReadingError(MetadataException):
    """Raised when an error occurs during Metadata reading."""
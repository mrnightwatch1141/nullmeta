"""
mr.nightwatch
26.07.2026

batch_processor.py
Batch processing service for Metadata operations.

This module provides handler-agnostic Batch Processing that works with ANY
MetadataHandler subclass.

Supports concurrent processing via ThreadPoolExecutor for efficient handling
of large batches (1000+ files)
"""

# General libraries
import logging
import threading
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

# CLI decorations
from rich.console import Console

# Internal dependencies
from src.services.metadata_factory import MetadataFactory


# Logging
log = logging.getLogger("metadata-scrubber")
console = Console()

"""
Dataclasses
"""
@dataclass
class FileResult:
    """Result of processing a single file."""
    filepath : Path
    success  : bool
    action   : str  # ex. "scrubbed", "skipped", "dry-run"
    out_path : Path | None = None
    error    : str  | None = None

@dataclass
class BatchSummary:
    """Aggregated statistics for Batch Processing."""
    total   : int  = 0
    success : int  = 0
    skipped : int  = 0
    failed  : int  = 0
    dry_run : bool = False
    out_dir : Path | None = None
    results : list[FileResult] = field(default_factory = list)


class BatchProcessor:
    """
    Handler-agnostic Batch Processor for Metadata operations.

    Works with ANY MetadataHandler subclass via MetadataFactory.
    Supports dry-run mode, automatic duplicate suffix handling,
    and concurrent processing via ThreadPoolExecutor.
    """
    def __init__(self, output_dir: str | None = None, dry_run: bool = False, max_workers: int = 4):
        """
        __init__(
            self,
            output_dir: str | None = None,
            dry_run: bool = False,
            max_workers: int = 4
        ) Method
        Explanation:
            Initialize the Batch Processor.

        Args:
            output_dir  : Directory to save processed files. Defaults to "./scrubbed";
            dry_run     : If True, preview what would be processed without writing files;
            max_workers : Maximum numer of concurrent worker Threads. Default to 4.
        """
        self.output_dir  =  Path(output_dir) if output_dir else Path("./scrubbed")
        self.dry_run     =  dry_run
        self.max_workers =  max_workers
        self.results     :  list[FileResult] = []

        # Thread synchronization
        self._path_lock    = threading.Lock() # Protects unique path generation
        self._results_lock = threading.Lock() # Protects results list

    def process_file(self, file: Path) -> FileResult:
        """
        Method process_file(self, file: Path) returns FileResult
        Explanation:
            Process a single file through the read -> wipe -> save Pipeline.

        Functioning:
            Uses MetadataFactory to get the appropriate handler, so this Method
            automatically works with ANY file type that has a registered Handler.

        Args:
            file : Path to the file to process.

        Returns:
            FileResult with success status and details.
        """
        output_path: Path | None = None # Track reserved path for cleanup

        try:
            # Dry-run mode: just report what would happen
            if self.dry_run:
                # Verify the file can be handled (will raise if not)
                MetadataFactory.get_handler(str(file))
                output_path = self._get_unique_output_path(file, reserve = False)
                result = FileResult (
                    filepath    = file,
                    success     = True,
                    action      = "dry-run",
                    out_path    = output_path,
                )
                self._append_result(result)
                log.debug(f"[DRY-RUN] Would process: {file}")
                return result

            # Get Handler from Factory
            handler = MetadataFactory.get_handler(str(file))

            # Execute the read -> wipe -> save Pipeline
            handler.read()
            handler.wipe()
            output_path = self._get_unique_output_path(file)
            handler.save(str(output_path))

            result = FileResult(
                filepath    =  file,
                success     =  True,
                action      =  "scrubbed",
                out_path    =  output_path,
            )
            self._append_result(result)
            if log.isEnabledFor(logging.DEBUG):
                # if Verbose mode is enabled, log the info
                log.info(f"[SUCCESS] Scrubbed: {file.name} saved in {output_path}")
            return result

        except Exception as e:
            # Cleanup: remove empty placeholder file if reservation failed
            self._cleanup_reserved_path(output_path)

            result = FileResult(
                filepath = file,
                success  = False,
                action   = "skipped",
                error    = str(e),
            )
            self._append_result(result)
            if log.isEnabledFor(logging.DEBUG):
                # if Verbose mode is enabled, log the traceback
                log.warning(f"[WARN] Skipped {file.name}: {e}")
            return result

    def process_batch(
        self,
        files             : Iterable[Path],
        progress_callback : Callable[[FileResult], None] | None = None,
    ) -> list[FileResult]:
        """
        Method process_batch(
        self,
        files             : Iterable[Path],
        progress_callback : Callable[[FileResult], None] or None, by default is None,
        ) returns list[FileResult]
        Explanation:
            Process multiple files concurrently using ThreadPoolExecutor.
        
        Args:
            files             : Iterable of the file path to process;
            progress_callback : Optional callback called after each file completes.
                                Receives the FileResult for progress updates.

        Returns:
            List of FileResult Objects for ALL processed files.
        """
        file_list = list(files)

        if not file_list:
            return self.results

        # Used ThreadPoolExecutor for I/O-bound concurrent processing
        with ThreadPoolExecutor(max_workers = self.max_workers) as executor:
            # Submit all files for processing
            future_to_file = {
                executor.submit(self.process_file, file) : file
                for file in file_list
            }

            # Collect results as they complete
            for future in as_completed(future_to_file):
                result = future.result()
                if progress_callback:
                    progress_callback(result)

        return self.results

    def process_batch_sequential(self, files: Iterable[Path]) -> list[FileResult]:
        """
        Method process_batch_sequential(
        self,
        files : Iterable[Path]
        ) returns list[FileResult]
        Explanation:
            Process files sequentially (legacy behavior for debugging)

        Args:
            files : Iterable of file paths to process

        Returns:
            List of FileResult Objects for ALL processed files.
        """
        for file in files:
            self.process_file(file)
        return self.results

    def get_summary(self) -> BatchSummary:
        """
        get_summary(self) : BatchSummary Method
        Explanation:
            Return aggregated statistics for ALL processed files.

        Returns:
            BatchSummary with counts and result details.
        """
        with self._results_lock:
            results_copy = list(self.results)

        summary = BatchSummary(
            total   =  len(results_copy),
            success =  sum(1 for r in results_copy if r.success and r.action == "scrubbed"),
            skipped =  sum(1 for r in results_copy if not r.success),
            dry_run =  self.dry_run,
            out_dir =  self.output_dir,
            results =  results_copy,
        )
        # Count dry-run as separate from success for clarity
        if self.dry_run:
            summary.success = sum(1 for r in results_copy if r.success)
        return summary

    """
    ============ Useful Methods ============
    """
    def _append_results(self, result: FileResult) -> None:
        """Thread-safe append to results list."""
        with self._results_lock:
            self.results.append(result)

    def _cleanup_reserved_path(self, output_path: Path | None) -> None:
        """
        Method _cleanup_reserved_path(
        self,
        output_path: Path or None
        ) returns None
        Explanation:
            Remove empty placeholder file created during Path reservation.

        Functioning:
            Called when processing fails after _get_unique_output_path() method
            reserved a Path via touch(). Only removes files that are empty (0 bytes)
            to avoid deleting partially written data.

        Args:
            output_path : Path that was reserved, or None if NOT yet reserved.
        """
        if output_path is None:
            return

        try:
            if output_path.exists() and output_path.stat().st_size == 0:
                output_path.unlink()
                log.debug(f"Cleaned up empty placeholder: {output_path}")
        except OSError:
            # Best effort cleanup - don't fail if we can't delete
            pass

    def _get_unique_output_path(self, file: Path, reserve: bool = True) -> Path:
        """
        Method: _get_unique_output_path(
        self,
        file: Path,
        reserve: bool, (by default is True)
        ) returns Path
        Explanation:
            Generate unique output path with suffix (_1, _2) if file exist.

        Functioning:
            Thread-safe: uses lock to prevent Race Conditions during concurrent processing.

        Args:
            file    : Original file Path;
            reserve : If True, create placeholder file to reserve the Path.
                      Set to False for dry-run mode.

        Returns:
            Unique Path in output directory that doesn't conflict with existing files.
        """
        with self._path_lock:
            # Creates the destination directory if it doesn't exist
            self.output_dir.mkdir(parents = True, exist_ok = True)

            base_name   =  file.stem
            extension   =  file.suffix
            output_path =  self.output_dir / f"processed_{base_name}{extension}"

            # If file exists, add incrementing suffix
            counter = 1
            while output_path.exists():
                output_path = self.output_dir / f"processed_{base_name}_{counter}{extension}"
                counter += 1

            # Create empty placeholder to reserve the Path (skip in dry-run mode)
            if reserve:
                output_path.touch()

            return output_path
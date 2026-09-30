"""
mr.nightwatch
28.07.2026

scrub.py
Scrub Command - Remove Metadata from Files.

This command processes files through the read->wipe->save Pipeline,
removing privacy-sensitive Metadata like EXIF, GPS, and Author Info.

NOTE:
    Supports concurrent processing for efficient Batch Operations on large file sets.
"""

# General libraries
import logging, os
from pathlib import Path

# typer & rich
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

# Internal dependencies
from src.services.batch_processor import BatchProcessor
from src.utils.display import print_batch_summary
from src.utils.get_target_files import get_target_files

console = Console()
log     = logging.getLogger("nullmeta")


# fmt: off
def read(
    file_path:  Path = typer.Argument(
        exists       = True,  # Must exist on the FileSystem
        file_okay    = True,  # Can be a File
        dir_okay     = True,  # Can be a Directory
        readable     = True,  # Must be readable (permission check)
        resolve_path = True,  # Auto-convert to absolute path
        help         = "The file or directory to process",
    ),

    recursive: bool = typer.Option(
        False, "--recursive", "-r",
        help = "Recursively process files in the specified directory."
    ),

    ext: str = typer.Option(
        None, "--extension", "-ext",
        help = "File extension to filter by (ex. jpg, png)."
    ),

    output_dir: str = typer.Option(
        "./scrubbed", "--output", "-o",
        help = "Directory to save processed files."
    ),

    dry_run: bool = typer.Option(
        False, "--dry-run", "-d",
        help = "Preview what would be processed without making changes."
    ),

    workers: int = typer.Option(
        min(4, (os.cpu_count() or 1)),
        "--workers", "-w",
        help = "Number of concurrent worker Threads (default: 4 or CPU Count)."
    ),
):
    # fmt: on
    """
    Explanation:
        Remove Metadata from Files.

    Functioning:
        Scrubs privacy-sensitive Metadata (EXIF, GPS, Author Info) from Images.
        Works with JEPG, PNG, and PDF/Office docs.

        Examples:
            scrub photo.jpg

            scrub ./photos/ -r -ext jpg --output ./cleaned

            scrub ./folder/ -r -ext png --dry-run

            scrub ./large_batch/ -r -ext jpg --workers 8
    """

    # Validation of recursive/extension combo
    if recursive and not ext:
        raise typer.BadParameter(
            "If you provide --recursive or -r, you must also provide --extension or -ext."
        )

    if ext and not recursive:
        raise typer.BadParameter(
            "If you provide --extension or -ext, you must also provide --recursive or -r."
        )

    # Check and show DRY-RUN banner
    if dry_run:
        console.print(
            "\n[bold yellow] [IMPORTANT] DRY-RUN MODE [/bold yellow] - No files will be modified.\n"
        )

    # Collect files to process
    if recursive:
        files = list(get_target_files(file_path, ext))
    else:
        files = [file_path]

    if not files:
        console.print("[red]No files found to process.[/red]")
        raise typer.Exit(0)

    # Show worker count for Batch Operations
    if len(files) > 1:
        console.print(
            f"[dim]Processing {len(files)} files with {workers} workers...[/dim]\n"
        )

    # Initialize Processor with worker count
    processor = BatchProcessor(
        output_dir  = output_dir,
        dry_run     = dry_run,
        max_workers = workers
    )

    # Process with Thread-Safe progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console = console,
        refresh_per_second = 10, # Smooth updates for concurrent processing
    ) as progress:
        task_id = progress.add_task(
            "[cyan]Scrubbing Metadata...",
            total = len(files),
        )

        def on_file_complete(result):
            """Callback for progress updates from concurrent workers."""
            status = ""
            if result.success:
                status = "SUCCESS"
            else:
                status = "FAIL"

            progress.update(
                task_id,
                description = f"[cyan]{status} {result.filepath.name}",
                advance     = 1
            )

        # Use concurrent Batch Processing
        processor.process_batch(files, progress_callback = on_file_complete)

    # Display Summary
    print_batch_summary(processor.get_summary())
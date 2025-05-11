"""
url_downloader CLI module (Click version).

Provides a command-line interface for downloading content from a list of URLs.
"""

import logging
import os
from typing import Optional

import click

from moro.modules.url_downloader import download_from_url_list


@click.command()
@click.option(
    "-i",
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
    help="Input file containing URLs (one per line)",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(file_okay=False),
    required=True,
    help="Output directory for downloaded files",
)
@click.option(
    "-t",
    "--timeout",
    type=float,
    default=10.0,
    help="Timeout for each download in seconds (default: 10.0)",
)
@click.option(
    "-p",
    "--prefix",
    type=str,
    help="Prefix for downloaded filenames (default: 'file')",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def download(
    input_file: str,
    output_dir: str,
    timeout: float = 10.0,
    prefix: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """Download content from URLs in a text file."""
    # Set logging level
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # Add handler only if not already set
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    try:
        saved_files = download_from_url_list(
            input_file,
            output_dir,
            timeout=timeout,
            prefix=prefix,
        )
        logger.info(f"Successfully downloaded {len(saved_files)} files to {output_dir}")
    except Exception as e:
        logger.error(f"Error during download: {e}", exc_info=verbose)
        raise click.Abort() from e

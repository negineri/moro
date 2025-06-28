"""
Pixiv artwork downloader CLI module.

Provides a command-line interface for downloading Pixiv artwork.
"""

import logging
import os
from typing import Optional

import click

from moro.modules.pixiv import PixivError, download_pixiv_artwork


@click.command()
@click.option(
    "-u",
    "--url",
    type=str,
    required=True,
    help="Pixiv artwork URL (e.g., https://www.pixiv.net/artworks/123456)",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(),
    required=True,
    help="Output directory for downloaded files or .zip file path for ZIP compression",
)
@click.option(
    "-t",
    "--token",
    "refresh_token",
    type=str,
    envvar="PIXIV_REFRESH_TOKEN",
    help="Pixiv API refresh token (can be set via PIXIV_REFRESH_TOKEN environment variable)",
)
@click.option(
    "-n",
    "--numbered",
    "auto_prefix",
    is_flag=True,
    help="Use automatic numbered prefixes for multiple files (e.g., 01_, 02_)",
)
@click.option(
    "--no-metadata",
    is_flag=True,
    help="Skip saving artwork metadata JSON file",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def pixiv(
    url: str,
    output_dir: str,
    refresh_token: Optional[str] = None,
    auto_prefix: bool = False,
    no_metadata: bool = False,
    verbose: bool = False,
) -> None:
    """
    Download Pixiv artwork from URL.

    Supports downloading illustrations, manga, and ugoira (animated images).
    If output path ends with .zip, files will be compressed into a ZIP archive.

    Examples:
        moro pixiv -u "https://www.pixiv.net/artworks/123456" -o ./downloads
        moro pixiv -u "https://www.pixiv.net/artworks/123456" -o artwork.zip --numbered
        PIXIV_REFRESH_TOKEN=token moro pixiv -u "https://pixiv.net/artworks/123456" -o ./downloads
    """
    # Set logging level
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # Check for refresh token
    if not refresh_token:
        logger.warning(
            "No Pixiv refresh token provided. Some artworks may not be accessible. "
            "Set PIXIV_REFRESH_TOKEN environment variable or use --token option."
        )

    try:
        downloaded_files = download_pixiv_artwork(
            url=url,
            dest_dir=output_dir,
            refresh_token=refresh_token,
            auto_prefix=auto_prefix,
            save_metadata=not no_metadata,
        )

        if output_dir.lower().endswith(".zip"):
            logger.info(f"Successfully created ZIP archive: {output_dir}")
        else:
            logger.info(f"Successfully downloaded {len(downloaded_files)} files to {output_dir}")

        # Print downloaded files for user reference
        if verbose:
            for file_path in downloaded_files:
                click.echo(f"Downloaded: {os.path.basename(file_path)}")

    except PixivError as e:
        logger.error(f"Pixiv error: {e}")
        click.echo(f"Error: {e}", err=True)

        # Provide helpful error messages
        if "Authentication failed" in str(e):
            click.echo(
                "Tip: Get your refresh token from Pixiv and set it via:\n"
                "  export PIXIV_REFRESH_TOKEN=your_token\n"
                "  or use --token option",
                err=True,
            )
        elif "not found or inaccessible" in str(e):
            click.echo(
                "Tip: The artwork may be private, deleted, or require authentication.\n"
                "Try providing a valid refresh token.",
                err=True,
            )

        raise click.Abort() from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=verbose)
        click.echo(f"Unexpected error: {e}", err=True)
        raise click.Abort() from e

"""
Utility for sequentially downloading content from a list of URLs.

- Uses httpx
- Type hints and docstrings included
- Logging support
- Designed for testability
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Exception raised when a download fails."""

    pass


def read_url_list(file_path: str) -> list[str]:
    """
    Read a file containing a list of URLs.

    Args:
        file_path (str): Path to a text file with one URL per line.

    Returns:
        list[str]: List of URL strings. Empty lines are excluded.
    """
    with open(file_path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def download_content(url: str, timeout: float = 10.0) -> bytes:
    """
    Download content from the specified URL.

    Args:
        url (str): Target URL to download.
        timeout (float): Timeout in seconds. Default is 10 seconds.

    Returns:
        bytes: Downloaded binary data.

    Raises:
        DownloadError: If the download fails.
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise DownloadError(f"{url}: {e}") from e


def save_content(content: bytes, dest_dir: str, filename: str) -> str:
    """
    Save binary data to the specified directory.

    Args:
        content (bytes): Data to save.
        dest_dir (str): Destination directory. Created if it does not exist.
        filename (str): Name of the file to save.

    Returns:
        str: Absolute path to the saved file.
    """
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path


def download_from_url_list(
    url_list_path: str, dest_dir: str, timeout: float = 10.0, prefix: Optional[str] = None
) -> list[str]:
    """
    Download and save content sequentially from a URL list file.

    Args:
        url_list_path (str): Path to the URL list file.
        dest_dir (str): Destination directory for saving files.
        timeout (float): Timeout in seconds. Default is 10 seconds.
        prefix (Optional[str]): Prefix for saved filenames. Default is "file".

    Returns:
        list[str]: List of saved file paths.
    """
    urls = read_url_list(url_list_path)
    saved_files: list[str] = []

    for idx, url in enumerate(urls, 1):
        try:
            logger.info(f"Downloading {idx}/{len(urls)}: {url}")
            content = download_content(url, timeout=timeout)

            # Get file extension from URL (default to .bin if no extension)
            ext = os.path.splitext(url.split("?")[0].split("#")[0])[-1] or ".bin"
            fname = f"{prefix or 'file'}_{idx}{ext}"

            path = save_content(content, dest_dir, fname)
            logger.info(f"Downloaded: {url} -> {path}")
            saved_files.append(path)
        except DownloadError:
            logger.warning(f"Skipping {url} due to download error")
            continue

    logger.info(f"Download completed: {len(saved_files)}/{len(urls)} files downloaded")
    return saved_files

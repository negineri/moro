"""
Utility for sequentially downloading content from a list of URLs.

- Uses httpx
- Type hints and docstrings included
- Logging support
- Designed for testability
- Supports numbered prefixes for downloaded files
- Supports saving downloads as a ZIP archive
"""

import logging
import os
import shutil
import tempfile
import zipfile
from time import sleep
from typing import Optional
from urllib.parse import unquote

import httpx

from moro.modules.number_prefix import generate_number_prefix

logger = logging.getLogger(__name__)

__all__ = [
    "DownloadError",
    "download_content",
    "download_from_url_list",
    "get_filename_with_prefix",
    "is_zip_path",
    "process_files_to_zip",
    "read_url_list",
    "save_content",
]


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


def download_content(url: str, timeout: float = 10.0, sleep_sec: float = 1.0) -> bytes:
    """
    Download content from the specified URL.

    Args:
        url (str): Target URL to download.
        timeout (float): Timeout in seconds. Default is 10 seconds.
        sleep_sec (float): Sleep time in seconds after download. Default is 1 second.

    Returns:
        bytes: Downloaded binary data.

    Raises:
        DownloadError: If the download fails.
    """
    sleep(sleep_sec)
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise DownloadError(f"{url}: {e}") from e


def get_filename_with_prefix(url: str, total_count: int, current_index: int) -> str:
    """
    Generate a filename with prefix based on URL and index information.

    Args:
        url (str): URL to download from.
        total_count (int): Total number of URLs in the list.
        current_index (int): Current processing index (starting from 1).

    Returns:
        str: Filename with prefix.
    """
    # URLからファイル名部分を抽出
    path = url.split("?")[0].split("#")[0]
    filename = os.path.basename(path)
    # URLエンコードされたファイル名をデコード
    filename = unquote(filename)

    # 拡張子を取得(拡張子がない場合は.binをデフォルトとする)
    ext = os.path.splitext(filename)[-1] or ".bin"

    # ベース名部分(拡張子なし)を取得
    basename = os.path.splitext(filename)[0] or "file"

    # プレフィックスを生成
    prefix = generate_number_prefix(total_count, current_index)

    # プレフィックス付きのファイル名を生成して返す
    return f"{prefix}{basename}{ext}"


def is_zip_path(path: str) -> bool:
    """
    Check if a path has a .zip extension.

    Args:
        path (str): Path to check.

    Returns:
        bool: True if the path has a .zip extension, False otherwise.
    """
    return path.lower().endswith(".zip")


def process_files_to_zip(source_files: list[str], zip_path: str) -> str:
    """
    Compress a list of files into a ZIP archive.

    Args:
        source_files (list[str]): List of file paths to include in the ZIP.
        zip_path (str): Path of the destination ZIP file.

    Returns:
        str: Path to the created ZIP file.

    Raises:
        IOError: If there is an error creating the ZIP file.
    """
    try:
        # ZIP ファイルディレクトリを作成
        os.makedirs(os.path.dirname(os.path.abspath(zip_path)), exist_ok=True)

        # ZIP ファイルを作成
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # ファイルを追加
            for file_path in source_files:
                # ベースネームだけを使用して、ディレクトリ構造を ZIP 内に作らない
                zipf.write(file_path, os.path.basename(file_path))
                logger.debug(f"Added to ZIP: {file_path}")

        logger.info(f"Created ZIP archive: {zip_path} with {len(source_files)} files")
        return zip_path
    except Exception as e:
        logger.error(f"Failed to create ZIP file {zip_path}: {e}")
        raise OSError(f"Failed to create ZIP file: {e}") from e


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
    url_list_path: str,
    dest_dir: str,
    timeout: float = 10.0,
    prefix: Optional[str] = None,
    auto_prefix: bool = False,
) -> list[str]:
    """
    Download and save content sequentially from a URL list file.

    If dest_dir ends with .zip, files are saved to a temporary directory
    and then compressed into a ZIP archive.

    Args:
        url_list_path (str): Path to the URL list file.
        dest_dir (str): Destination directory for saving files or path to a ZIP file.
        timeout (float): Timeout in seconds. Default is 10 seconds.
        prefix (Optional[str]): Prefix for saved filenames. Default is "file".
        auto_prefix (bool): Whether to use automatic numbered prefixes. Default is False.

    Returns:
        list[str]: List of saved file paths or a list with the single ZIP file path.
    """
    urls = read_url_list(url_list_path)
    saved_files: list[str] = []

    # ZIP モードかどうかを判断
    zip_mode = is_zip_path(dest_dir)
    temp_dir = None

    try:
        # ZIP モードの場合は一時ディレクトリを作成
        if zip_mode:
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Creating temporary directory for ZIP processing: {temp_dir}")
            download_dest = temp_dir
        else:
            download_dest = dest_dir

        # ダウンロード処理
        for idx, url in enumerate(urls, 1):
            try:
                logger.info(f"Downloading {idx}/{len(urls)}: {url}")
                content = download_content(url, timeout=timeout)

                if auto_prefix:
                    # 連番プレフィックス機能を使用
                    fname = get_filename_with_prefix(url, len(urls), idx)
                else:
                    # 従来のプレフィックス機能を使用
                    path = url.split("?")[0].split("#")[0]
                    original_filename = os.path.basename(path)
                    # URLエンコードされたファイル名をデコード
                    original_filename = unquote(original_filename)
                    ext = os.path.splitext(original_filename)[-1] or ".bin"

                    if prefix is None:
                        # prefixがNoneの場合は元のファイル名を使用
                        fname = original_filename or f"file_{idx}{ext}"
                    else:
                        # prefixが指定されている場合は従来通り
                        fname = f"{prefix}_{idx}{ext}"

                path = save_content(content, download_dest, fname)
                logger.info(f"Downloaded: {url} -> {path}")
                saved_files.append(path)
            except DownloadError:
                logger.warning(f"Skipping {url} due to download error")
                continue

        # ZIP モードの場合は一時ファイルを ZIP 圧縮
        if zip_mode and temp_dir:
            logger.info(f"Compressing {len(saved_files)} files into ZIP: {dest_dir}")
            zip_path = process_files_to_zip(saved_files, dest_dir)
            return [zip_path]

        logger.info(f"Download completed: {len(saved_files)}/{len(urls)} files downloaded")
        return saved_files
    finally:
        # ZIP モードの場合、一時ディレクトリをクリーンアップ
        if zip_mode and temp_dir:
            logger.debug(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)

"""Fantia module for Moro, a Fantia downloader."""

import json
import logging
import mimetypes
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime as dt
from os import makedirs, remove
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from click import echo

logger = logging.getLogger(__name__)

FANTIA_URL_RE = re.compile(r"(?:https?://(?:(?:www\.)?(?:fantia\.jp/(fanclubs|posts)/)))([0-9]+)")
EXTERNAL_LINKS_RE = re.compile(
    r"(?:[\s]+)?((?:(?:https?://)?(?:(?:www\.)?(?:mega\.nz|mediafire\.com|(?:drive|docs)\.google\.com|youtube.com|dropbox.com)\/))[^\s]+)"
)

DOMAIN = "fantia.jp"
BASE_URL = "https://fantia.jp/"

LOGIN_SIGNIN_URL = "https://fantia.jp/sessions/signin"
LOGIN_SESSION_URL = "https://fantia.jp/sessions"

ME_API = "https://fantia.jp/api/v1/me"

FANCLUB_API = "https://fantia.jp/api/v1/fanclubs/{}"
FANCLUBS_FOLLOWING_API = "https://fantia.jp/api/v1/me/fanclubs"
FANCLUBS_PAID_HTML = "https://fantia.jp/mypage/users/plans?type=not_free&page={}"
FANCLUB_POSTS_HTML = "https://fantia.jp/fanclubs/{}/posts?page={}"

POST_API = "https://fantia.jp/api/v1/posts/{}"
POST_URL = "https://fantia.jp/posts/{}"
POSTS_URL = "https://fantia.jp/posts"
POST_RELATIVE_URL = "/posts/"

TIMELINES_API = "https://fantia.jp/api/v1/me/timelines/posts?page={}&per=24"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)

CRAWLJOB_FILENAME = "external_links.crawljob"

MIMETYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}

UNICODE_CONTROL_MAP = dict.fromkeys(range(32))


class FantiaClient(httpx.Client):
    """A synchronous HTTP client for interacting with the Fantia API."""

    def __init__(self, session_id: str, *args: Any, **kwargs: Any) -> None:
        timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)

        # Transport configuration with retry logic
        transport = httpx.HTTPTransport(retries=5, verify=True)

        # Headers configuration
        headers = {
            "User-Agent": USER_AGENT,
            # "Accept": "application/json, text/html, */*",
            # "Accept-Encoding": "gzip, deflate, br",
            # "Connection": "keep-alive",
        }

        cookies = {
            "_session_id": session_id,
        }

        # Initialize synchronous client

        options: dict[str, Any] = {
            "headers": headers,
            "timeout": timeout,
            "transport": transport,
            "follow_redirects": True,
            "limits": httpx.Limits(
                max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0
            ),
            "cookies": cookies,
        }

        super().__init__(*args, **{**kwargs, **options})


@dataclass
class FantiaConfig:
    """Configuration for the Fantia client."""

    directory: str = "downloads/fantia"
    dump_metadata: bool = False
    mark_incomplete_posts: bool = False
    parse_for_external_links: bool = False
    download_thumb: bool = False
    use_server_filenames: bool = False


def _get_csrf_token(client: FantiaClient, post_id: str) -> str:
    """Retrieve the CSRF token from the post HTML."""
    post_html_response = client.get(POST_URL.format(post_id))
    post_html_response.raise_for_status()
    post_html = BeautifulSoup(post_html_response.text, "html.parser")
    csrf_token_tag = post_html.select_one('meta[name="csrf-token"]')
    if csrf_token_tag is None or not csrf_token_tag.has_attr("content"):
        raise ValueError("CSRF token not found in the post HTML.")
    return str(csrf_token_tag["content"])


def sanitize_for_path(value: str, replace: str = " ") -> str:
    """Remove potentially illegal characters from a path."""
    sanitized = re.sub(r"[<>\"\?\\\/\*:|]", replace, value)
    sanitized = sanitized.translate(UNICODE_CONTROL_MAP)
    return re.sub(r"[\s.]+$", "", sanitized)


def _collect_post_titles(post_metadata: Any) -> list[str]:
    """Collect all post titles to check for duplicate names and rename as necessary."""
    post_titles: list[str] = []
    for post in post_metadata["post_contents"]:
        try:
            potential_title = post["title"] or post["parent_post"]["title"]
            if not potential_title:
                potential_title = str(post["id"])
        except KeyError:
            potential_title = str(post["id"])

        title = potential_title
        counter = 2
        while title in post_titles:
            title = potential_title + f"_{counter}"
            counter += 1
        post_titles.append(title)

    return post_titles


def _save_metadata(metadata: Any, directory: str) -> None:
    """Save the metadata for a post to the post's directory."""
    filename = os.path.join(directory, "metadata.json")
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(metadata, file, sort_keys=True, ensure_ascii=False, indent=4)


def _mark_incomplete_post(post_metadata: Any, post_directory: str) -> None:
    """Mark incomplete posts with a .incomplete file."""
    is_incomplete = False
    incomplete_filename = os.path.join(post_directory, ".incomplete")
    for post in post_metadata["post_contents"]:
        if post["visible_status"] != "visible":
            is_incomplete = True
            break
    if is_incomplete:
        if not os.path.exists(incomplete_filename):
            open(incomplete_filename, "a").close()
    else:
        if os.path.exists(incomplete_filename):
            remove(incomplete_filename)


def _download_thumbnail(
    client: httpx.Client, thumb_url: str, post_directory: str, use_server_filenames: bool
) -> None:
    """Download a thumbnail to the post's directory."""
    extension = _process_content_type(client, thumb_url)
    filename = os.path.join(post_directory, "thumb" + extension)
    _perform_download(client, thumb_url, filename, use_server_filename=use_server_filenames)


def _process_content_type(client: httpx.Client, url: str) -> str:
    """Process the Content-Type from a request header and use it to build a filename."""
    url_header = client.head(url, follow_redirects=True)
    mimetype = url_header.headers["Content-Type"]
    return _guess_extension(mimetype, url)


def _guess_extension(mimetype: str, download_url: str) -> str:
    """
    Guess the file extension from the mimetype or force a specific extension for certain mimetypes.

    If the mimetype returns no found extension, guess based on the download URL.
    """
    extension = MIMETYPES.get(mimetype) or mimetypes.guess_extension(mimetype, strict=True)
    if extension is None:
        try:
            path = urlparse(download_url).path
            extension = os.path.splitext(path)[1]
        except IndexError:
            extension = ".unknown"
    return extension


def _perform_download(
    client: httpx.Client,
    url: str,
    filepath: str,
    use_server_filename: bool = False,
    append_server_extension: bool = False,
) -> None:
    """Perform a download for the specified URL while showing progress."""
    url_path = unquote(url.split("?", 1)[0])
    server_filename = os.path.basename(url_path)
    if use_server_filename:
        filepath = os.path.join(os.path.dirname(filepath), server_filename)

    with client.stream("GET", url) as response:
        if response.status_code == 404:
            logger.info("Download URL returned 404. Skipping...\n")
            return
        response.raise_for_status()

        # Handle redirects so we can properly catch an excluded filename
        # Attachments typically route from fantia.jp/posts/#/download/#
        # Images typically are served directly from cc.fantia.jp
        # Metadata images typically are served from c.fantia.jp
        if str(response.url) != url:
            url_path = unquote(str(response.url).split("?", 1)[0])
            server_filename = os.path.basename(url_path)
            if use_server_filename:
                filepath = os.path.join(os.path.dirname(filepath), server_filename)

        if not use_server_filename and append_server_extension:
            filepath += _guess_extension(response.headers["Content-Type"], url)

        file_size = int(response.headers["Content-Length"])
        if os.path.isfile(filepath) and os.stat(filepath).st_size == file_size:
            logger.info(f"File found (skipping): {filepath}\n")
            return

        logger.info(f"File: {filepath}\n")
        incomplete_filename = filepath + ".part"

        downloaded = 0
        with open(incomplete_filename, "wb") as file:
            for chunk in response.iter_bytes():
                downloaded += len(chunk)
                file.write(chunk)

        if downloaded != file_size:
            raise Exception(
                f"Downloaded file size mismatch (expected {file_size}, got {downloaded})"
            )

        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(incomplete_filename, filepath)

        modification_time_string = response.headers["Last-Modified"]
        modification_time = int(
            dt.strptime(modification_time_string, "%a, %d %b %Y %H:%M:%S %Z").timestamp()
        )
        if modification_time:
            access_time = int(time.time())
            os.utime(filepath, times=(access_time, modification_time))


def _parse_external_links(post_description: str, post_directory: str, directory: str) -> None:
    """Parse the post description for external links, e.g. Mega and Google Drive links."""
    link_matches = EXTERNAL_LINKS_RE.findall(post_description)
    if link_matches:
        logger.info(f"Found {len(link_matches)} external link(s) in post. Saving...\n")
        _build_crawljob(link_matches, directory, post_directory)


def _build_crawljob(links: list[Any], root_directory: str, post_directory: str) -> None:
    """Append to a root .crawljob file with external links gathered from a post."""
    filename = os.path.join(root_directory, CRAWLJOB_FILENAME)
    with open(filename, "a", encoding="utf-8") as file:
        for link in links:
            crawl_dict: dict[str, str] = {
                "packageName": "Fantia",
                "text": link,
                "downloadFolder": post_directory,
                "enabled": "true",
                "autoStart": "true",
                "forcedStart": "true",
                "autoConfirm": "true",
                "addOfflineLink": "true",
                "extractAfterDownload": "false",
            }

            for key, value in crawl_dict.items():
                file.write(key + "=" + value + "\n")
            file.write("\n")


def _download_post_content(
    client: httpx.Client,
    post_json: Any,
    post_directory: str,
    post_title: str,
    directory: str,
    parse_for_external_links: bool,
    use_server_filenames: bool,
) -> bool:
    """Parse the post's content to determine whether to save the content as a photo or file."""
    logger.info(f"> Content {post_json['id']}\n")

    if post_json["visible_status"] != "visible":
        logger.info("Post content not available on current plan. Skipping...\n")
        return False

    if post_json.get("category"):
        if post_json["category"] == "photo_gallery":
            photo_gallery = post_json["post_content_photos"]
            photo_counter = 0
            gallery_directory = os.path.join(post_directory, sanitize_for_path(post_title))
            os.makedirs(gallery_directory, exist_ok=True)
            for photo in photo_gallery:
                photo_url = photo["url"]["original"]
                _download_photo(
                    client, photo_url, photo_counter, gallery_directory, use_server_filenames
                )
                photo_counter += 1
        elif post_json["category"] == "file":
            filename = os.path.join(post_directory, post_json["filename"])
            download_url = urljoin(POSTS_URL, post_json["download_uri"])
            _download_file(client, download_url, filename, post_directory)
        elif post_json["category"] == "embed":
            if parse_for_external_links:
                # TODO: Check what URLs are allowed as embeds
                link_as_list = [post_json["embed_url"]]
                logger.info(
                    "Adding embedded link {} to {}.\n".format(
                        post_json["embed_url"], CRAWLJOB_FILENAME
                    )
                )
                _build_crawljob(link_as_list, directory, post_directory)
        elif post_json["category"] == "blog":
            blog_comment = post_json["comment"]
            blog_json = json.loads(blog_comment)
            photo_counter = 0
            gallery_directory = os.path.join(post_directory, sanitize_for_path(post_title))
            os.makedirs(gallery_directory, exist_ok=True)
            for op in blog_json["ops"]:
                if type(op["insert"]) is dict and op["insert"].get("fantiaImage"):
                    photo_url = urljoin(BASE_URL, op["insert"]["fantiaImage"]["original_url"])
                    _download_photo(
                        client, photo_url, photo_counter, gallery_directory, use_server_filenames
                    )
                    photo_counter += 1
        else:
            logger.info(
                'Post content category "{}" is not supported. Skipping...\n'.format(
                    post_json.get("category")
                )
            )
            return False

    if parse_for_external_links:
        post_description = post_json["comment"] or ""
        _parse_external_links(post_description, os.path.abspath(post_directory), directory)

    return True


def _download_photo(
    client: httpx.Client,
    photo_url: str,
    photo_counter: int,
    gallery_directory: str,
    use_server_filenames: bool,
) -> None:
    """Download a photo to the post's directory."""
    extension = _process_content_type(client, photo_url)
    filename = (
        os.path.join(gallery_directory, str(photo_counter) + extension) if gallery_directory else ""
    )
    _perform_download(client, photo_url, filename, use_server_filename=use_server_filenames)


def _download_file(
    client: httpx.Client, download_url: str, filename: str, post_directory: str
) -> None:
    """Download a file to the post's directory."""
    _perform_download(
        client, download_url, filename, use_server_filename=True
    )  # Force serve filenames to prevent duplicate collision


def login(client: FantiaClient) -> bool:
    """Check if the session is valid by fetching the user data."""
    check_user = client.get(ME_API)
    if not (check_user.is_success or check_user.status_code == 304):
        logger.error("Error: Invalid session. Please verify your session cookie")
        return False
    return True


def download_post(client: FantiaClient, post_id: str, config: FantiaConfig) -> None:
    """Download a post to its own directory."""
    echo(f"Downloading post {post_id}...\n")

    csrf_token = _get_csrf_token(client, post_id)

    response = client.get(
        POST_API.format(post_id),
        headers={"X-CSRF-Token": csrf_token, "X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    post_json = json.loads(response.text)["post"]

    post_id = post_json["id"]
    post_creator = post_json["fanclub"]["creator_name"]
    post_title = post_json["title"]
    post_contents = post_json["post_contents"]

    # post_posted_at = int(parsedate_to_datetime(post_json["posted_at"]).timestamp())
    # post_converted_at = (
    #     int(dt.fromisoformat(post_json["converted_at"]).timestamp())
    #     if post_json["converted_at"]
    #     else post_posted_at
    # )

    post_directory_title = sanitize_for_path(str(post_id))

    post_directory = os.path.join(
        config.directory, sanitize_for_path(post_creator), post_directory_title
    )
    makedirs(post_directory, exist_ok=True)

    post_titles = _collect_post_titles(post_json)

    if config.dump_metadata:
        _save_metadata(post_json, post_directory)
    if config.mark_incomplete_posts:
        _mark_incomplete_post(post_json, post_directory)
    if config.download_thumb and post_json["thumb"]:
        _download_thumbnail(
            client, post_json["thumb"]["original"], post_directory, config.use_server_filenames
        )
    if config.parse_for_external_links:
        # Main post
        post_description = post_json["comment"] or ""
        _parse_external_links(post_description, os.path.abspath(post_directory), config.directory)

    download_complete_counter = 0
    for post_index, post in enumerate(post_contents):
        post_title = post_titles[post_index]
        if _download_post_content(
            client,
            post,
            post_directory,
            post_title,
            config.directory,
            config.parse_for_external_links,
            config.use_server_filenames,
        ):
            download_complete_counter += 1

    if not os.listdir(post_directory):
        logger.info(f"No content downloaded for post {post_id}. Deleting directory.\n")
        os.rmdir(post_directory)

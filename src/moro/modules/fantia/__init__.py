"""Fantia module."""

import json
import logging
import os
import re
import time
from datetime import datetime as dt
from email.utils import parsedate_to_datetime
from os import makedirs
from pathlib import Path
from typing import Annotated, Any, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from injector import inject, singleton
from selenium import webdriver

from moro.modules.fantia.config import (
    BASE_URL,
    DOMAIN,
    FANCLUB_POSTS_HTML,
    LOGIN_SIGNIN_URL,
    ME_API,
    POST_API,
    POST_URL,
    UNICODE_CONTROL_MAP,
    USER_AGENT,
    FantiaConfig,
)
from moro.modules.fantia.domain import (
    FantiaFile,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaProduct,
    FantiaText,
    FantiaURL,
    SessionIdProvider,
)

logger = logging.getLogger(__name__)


@singleton
class FantiaClient(httpx.Client):
    """A synchronous HTTP client for interacting with the Fantia API."""

    @inject
    def __init__(self, config: FantiaConfig, session_provider: SessionIdProvider) -> None:
        timeout = httpx.Timeout(
            connect=config.timeout_connect,
            read=config.timeout_read,
            write=config.timeout_write,
            pool=config.timeout_pool,
        )

        # Transport configuration with retry logic
        transport = httpx.HTTPTransport(retries=config.max_retries, verify=True)

        # Headers configuration
        headers = {
            "User-Agent": USER_AGENT,
            # "Accept": "application/json, text/html, */*",
            # "Accept-Encoding": "gzip, deflate, br",
            # "Connection": "keep-alive",
        }

        # Store session provider for dynamic session_id retrieval
        self._session_provider = session_provider

        cookies: dict[str, str] = {}
        if config.session_id:
            cookies["_session_id"] = config.session_id

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

        super().__init__(**options)

    def _update_cookies(self) -> None:
        """Update all cookies with current values from the provider."""
        if self._session_provider:
            cookies = self._session_provider.get_cookies()

            # Define target cookies that should be managed
            target_cookies = ["_session_id", "jp_chatplus_vtoken", "_f_v_k_1"]

            for cookie_name in target_cookies:
                if cookie_name in cookies:
                    # Set the cookie if it exists in provider
                    self.cookies.set(cookie_name, cookies[cookie_name], domain=DOMAIN)
                else:
                    # Remove the cookie if it doesn't exist in provider
                    if cookie_name in self.cookies:
                        self.cookies.delete(cookie_name, domain=DOMAIN)

    def get(self, url: httpx.URL | str, **kwargs: Any) -> httpx.Response:
        """Override get method to automatically retry with updated cookies on 401 errors."""
        # First attempt
        response = super().get(url, **kwargs)

        # Check if we got a 401 Unauthorized and have a session provider
        if response.status_code == 401:
            logger.info("Received 401 Unauthorized, attempting to refresh cookies")

            # Try to get new cookies from the provider
            new_cookies = self._session_provider.get_cookies()
            if new_cookies.get("_session_id"):
                # Update all cookies
                self._update_cookies()
                logger.info("Updated cookies, retrying request")

                # Retry the request once with the new cookies
                response = super().get(url, **kwargs)

                if response.status_code == 401:
                    logger.warning("Request still failed after cookie refresh")
                else:
                    logger.info("Request succeeded after cookie refresh")
            else:
                logger.warning("Unable to get new session_id from provider")

        return response


def get_csrf_token(client: FantiaClient, post_id: str) -> str:
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


# def _parse_external_links(post_description: str, post_directory: str, directory: str) -> None:
#     """Parse the post description for external links, e.g. Mega and Google Drive links."""
#     link_matches = EXTERNAL_LINKS_RE.findall(post_description)
#     if link_matches:
#         logger.info(f"Found {len(link_matches)} external link(s) in post. Saving...\n")
#         _build_crawljob(link_matches, directory, post_directory)


# def _build_crawljob(links: list[Any], root_directory: str, post_directory: str) -> None:
#     """Append to a root .crawljob file with external links gathered from a post."""
#     filename = os.path.join(root_directory, CRAWLJOB_FILENAME)
#     with open(filename, "a", encoding="utf-8") as file:
#         for link in links:
#             crawl_dict: dict[str, str] = {
#                 "packageName": "Fantia",
#                 "text": link,
#                 "downloadFolder": post_directory,
#                 "enabled": "true",
#                 "autoStart": "true",
#                 "forcedStart": "true",
#                 "autoConfirm": "true",
#                 "addOfflineLink": "true",
#                 "extractAfterDownload": "false",
#             }
#
#             for key, value in crawl_dict.items():
#                 file.write(key + "=" + value + "\n")
#             file.write("\n")


def check_login(client: FantiaClient) -> bool:
    """Check if the session is valid by fetching the user data."""
    check_user = client.get(ME_API)
    if not (check_user.is_success or check_user.status_code == 304):
        logger.error("Error: Invalid session. Please verify your session cookie")
        return False
    return True


def login_fantia(client: FantiaClient, options: webdriver.ChromeOptions) -> bool:
    """Login to Fantia using Selenium and set the session cookies."""
    check_user = client.get(ME_API)
    if check_user.is_success or check_user.status_code == 304:
        return True
    with webdriver.Chrome(options=options) as driver:
        driver.get(LOGIN_SIGNIN_URL)
        while True:
            parsed_url = urlparse(driver.current_url)
            if parsed_url.path == "/" and parsed_url.netloc == DOMAIN:
                # Successfully logged in
                cookies: list[dict[str, str]] = driver.get_cookies()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                client.cookies.clear()  # Clear existing cookies
                for cookie in cookies:
                    if (
                        cookie["name"] == "_session_id"
                        or cookie["name"] == "jp_chatplus_vtoken"
                        or cookie["name"] == "_f_v_k_1"
                    ):
                        client.cookies.set(cookie["name"], cookie["value"], domain=DOMAIN)
                    elif (
                        cookie["name"] == "cvi"
                        or cookie["name"] == "gid"
                        or cookie["name"] == "lamp"
                    ):
                        continue  # These cookies are not needed for the Fantia API
                    else:
                        continue
                break
        return True

    return False


def create_chrome_options(userdata: str) -> webdriver.ChromeOptions:
    """Create Chrome options for the Fantia login."""
    makedirs(userdata, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={userdata}")
    return options


def _fetch_post_data(client: FantiaClient, post_id: str) -> dict[str, Any]:
    """Fetch post data from the API."""
    if not check_login(client):
        raise ValueError("Invalid session. Please verify your session cookie.")
    logger.info(f"Parsing post {post_id}...")
    csrf_token = get_csrf_token(client, post_id)
    response = client.get(
        POST_API.format(post_id),
        headers={"X-CSRF-Token": csrf_token, "X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    post: dict[str, Any] = json.loads(response.text)["post"]
    return post


def _extract_post_metadata(post_json: dict[str, Any]) -> dict[str, Any]:
    """Extract basic metadata from post JSON."""
    post_id = post_json["id"]
    post_creator = post_json["fanclub"]["creator_name"]
    post_creator_id = post_json.get("fanclub", {}).get("id", "")
    post_title = post_json["title"]
    post_contents = post_json["post_contents"]
    post_posted_at = int(parsedate_to_datetime(post_json["posted_at"]).timestamp())
    post_converted_at = (
        int(dt.fromisoformat(post_json["converted_at"]).timestamp())
        if post_json["converted_at"]
        else post_posted_at
    )
    post_comment = post_json.get("comment", None)

    return {
        "id": post_id,
        "creator": post_creator,
        "creator_id": post_creator_id,
        "title": post_title,
        "contents": post_contents,
        "posted_at": post_posted_at,
        "converted_at": post_converted_at,
        "comment": post_comment,
    }


def _validate_post_type(post_json: dict[str, Any], post_id: str) -> None:
    """Validate that the post is not a blog post."""
    if post_json.get("is_blog") is not False:
        logger.error("Post is a blog post!\n")
        raise NotImplementedError(f"Blog posts are not supported yet. Post ID: {post_id}")


def _parse_post_thumbnail(post_json: dict[str, Any]) -> FantiaURL | None:
    """Parse thumbnail from post JSON."""
    if post_json.get("thumb"):
        thumb_url = post_json["thumb"]["original"]
        return FantiaURL(url=thumb_url, ext=Path(thumb_url).suffix)
    return None


def _parse_post_contents(
    post_contents: list[dict[str, Any]], post_id: str
) -> tuple[list[FantiaPhotoGallery], list[FantiaFile], list[FantiaText], list[FantiaProduct]]:
    """Parse all post contents by category."""
    contents_photo_gallery: list[FantiaPhotoGallery] = []
    contents_files: list[FantiaFile] = []
    contents_text: list[FantiaText] = []
    contents_products: list[FantiaProduct] = []

    for content in post_contents:
        if content["visible_status"] != "visible":
            logger.info(
                f"Post content {content['id']} is not available on current plan. Skipping..."
            )
            continue
        if content["category"] == "photo_gallery":
            contents_photo_gallery.append(_parse_photo_gallery(content))
        elif content["category"] == "file":
            contents_files.append(_parse_file(content))
        elif content["category"] == "text":
            contents_text.append(_parse_text(content))
        elif content["category"] == "product":
            contents_products.append(_parse_product(content))
        else:
            raise NotImplementedError(
                f"Post content category '{content['category']}' is not supported yet. "
                f"Post ID: {post_id}"
            )

    return contents_photo_gallery, contents_files, contents_text, contents_products


def parse_post(client: FantiaClient, post_id: str) -> FantiaPostData:
    """Parse a post and return its data."""
    post_json = _fetch_post_data(client, post_id)
    metadata = _extract_post_metadata(post_json)
    _validate_post_type(post_json, str(metadata["id"]))

    post_thumbnail = _parse_post_thumbnail(post_json)
    contents_photo_gallery, contents_files, contents_text, contents_products = _parse_post_contents(
        metadata["contents"], str(metadata["id"])
    )

    return FantiaPostData(
        id=str(metadata["id"]),
        title=metadata["title"],
        creator_name=metadata["creator"],
        creator_id=str(metadata["creator_id"]),
        contents=metadata["contents"],
        contents_photo_gallery=contents_photo_gallery,
        contents_files=contents_files,
        contents_text=contents_text,
        contents_products=contents_products,
        posted_at=metadata["posted_at"],
        converted_at=metadata["converted_at"],
        comment=metadata["comment"],
        thumbnail=post_thumbnail,
    )


def _parse_product(post_content: dict[str, Any]) -> FantiaProduct:
    """Parse a product post content and return a FantiaProduct object."""
    title = post_content.get("title", "")
    if title is None:
        title = ""
    url = urljoin(BASE_URL, post_content["product"].get("uri", ""))
    name = post_content["product"].get("name", "")
    return FantiaProduct(
        id=str(post_content["id"]),
        title=title,
        comment=post_content.get("comment", None),
        name=name,
        url=url,
    )


def _parse_text(post_content: dict[str, Any]) -> FantiaText:
    """Parse a text post content and return a FantiaText object."""
    title = post_content.get("title", "")
    if title is None:
        title = ""
    return FantiaText(
        id=str(post_content["id"]),
        title=title,
        comment=post_content.get("comment", None),
    )


def _parse_file(post_content: dict[str, Any]) -> FantiaFile:
    """Parse a file post content and return a FantiaFile object."""
    path: str = post_content["download_uri"]
    url = urljoin(BASE_URL, path)
    ext = Path(path).suffix
    title = post_content.get("title", "")
    if title is None:
        title = ""
    return FantiaFile(
        id=str(post_content["id"]),
        title=title,
        comment=post_content.get("comment", None),
        url=url,
        name=post_content.get("filename", f"file_{post_content['id']}{ext}"),
    )


def _parse_photo_gallery(post_content: dict[str, Any]) -> FantiaPhotoGallery:
    """Parse a photo gallery post content and return a FantiaPhotoGallery object."""
    title = post_content.get("title", "")
    if title is None:
        title = ""

    photos: list[FantiaURL] = []
    for photo in post_content["post_content_photos"]:
        url: str = photo["url"]["original"]
        path = urlparse(url).path
        ext = Path(path).suffix
        photos.append(FantiaURL(url=url, ext=ext))
    return FantiaPhotoGallery(
        id=str(post_content["id"]),
        title=title,
        comment=post_content.get("comment", None),
        photos=photos,
    )


def _perform_download(client: httpx.Client, url: str, path: str) -> None:
    """Perform a download for the specified URL while showing progress."""
    with client.stream("GET", url) as response:
        if response.status_code == 404:
            logger.info("Thumbnail URL returned 404. Skipping...\n")
            return
        response.raise_for_status()

        file_size = int(response.headers["Content-Length"])
        downloaded = 0
        with open(path, mode="wb") as f:
            for chunk in response.iter_bytes():
                downloaded += len(chunk)
                f.write(chunk)

            if downloaded != file_size:
                raise Exception(
                    f"Downloaded thumbnail size mismatch (expected {file_size}, got {downloaded})"
                )


def download_thumbnail(client: httpx.Client, post_path: str, post_content: FantiaPostData) -> None:
    """Download the thumbnail of a post to the specified directory."""
    if post_content.thumbnail is not None:
        thumb_url = post_content.thumbnail.url
        ext = post_content.thumbnail.ext
        file_path = os.path.join(post_path, "0000_thumb" + ext)
        _perform_download(client, thumb_url, file_path)
    else:
        logger.info("No thumbnail found for this post. Skipping...\n")


def download_file(client: httpx.Client, post_path: str, post_content: FantiaFile) -> None:
    """Download a file to the specified directory."""
    if post_content.comment is not None:
        file_path = post_path + "/comment.txt"
        with open(file_path, mode="w") as f:
            f.write(post_content.comment)

    download_url = post_content.url
    file_name = post_content.name
    file_path = os.path.join(post_path, file_name)
    _perform_download(client, download_url, file_path)


def download_photo_gallery(
    client: httpx.Client, post_path: str, post_content: FantiaPhotoGallery
) -> None:
    """Download a photo gallery to the specified directory."""
    if post_content.comment is not None:
        file_path = post_path + "/comment.txt"
        with open(file_path, mode="w") as f:
            f.write(post_content.comment)
    for index, photo in enumerate(post_content.photos):
        _perform_download(
            client,
            photo.url,
            os.path.join(post_path, f"{index:03d}{photo.ext}"),
        )


def get_posts_by_user(client: FantiaClient, user_id: str, interval: float = 0) -> list[str]:
    """Get all post ids by a user."""
    if not check_login(client):
        raise ValueError("Invalid session. Please verify your session cookie.")
    logger.info(f"Fetching posts for user {user_id}...\n")

    posts: list[str] = []
    page = 1
    while True:
        logger.info(f"Fetching page {page}...")
        response = client.get(FANCLUB_POSTS_HTML.format(user_id, page))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        post_elements = soup.select("div.post")
        if not post_elements:
            break

        for post_element in post_elements:
            post_title_ele = post_element.select_one(".post-title")
            if post_title_ele is None:
                logger.warning("Post title not found. Skipping post.")
                continue
            post_title = post_title_ele.string
            if post_title is None:
                logger.warning("Post title is None. Skipping post.")
                continue

            post_href_ele = post_element.select_one("a.link-block")
            if post_href_ele is None:
                logger.warning("Post link not found. Skipping post.")
                continue
            post_href = post_href_ele.get("href")
            if post_href is None:
                logger.warning("Post link is None. Skipping post.")
                continue

            post_id = Path(str(post_href)).name
            posts.append(post_id)

        page += 1
        time.sleep(interval)

    return posts

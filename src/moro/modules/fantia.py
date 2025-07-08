"""Fantia module for Moro, a Fantia downloader."""

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime as dt
from email.utils import parsedate_to_datetime
from os import makedirs
from typing import Annotated, Any, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from injector import inject, singleton
from pydantic import BaseModel, Field
from selenium import webdriver
from trio import Path

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


@singleton
@dataclass
class FantiaConfig:
    """Configuration for the Fantia client."""

    session_id: Optional[str] = None
    directory: str = "downloads/fantia"
    dump_metadata: bool = False
    mark_incomplete_posts: bool = False
    parse_for_external_links: bool = False
    download_thumb: bool = False
    use_server_filenames: bool = False
    priorize_webp: bool = False


class FantiaClient(httpx.Client):
    """A synchronous HTTP client for interacting with the Fantia API."""

    @inject
    def __init__(self, config: FantiaConfig) -> None:
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


def _check_login(client: FantiaClient) -> bool:
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


class FantiaURL(BaseModel):
    """Data model for Fantia post file."""

    url: Annotated[str, Field(description="The URL to download the file")]
    ext: Annotated[str, Field(description="The file extension")]


class FantiaPhotoGallery(BaseModel):
    """Data model for Fantia post photo gallery."""

    id: Annotated[str, Field(description="The ID of the photo")]
    title: Annotated[str, Field(description="The title of the photo")]
    comment: Annotated[Optional[str], Field(description="The comment of the photo")]
    photos: Annotated[list[FantiaURL], Field(description="The URLs of the photos in the gallery")]


class FantiaFile(BaseModel):
    """Data model for Fantia post file."""

    id: Annotated[str, Field(description="The ID of the file")]
    title: Annotated[str, Field(description="The title of the file")]
    comment: Annotated[Optional[str], Field(description="The comment of the file")]
    url: Annotated[str, Field(description="The URL to download the file")]
    name: Annotated[str, Field(description="The name of the file")]


class FantiaText(BaseModel):
    """Data model for Fantia post text content."""

    id: Annotated[str, Field(description="The ID of the text content")]
    title: Annotated[str, Field(description="The title of the text content")]
    comment: Annotated[Optional[str], Field(description="The comment of the text content")]


class FantiaProduct(BaseModel):
    """Data model for Fantia product."""

    id: Annotated[str, Field(description="The ID of the product")]
    title: Annotated[str, Field(description="The title of the product")]
    comment: Annotated[Optional[str], Field(description="The comment of the product")]
    name: Annotated[str, Field(description="The name of the product")]
    url: Annotated[str, Field(description="The URL of the product")]


class FantiaPostData(BaseModel):
    """Data model for Fantia post data."""

    id: Annotated[str, Field(description="The ID of the post")]
    title: Annotated[str, Field(description="The title of the post")]
    creator_name: Annotated[str, Field(description="The name of the post creator")]
    creator_id: Annotated[str, Field(description="The ID of the post creator")]
    contents: Annotated[list[Any], Field(description="The contents of the post")]
    contents_photo_gallery: Annotated[
        list[FantiaPhotoGallery], Field(description="The photo gallery of the post")
    ]
    contents_files: Annotated[list[FantiaFile], Field(description="The files of the post")]
    contents_text: Annotated[list[FantiaText], Field(description="The text contents of the post")]
    contents_products: Annotated[list[FantiaProduct], Field(description="The products of the post")]
    posted_at: Annotated[int, Field(description="The timestamp when the post was created")]
    converted_at: Annotated[int, Field(description="The timestamp when the post was converted")]
    comment: Annotated[Optional[str], Field(description="The comment of the post")]
    thumbnail: Annotated[Optional[FantiaURL], Field(description="The URL of the post thumbnail")]


def parse_post(client: FantiaClient, post_id: str, priorize_webp: bool) -> FantiaPostData:
    """Parse a post and return its data."""
    if not _check_login(client):
        raise ValueError("Invalid session. Please verify your session cookie.")
    logger.info(f"Parsing post {post_id}...")
    csrf_token = get_csrf_token(client, post_id)
    response = client.get(
        POST_API.format(post_id),
        headers={"X-CSRF-Token": csrf_token, "X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    post_json: dict[str, Any] = json.loads(response.text)["post"]

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
    if post_json.get("is_blog") is not False:
        logger.error("Post is a blog post!\n")
        raise NotImplementedError(f"Blog posts are not supported yet. Post ID: {post_id}")

    contents_photo_gallery: list[FantiaPhotoGallery] = []
    contents_files: list[FantiaFile] = []
    contents_text: list[FantiaText] = []
    contents_products: list[FantiaProduct] = []
    post_thumbnail: Optional[FantiaURL] = None
    if post_json.get("thumb"):
        thumb_url = post_json["thumb"]["original"]
        post_thumbnail = FantiaURL(url=thumb_url, ext=Path(thumb_url).suffix)
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
                (
                    f"Post content category '{content['category']}' is not supported yet.",
                    f"Post ID: {post_id}",
                )
            )

    return FantiaPostData(
        id=str(post_id),
        title=post_title,
        creator_name=post_creator,
        creator_id=str(post_creator_id),
        contents=post_contents,
        contents_photo_gallery=contents_photo_gallery,
        contents_files=contents_files,
        contents_text=contents_text,
        contents_products=contents_products,
        posted_at=post_posted_at,
        converted_at=post_converted_at,
        comment=post_comment,
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


def get_posts_by_user(client: FantiaClient, user_id: str, interval: float = 1) -> list[str]:
    """Get all post ids by a user."""
    if not _check_login(client):
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

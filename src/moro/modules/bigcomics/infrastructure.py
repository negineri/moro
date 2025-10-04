"""Infrastructure for BigComics module."""

import re
from asyncio import sleep
from base64 import b64decode
from datetime import datetime
from logging import getLogger
from pathlib import Path

from injector import inject
from playwright.async_api import (
    BrowserContext,
    Cookie,
    ElementHandle,
    Page,
    Playwright,
    ViewportSize,
    async_playwright,
    expect,
)
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from moro.modules.bigcomics.config import BigComicsConfig
from moro.modules.common import CommonConfig, CommonDBEngine

logger = getLogger(__name__)

EPISODE_ENDPOINT = "https://bigcomics.jp/episodes/{episode_id}/"
SERIES_ENDPOINT = "https://bigcomics.jp/series/{series_id}/pagingList?s=2&page={page}&limit=50"
RE_EPISODE_ID = re.compile(r"\/episodes\/([^\/]+)\/")


async def check_require_auth(page: Page) -> bool:
    """Check if authentication is required."""
    if await page.query_selector(".charge-box-inner"):
        return False
    return True


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class CookieORM(Base):
    """Cookie ORM model."""

    __tablename__ = "cookies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    value: Mapped[str]
    domain: Mapped[str]
    path: Mapped[str]
    expires: Mapped[float]
    http_only: Mapped[bool]
    secure: Mapped[bool]
    same_site: Mapped[str]
    partition_key: Mapped[str | None]

    def to_playwright_cookie(self) -> Cookie:
        """Convert CookieORM to Playwright Cookie."""
        if self.partition_key is None:
            return {
                "name": self.name,
                "value": self.value,
                "domain": self.domain,
                "path": self.path,
                "expires": self.expires,
                "httpOnly": self.http_only,
                "secure": self.secure,
                "sameSite": self.same_site,  # type: ignore
            }
        return {
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "path": self.path,
            "expires": self.expires,
            "httpOnly": self.http_only,
            "secure": self.secure,
            "sameSite": self.same_site,  # type: ignore
            "partitionKey": self.partition_key,
        }

    def from_playwright_cookie(self, cookie: Cookie) -> "CookieORM":
        """Create CookieORM from Playwright Cookie."""
        self.name = cookie["name"]  # pyright: ignore
        self.value = cookie["value"]  # pyright: ignore
        self.domain = cookie["domain"]  # pyright: ignore
        self.path = cookie["path"]  # pyright: ignore
        self.expires = cookie["expires"]  # pyright: ignore
        self.http_only = cookie["httpOnly"]  # pyright: ignore
        self.secure = cookie["secure"]  # pyright: ignore
        self.same_site = cookie["sameSite"]  # pyright: ignore
        self.partition_key = cookie.get("partitionKey", None)
        return self


class AuthError(Exception):
    """Custom exception for authentication errors."""


@inject
class BigComicsRepository:
    """Repository for BigComics."""

    def __init__(
        self,
        common_config: CommonConfig,
        bigcomics_config: BigComicsConfig,
        common_db_engine: CommonDBEngine,
    ) -> None:
        self._user_data_dir = Path(common_config.user_cache_dir) / bigcomics_config.user_data_dir
        self._output_dir = bigcomics_config.output_dir
        self._viewport = ViewportSize(
            width=bigcomics_config.viewport_width, height=bigcomics_config.viewport_height
        )
        self._user_agent = bigcomics_config.user_agent
        self._timeout_ms = bigcomics_config.timeout_ms
        self._engine = common_db_engine
        Base.metadata.create_all(self._engine)

    async def _login(self, playwright: Playwright) -> None:
        """Login to BigComics."""
        context = await self._launch_browser(playwright, headless=False)
        page = await context.new_page()
        await page.goto("https://bigcomics.jp/signin")
        page.set_default_timeout(0)
        await page.wait_for_selector(".g-icon-bookshelf")
        await self._close_browser(context)

    async def _launch_browser(
        self, playwright: Playwright, *, headless: bool = True
    ) -> BrowserContext:
        """Launch browser."""
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=self._user_data_dir,
            viewport=self._viewport,
            user_agent=self._user_agent,
            device_scale_factor=2,
            headless=headless,
        )
        with Session(self._engine) as session:
            cookies = session.scalars(select(CookieORM)).all()
            await context.add_cookies([cookie.to_playwright_cookie() for cookie in cookies])  # type: ignore
        return context

    async def _close_browser(self, context: BrowserContext) -> None:
        """Close browser context."""
        with Session(self._engine) as session:
            for cookie in await context.cookies():
                cookie_orm = session.scalar(
                    select(CookieORM)
                    .filter_by(name=cookie["name"])  # pyright: ignore
                    .filter_by(domain=cookie["domain"])  # pyright: ignore
                    .filter_by(path=cookie["path"])  # pyright: ignore
                )
                if cookie_orm:
                    cookie_orm.from_playwright_cookie(cookie)
                else:
                    session.add(CookieORM().from_playwright_cookie(cookie))
            session.commit()

        await context.close()

    async def fetch_episode(self, episode_id: str) -> None:
        """Fetch episode by ID."""
        for _ in range(5):
            try:
                await self._fetch_episode(episode_id)
            except AuthError:
                logger.warning(f"Authentication error occurred while fetching episode {episode_id}")
                async with async_playwright() as p:
                    await self._login(p)
            except Exception as e:
                logger.error(f"Failed to fetch episode {episode_id}: {e}")
            else:
                break

            logger.info("Retrying in 1 minute...")
            await sleep(60)

    async def _fetch_episode(self, episode_id: str) -> None:
        """Fetch episode by ID."""
        async with async_playwright() as p:
            # browser = await p.chromium.launcht()
            # context = await browser.new_context(
            #     viewport=self._viewport, user_agent=self._user_agent, device_scale_factor=2
            # )
            context = await self._launch_browser(p)
            page = await context.new_page()
            page.set_default_timeout(self._timeout_ms)

            await page.goto(EPISODE_ENDPOINT.format(episode_id=episode_id))
            series_title = await _get_series_title(page)
            if not series_title:
                await self._close_browser(context)
                raise ValueError("Failed to get series title")
            if not await check_require_auth(page):
                await self._close_browser(context)
                raise AuthError("Authentication required")

            page_total = await _get_page_total(page)
            article_title = await _get_article_title(page)
            if not article_title:
                return
            publish_date = await _get_publish_date(page)
            if publish_date is None:
                return
            episode_path = (
                self._output_dir
                / Path(series_title)
                / Path(f"{publish_date.strftime('%Y-%m-%d')}_{article_title}")
            )

            for _ in range(1, page_total):
                # Reset page
                await page.keyboard.press("ArrowRight")
                page_current_ele = await page.wait_for_selector(".-cv-f-page-current")
                if page_current_ele and (await page_current_ele.inner_text()) == "1":
                    break

            for _ in range(1, page_total):
                await page.keyboard.press("ArrowLeft")
                # await sleep(0.3)
                xcv_pages = await page.wait_for_selector("#xCVPages")
                if xcv_pages is None:
                    logger.error("Failed to find xCVPages element")
                    return
                cv_pages = await xcv_pages.query_selector_all(".-cv-page")
                await _save_cv_pages(cv_pages, episode_path)
                page_current_ele = await page.wait_for_selector(".-cv-f-page-current")
                if page_current_ele and (await page_current_ele.inner_text()) == str(page_total):
                    break
            await self._close_browser(context)

    async def fetch_series(self, series_id: str) -> list[str]:
        """Fetch series by ID."""
        async with async_playwright() as p:
            context = await self._launch_browser(p)
            page = await context.new_page()
            page.set_default_timeout(self._timeout_ms)
            page_num = 0
            series_ids: list[str] = []

            while True:
                logger.info(f"Fetching series page {page_num}")
                await page.goto(SERIES_ENDPOINT.format(series_id=series_id, page=page_num))
                await page.wait_for_selector(".series-ep-list")
                episode_elements = await page.query_selector_all("a.article-ep-list-item-img-link")
                for index, episode_ele in enumerate(episode_elements):
                    href = await episode_ele.get_attribute("href")
                    if href is None:
                        logger.error(f"Failed to get href attribute page:{page_num}, index:{index}")
                        continue
                    match = RE_EPISODE_ID.search(href)
                    if match is None:
                        logger.error(f"Failed to parse episode ID from href: {href}")
                        continue
                    episode_id: str = match.group(1)
                    series_ids.append(episode_id)
                next_page = await page.query_selector("a.next-page")

                if next_page and await next_page.is_visible():
                    page_num += 1
                else:
                    break

            await self._close_browser(context)
            return series_ids


async def _save_cv_pages(cv_pages: list[ElementHandle], path: Path) -> None:
    for i, page in enumerate(cv_pages):
        cv = await page.query_selector("canvas")
        if cv is None:
            continue
        file_path = path / f"{i + 1:03}.png"
        if file_path.exists():
            logger.debug(f"File {file_path} already exists, skipping...")
            continue
        logger.info(f"Saving page {i + 1} to {file_path}")
        width = await cv.get_attribute("width")
        height = await cv.get_attribute("height")
        logger.debug(f"Canvas size: {width}x{height}")
        image_base64: str = await cv.evaluate(
            """(selector_handle) => {
                return selector_handle.toDataURL("image/png");
                // return cnv.toDataURL('image/jpeg').substring(22);
            }""",
            cv,
        )
        path.mkdir(parents=True, exist_ok=True)
        with open(path / f"{i + 1:03}.png", "wb") as f:
            img_bin = b64decode(image_base64.split(",")[1])
            f.write(img_bin)


async def _get_publish_date(page: Page) -> datetime | None:
    publish_date_ele = await page.wait_for_selector(".publish-date")
    if publish_date_ele is None:
        logger.error("Failed to find publish date element")
        return None
    date_str = await publish_date_ele.inner_text()
    return datetime.strptime(date_str, "%Y年%m月%d日")


async def _get_page_total(page: Page) -> int:
    page_total_ele = await page.wait_for_selector("#sliderTooltip .-cv-f-page-total")
    if page_total_ele is None:
        logger.error("Failed to find page total element")
        return 0
    return int(await page_total_ele.inner_text())


async def _get_series_title(page: Page) -> str:
    title_loc = page.locator(".series-h-title span")
    error_loc = page.locator(".error-title")
    await expect(title_loc.or_(error_loc).first).to_be_visible()
    if await error_loc.is_visible():
        logger.error("Rate limit reached")
        return ""

    series_title = await page.query_selector(".series-h-title span")
    if series_title is None:
        logger.error("Failed to find series title element")
        return ""
    return await series_title.inner_text()


async def _get_article_title(page: Page) -> str:
    article_title = await page.wait_for_selector(".article-title")
    if article_title is None:
        logger.error("Failed to find article title element")
        return ""
    return await article_title.inner_text()

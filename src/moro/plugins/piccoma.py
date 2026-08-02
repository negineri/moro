"""Piccoma plugin."""

import re
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from playwright.async_api import BrowserContext, Page
from pydantic import BaseModel

from moro.modules.common.domain import AuthError, PWScriptBase

_logger = getLogger(__name__)


class Episode(BaseModel):
    """episode information for Piccoma."""

    title: str
    episode_id: str
    readable: bool


class PWScript(PWScriptBase):
    """
    Base class for Playwright scripts.

    All Playwright scripts should inherit from this class.
    """

    name = "piccoma"

    @classmethod
    def validate(cls, url: str) -> bool:
        """Validate if the given URL is a valid Piccoma URL."""
        return "piccoma.com" in url

    async def script(self, context: BrowserContext, data: dict[str, Any]) -> str:
        """
        The main script logic should be implemented in this method.

        Args:
            context: The Playwright browser context.
            data: A dictionary containing input data for the script.

        Returns:
            A string result from the script execution.
        """
        result = ""
        product_id = re.search(r"product/(\d+)", data["url"])
        if not product_id:
            raise ValueError("Invalid Piccoma URL: Product ID not found.")
        page = await context.new_page()
        await page.goto(f"https://piccoma.com/web/product/{product_id.group(1)}/episodes?etype=E")
        await page.wait_for_selector("css=div.PCM-productSaleList_episode")
        if data.get("login", False) and await page.locator("css=.PCM-headerLogin").count() > 0:
            raise AuthError("Login failed. Please check your credentials.")
        product_title = await page.locator("css=span.PCM-headTitle_name").inner_text()
        episodes = await self._get_episodes(page)
        for episode_number, episode in enumerate(episodes, start=1):
            if episode.readable:
                output_dir = (
                    Path(data["output_dir"])
                    / "piccoma"
                    / f"{product_id.group(1)}_{product_title}"
                    / f"{episode_number:03}_{episode.episode_id}_{episode.title}"
                )
                if output_dir.exists() and any(output_dir.iterdir()):
                    _logger.info(f"Skipping episode {episode.episode_id} as it already exists.")
                    result += f"Episode {episode_number}: {episode.title} (skipped)\n"
                    continue
                await self._dump_episode(page, output_dir, product_id.group(1), episode.episode_id)
                result += f"Episode {episode_number}: {episode.title}\n"

        return result

    async def _dump_episode(
        self, page: Page, output_dir: Path, product_id: str, episode_id: str
    ) -> None:
        """
        Dump episode information for a specific episode.

        Args:
            page: The Playwright page object.
            output_dir: The directory to save the episode screenshots.
            product_id: The ID of the product to which the episode belongs.
            episode_id: The ID of the episode to dump.
        """
        await page.set_viewport_size({"width": 500, "height": 1000})
        await page.goto(f"https://piccoma.com/web/viewer/{product_id}/{episode_id}")
        if await page.locator("css=div.jconfirm-buttons").count() > 0:
            await (
                page.locator("css=div.jconfirm-buttons")
                .get_by_role("button", name="キャンセル")
                .click()
            )
        await page.wait_for_timeout(3000)

        page_count = await page.locator("css=div.react-transform-wrapper").count()

        with TemporaryDirectory() as dname:
            Path(dname).mkdir(parents=True, exist_ok=True)
            for i in range(1, page_count + 1):
                file_name = f"{i:03}.png"
                container = page.locator("css=div.PCM-viewer2_pageWrapper.current")
                container_class = await container.locator(
                    "css=div.PCM-viewer2_canvasWrapper"
                ).get_attribute("class")
                if container_class and "loading" in container_class:
                    _logger.warning(f"Page {i}: Canvas is still loading.")
                    raise ValueError(f"Page {i}: Canvas is still loading.")

                canvas = container.locator("css=canvas")
                height = await canvas.get_attribute("height")
                width = await canvas.get_attribute("width")
                if height is None or width is None:
                    _logger.warning(f"Page {i}: Canvas dimensions not found.")
                    raise ValueError(f"Page {i}: Canvas dimensions not found.")
                await page.set_viewport_size({"width": int(width), "height": int(height)})
                await page.wait_for_timeout(100)  # Wait for the canvas to render
                # screenshot
                await canvas.screenshot(path=Path(dname) / file_name)
                # left arrow key click
                await page.keyboard.press("ArrowLeft")
                await page.wait_for_timeout(200)
            # copy screenshots to output_dir
            for file in Path(dname).iterdir():
                if file.is_file() and file.suffix == ".png":
                    dest_file = output_dir / file.name
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    file.rename(dest_file)
        _logger.info(f"Dumped {page_count} pages to {output_dir}")

    async def _get_episodes(self, page: Page) -> list[Episode]:
        """
        Extract episode information from the given page.

        Args:
            page: The Playwright page object.

        Returns:
            A list of Episode objects containing episode information.
        """
        episodes = []
        for episode_element in await page.locator("css=li.unrDOSPmj0tjYEm").all():
            title = episode_element.locator("css=h2")
            url = episode_element.locator("css=a")
            status = episode_element.locator(
                "css=div.PCM-epList_status>div, div.PCM-epList_status>p"
            ).last
            status_type = await status.get_attribute("class")
            readable = status_type in ["PCM-epList_status_free", "PCM-epList_status_waitfreeRead"]

            if title and url:
                title_text = await title.inner_text()
                episode_id = await url.get_attribute("data-episode_id")
                if episode_id:
                    episodes.append(
                        Episode(title=title_text, episode_id=episode_id, readable=readable)
                    )
        return episodes

    async def login(self, context: BrowserContext, data: dict[str, Any]) -> None:
        """
        Perform login using the Playwright browser context.

        Args:
            context: The Playwright browser context.
            data: A dictionary containing input data for the login process.
        """
        page = await context.new_page()
        page.set_default_timeout(30000)  # Set a default timeout for page actions
        await page.goto("https://piccoma.com/web/acc/signin")
        await page.wait_for_url("https://piccoma.com/web/")

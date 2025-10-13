"""Use cases for the BigComics module."""

import re
from asyncio import sleep
from logging import getLogger
from urllib.parse import urlparse

from injector import inject
from rich.progress import track

from moro.modules.bigcomics.infrastructure import BigComicsRepository

logger = getLogger(__name__)


@inject
class BigComicsUseCase:
    """Use case for BigComics operations."""

    def __init__(self, repo: BigComicsRepository):
        self._repo = repo

    def validate_url(self, url: str) -> bool:
        """Validate the provided URL."""
        parsed_url = urlparse(url)
        if parsed_url.netloc == "bigcomics.jp":
            logger.info(f"Validating URL: {url} - Valid: True")
            return True
        logger.debug(f"Validating URL: {url} - Valid: False")
        return False

    async def download(self, url: str) -> None:
        """Execute the BigComics use case."""
        logger.info("Executing BigComics use case.")
        parsed_url = urlparse(url)
        match = re.search(r"\/episodes\/([^\/]+)", parsed_url.path)
        if match:
            await self._repo.fetch_episode(match.group(1))
        match = re.search(r"\/series\/([^\/]+)", parsed_url.path)
        if match:
            series_ids = await self._repo.fetch_series(match.group(1))
            for series_id in track(series_ids):
                await self._repo.fetch_episode(series_id)
                await sleep(1)

"""Cross-cutting use cases for ebook commands."""

from dataclasses import dataclass

from injector import inject

from moro.modules.bigcomics.usecases import BigComicsUseCase


@inject
@dataclass
class EbookDownloadUseCase:
    """Use case for downloading ebooks."""

    bigcomics_usecase: BigComicsUseCase

    async def execute(self, url: str) -> None:
        """Execute the ebook download process."""
        if self.bigcomics_usecase.validate_url(url):
            await self.bigcomics_usecase.download(url)

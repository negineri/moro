"""Common infrastructure for the modules."""

from logging import getLogger
from typing import Any

from injector import inject
from playwright.async_api import BrowserContext, Playwright, async_playwright
from sqlalchemy.orm import Session

from moro.modules.common.config import CommonConfig
from moro.modules.common.domain import AuthError, Base, CommonDBEngine, CookieORM, PWScriptBase

_logger = getLogger(__name__)


@inject
class PlaywrightProvider:
    """Playwright provider for the modules."""

    def __init__(self, common_config: CommonConfig, common_db_engine: CommonDBEngine) -> None:
        self.common_config = common_config
        self.common_db_engine = common_db_engine
        Base.metadata.create_all(self.common_db_engine.engine)

    async def _launch_browser(
        self, playwright: Playwright, *, headless: bool = True
    ) -> BrowserContext:
        """Launch a Playwright browser."""
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=self.common_config.playwright_user_data_dir,
            user_agent=self.common_config.user_agent,
            headless=headless,
            timeout=self.common_config.timeout_ms,
        )
        with Session(self.common_db_engine.engine) as session:
            cookies = session.query(CookieORM).all()
            await context.add_cookies([cookie.to_playwright_cookie() for cookie in cookies])  # type: ignore
        return context

    async def _close_browser(self, context: BrowserContext) -> None:
        """Close the Playwright browser and save cookies."""
        with Session(self.common_db_engine.engine) as session:
            for cookie in await context.cookies():
                cookie_orm = (
                    session.query(CookieORM)
                    .filter_by(name=cookie["name"], domain=cookie["domain"], path=cookie["path"])  # pyright: ignore
                    .first()
                )
                if cookie_orm:
                    cookie_orm.from_playwright_cookie(cookie)
                else:
                    new_cookie = CookieORM()
                    new_cookie.from_playwright_cookie(cookie)
                    session.add(new_cookie)
            session.commit()
        await context.close()

    async def execute_script(self, script: PWScriptBase, data: dict[str, Any]) -> str:
        """Execute a Playwright script."""
        output = ""
        for _ in range(self.common_config.retry_count):
            try:
                async with async_playwright() as p:
                    context = await self._launch_browser(
                        p, headless=self.common_config.playwright_headless
                    )
                    try:
                        output = await script.script(context, data)
                    finally:
                        await self._close_browser(context)
            except AuthError:
                _logger.error("Authentication error occurred")
                async with async_playwright() as p:
                    context = await self._launch_browser(p, headless=False)
                    await script.login(context, data)
                    await self._close_browser(context)
            else:
                break
        return output

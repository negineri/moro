"""Domain models and base classes for the application."""

from typing import Any

from playwright.async_api import BrowserContext, Cookie
from sqlalchemy import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

CommonDBEngine = Engine


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


class PWScriptBase:
    """Base class for Playwright scripts."""

    name: str = "BaseScript"

    @classmethod
    def validate(cls, url: str) -> bool:
        """Validate the URL for the script.

        Args:
            url: The URL to validate.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def script(self, context: BrowserContext, data: dict[str, Any]) -> str:
        """Execute the Playwright script.

        Args:
            context: The Playwright browser context.
            data: Additional data for the script.

        Returns:
            str: Result of the script execution.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def login(self, context: BrowserContext, data: dict[str, Any]) -> None:
        """Perform login using the Playwright browser context.

        Args:
            context: The Playwright browser context.
            data: Additional data for the login process.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class AuthError(Exception):
    """Exception raised for authentication errors."""

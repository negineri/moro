"""Fantia authentication service."""

import os
from logging import getLogger
from urllib.parse import urlparse

from injector import inject, singleton
from selenium import webdriver

from moro.config.settings import ConfigRepository
from moro.modules.fantia import FantiaClient, check_login

logger = getLogger(__name__)

DOMAIN = "fantia.jp"
LOGIN_SIGNIN_URL = "https://fantia.jp/sessions/signin"


@inject
@singleton
class FantiaAuthService:
    """Service for handling Fantia authentication."""

    def __init__(self, config: ConfigRepository, client: FantiaClient) -> None:
        self.config = config
        self.client = client

    def ensure_authenticated(self) -> bool:
        """
        Ensure the client is authenticated.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        if check_login(self.client):
            return True

        chrome_userdata_dir = os.path.join(self.config.common.user_data_dir, "chrome_userdata")
        return self._login_with_selenium(chrome_userdata_dir)

    def _login_with_selenium(self, chrome_userdata_dir: str) -> bool:
        """
        Login to Fantia using Selenium.

        Args:
            chrome_userdata_dir: Chrome user data directory path.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        options = self._create_chrome_options(chrome_userdata_dir)

        try:
            with webdriver.Chrome(options=options) as driver:
                driver.get(LOGIN_SIGNIN_URL)

                while True:
                    parsed_url = urlparse(driver.current_url)
                    if parsed_url.path == "/" and parsed_url.netloc == DOMAIN:
                        # Successfully logged in
                        self._update_client_cookies(driver)
                        return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _create_chrome_options(self, userdata_dir: str) -> webdriver.ChromeOptions:
        """
        Create Chrome options for Selenium.

        Args:
            userdata_dir: Chrome user data directory path.

        Returns:
            webdriver.ChromeOptions: Configured Chrome options.
        """
        os.makedirs(userdata_dir, exist_ok=True)
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={userdata_dir}")
        return options

    def _update_client_cookies(self, driver: webdriver.Chrome) -> None:
        """
        Update client cookies from Selenium driver.

        Args:
            driver: Selenium Chrome driver.
        """
        cookies: list[dict[str, str]] = driver.get_cookies()  # pyright: ignore
        self.client.cookies.clear()

        for cookie in cookies:
            if cookie["name"] in ("_session_id", "jp_chatplus_vtoken", "_f_v_k_1"):
                self.client.cookies.set(cookie["name"], cookie["value"], domain=DOMAIN)

"""fantia moduleのテスト."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from moro.modules.fantia import (
    FantiaClient,
    FantiaConfig,
    _extract_post_metadata,
    _fetch_post_data,
    _parse_post_contents,
    _parse_post_thumbnail,
    _validate_post_type,
    check_login,
)


class TestFantiaConfig:
    """FantiaConfig クラスのテスト."""

    def test_init_with_defaults(self) -> None:
        """デフォルト値での初期化テスト."""
        config = FantiaConfig()

        assert config.session_id is None
        assert config.directory == "downloads/fantia"
        assert config.download_thumb is False
        assert config.priorize_webp is False
        assert config.use_server_filenames is False
        assert config.max_retries == 5
        assert config.timeout_connect == 10.0
        assert config.timeout_read == 30.0
        assert config.timeout_write == 10.0
        assert config.timeout_pool == 5.0
        assert config.concurrent_downloads == 3

    def test_config_validation(self) -> None:
        """設定値のバリデーションテスト."""
        # 負の値はバリデーションエラーになる
        with pytest.raises(ValueError):
            FantiaConfig(max_retries=-1)

        with pytest.raises(ValueError):
            FantiaConfig(timeout_connect=-1.0)

        with pytest.raises(ValueError):
            FantiaConfig(concurrent_downloads=0)


class TestFantiaClient:
    """FantiaClient クラスのテスト."""

    def test_http_client_configuration(self) -> None:
        """HTTP クライアントの設定テスト."""
        config = FantiaConfig(max_retries=5)
        client = FantiaClient(config)

        # httpx.Client が適切な設定で作成されることを確認
        assert client.timeout.connect == config.timeout_connect
        assert client.timeout.read == config.timeout_read
        assert client.timeout.write == config.timeout_write
        assert client.timeout.pool == config.timeout_pool


class TestCheckLogin:
    """check_login 関数のテスト."""

    def test_check_login_success(self) -> None:
        """ログイン成功テスト."""
        mock_client = MagicMock()

        # レスポンスが成功を示す
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        result = check_login(mock_client)

        assert result is True
        mock_client.get.assert_called_once_with("https://fantia.jp/api/v1/me")

    def test_check_login_failure(self) -> None:
        """ログイン失敗テスト."""
        mock_client = MagicMock()

        # レスポンスが失敗を示す
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_client.get.return_value = mock_response

        result = check_login(mock_client)

        assert result is False

    def test_check_login_exception(self) -> None:
        """ログインチェック例外テスト."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Network error")

        # 例外が発生することを確認
        with pytest.raises(httpx.RequestError, match="Network error"):
            check_login(mock_client)

        # APIエンドポイントが呼び出されたことを検証
        mock_client.get.assert_called_once_with("https://fantia.jp/api/v1/me")


class TestFetchPostData:
    """_fetch_post_data 関数のテスト."""

    @patch("moro.modules.fantia.check_login")
    @patch("moro.modules.fantia.get_csrf_token")
    def test_fetch_post_data_success(
        self, mock_get_csrf: MagicMock, mock_check_login: MagicMock
    ) -> None:
        """投稿データ取得成功テスト."""
        mock_client = MagicMock()
        mock_check_login.return_value = True
        mock_get_csrf.return_value = "test_csrf_token"

        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.text = '{"post": {"id": 12345, "title": "Test Post"}}'
        mock_client.get.return_value = mock_response

        result = _fetch_post_data(mock_client, "12345")

        assert result == {"id": 12345, "title": "Test Post"}
        mock_check_login.assert_called_once_with(mock_client)
        mock_get_csrf.assert_called_once_with(mock_client, "12345")
        # GETリクエストが正しいURLで呼び出されたことを検証
        mock_client.get.assert_called_once_with(
            "https://fantia.jp/api/v1/posts/12345",
            headers={"X-CSRF-Token": "test_csrf_token", "X-Requested-With": "XMLHttpRequest"},
        )

    @patch("moro.modules.fantia.check_login")
    def test_fetch_post_data_login_failed(self, mock_check_login: MagicMock) -> None:
        """ログイン失敗テスト."""
        mock_client = MagicMock()
        mock_check_login.return_value = False

        with pytest.raises(ValueError, match="Invalid session"):
            _fetch_post_data(mock_client, "12345")

        # ログインチェックが呼び出されたことを検証
        mock_check_login.assert_called_once_with(mock_client)
        # ログイン失敗時はデータ取得が呼び出されないことを検証
        mock_client.get.assert_not_called()


class TestExtractPostMetadata:
    """_extract_post_metadata 関数のテスト."""

    def test_extract_post_metadata_success(self) -> None:
        """メタデータ抽出成功テスト."""
        post_json = {
            "id": 12345,
            "title": "Test Post",
            "fanclub": {"creator_name": "Test Creator", "id": 456},
            "post_contents": [{"id": 1, "category": "text"}],
            "posted_at": "Wed, 01 Jan 2023 00:00:00 GMT",
            "converted_at": "2023-01-01T00:00:00+00:00",
            "comment": "Test comment",
        }

        result = _extract_post_metadata(post_json)

        assert result["id"] == 12345
        assert result["title"] == "Test Post"
        assert result["creator"] == "Test Creator"
        assert result["creator_id"] == 456
        assert result["comment"] == "Test comment"

    def test_extract_post_metadata_no_converted_at(self, fantia_test_data) -> None:
        """converted_atがない場合のテスト."""
        post_json = fantia_test_data.create_post_json_data(
            converted_at=None,
            comment=None,
        )

        result = _extract_post_metadata(post_json)

        assert result["posted_at"] == result["converted_at"]
        assert result["comment"] is None


class TestValidatePostType:
    """_validate_post_type 関数のテスト."""

    def test_validate_post_type_blog_post(self, fantia_test_data) -> None:
        """ブログ投稿のテスト."""
        post_json = fantia_test_data.create_post_json_data(is_blog=True)

        with pytest.raises(NotImplementedError, match="Blog posts are not supported"):
            _validate_post_type(post_json, fantia_test_data.DEFAULT_POST_ID)

    def test_validate_post_type_normal_post(self, fantia_test_data) -> None:
        """通常の投稿のテスト."""
        post_json = fantia_test_data.create_post_json_data(is_blog=False)

        # 例外が発生しないことを確認
        _validate_post_type(post_json, fantia_test_data.DEFAULT_POST_ID)


class TestParsePostThumbnail:
    """_parse_post_thumbnail 関数のテスト."""

    def test_parse_post_thumbnail_success(self, fantia_test_data) -> None:
        """サムネイル解析成功テスト."""
        post_json = fantia_test_data.create_post_json_data()

        result = _parse_post_thumbnail(post_json)

        assert result is not None
        assert result.url == "https://example.com/thumb.jpg"
        assert result.ext == ".jpg"

    def test_parse_post_thumbnail_no_thumb(self, fantia_test_data) -> None:
        """サムネイルがない場合のテスト."""
        post_json = fantia_test_data.create_post_json_data()
        del post_json["thumb"]

        result = _parse_post_thumbnail(post_json)

        assert result is None


class TestParsePostContents:
    """_parse_post_contents 関数のテスト."""

    def test_parse_post_contents_invisible(self, fantia_test_data) -> None:
        """非表示コンテンツのテスト."""
        post_contents = [{"id": 1, "category": "text", "visible_status": "invisible"}]

        gallery, files, text, products = _parse_post_contents(
            post_contents, fantia_test_data.DEFAULT_POST_ID
        )

        assert gallery == []
        assert files == []
        assert text == []
        assert products == []

    def test_parse_post_contents_unsupported_category(self, fantia_test_data) -> None:
        """サポートされていないカテゴリのテスト."""
        post_contents = [{"id": 1, "category": "unsupported", "visible_status": "visible"}]

        with pytest.raises(NotImplementedError, match="not supported yet"):
            _parse_post_contents(post_contents, fantia_test_data.DEFAULT_POST_ID)

    def test_parse_post_contents_empty(self, fantia_test_data) -> None:
        """空のコンテンツのテスト."""
        post_contents = []

        gallery, files, text, products = _parse_post_contents(
            post_contents, fantia_test_data.DEFAULT_POST_ID
        )

        assert gallery == []
        assert files == []
        assert text == []
        assert products == []

    def test_parse_post_contents_valid_categories(self, fantia_test_data) -> None:
        """有効なカテゴリのテスト."""
        post_contents = [
            {
                "id": 1,
                "category": "photo_gallery",
                "visible_status": "visible",
                "title": "Gallery 1",
                "comment": "Gallery comment",
                "post_content_photos": [
                    {"url": {"original": "https://example.com/1.jpg"}},
                    {"url": {"original": "https://example.com/2.jpg"}},
                ],
            },
            {
                "id": 2,
                "category": "file",
                "visible_status": "visible",
                "title": "File 1",
                "comment": "File comment",
                "download_uri": "/files/file.pdf",
                "filename": "file.pdf",
            },
            {
                "id": 3,
                "category": "text",
                "visible_status": "visible",
                "title": "Text 1",
                "comment": "Text comment",
            },
        ]

        gallery, files, text, products = _parse_post_contents(
            post_contents, fantia_test_data.DEFAULT_POST_ID
        )

        assert len(gallery) == 1
        assert len(files) == 1
        assert len(text) == 1
        assert len(products) == 0

        assert gallery[0].id == "1"
        assert gallery[0].title == "Gallery 1"
        assert files[0].id == "2"
        assert files[0].title == "File 1"
        assert text[0].id == "3"
        assert text[0].title == "Text 1"

"""Fantiaモジュール独立ドメインテスト

他モジュールへの依存・参照は一切禁止
moro.modules.fantia.* のみimport許可
"""

import pytest

from moro.modules.fantia.domain import (
    FantiaPostData,
    FantiaURL,
    SessionIdProvider,
)
from tests.factories.fantia_factories import (
    FantiaFileFactory,
    FantiaPhotoGalleryFactory,
    FantiaPostDataFactory,
    FantiaProductFactory,
    FantiaTextFactory,
    FantiaURLFactory,
)


@pytest.mark.unit
class TestFantiaURL:
    """FantiaURL ドメイン値オブジェクトテスト"""

    def test_create_url_with_valid_data(self) -> None:
        """有効データでのURL作成テスト"""
        url = FantiaURLFactory.build(url="https://example.com/image.jpg", ext=".jpg")

        assert url.url == "https://example.com/image.jpg"
        assert url.ext == ".jpg"
        assert isinstance(url, FantiaURL)

    def test_url_allows_empty_url(self) -> None:
        """空URL許可テスト（現在の実装確認）"""
        url = FantiaURL(url="", ext=".jpg")
        assert url.url == ""
        assert url.ext == ".jpg"

    def test_url_allows_empty_ext(self) -> None:
        """空拡張子許可テスト（現在の実装確認）"""
        url = FantiaURL(url="https://example.com/file", ext="")
        assert url.url == "https://example.com/file"
        assert url.ext == ""


@pytest.mark.unit
class TestFantiaFile:
    """FantiaFile ドメインエンティティテスト"""

    def test_create_file_with_required_fields(self) -> None:
        """必須フィールドでのファイル作成テスト"""
        file = FantiaFileFactory.build(
            id="file123",
            title="テストファイル",
            url="https://example.com/test.zip",
            name="test.zip",
        )

        assert file.id == "file123"
        assert file.title == "テストファイル"
        assert file.url == "https://example.com/test.zip"
        assert file.name == "test.zip"

    def test_file_with_optional_comment(self) -> None:
        """コメント付きファイルテスト"""
        file = FantiaFileFactory.build(comment="テストコメント")

        assert file.comment == "テストコメント"

    def test_file_with_none_comment(self) -> None:
        """コメントなしファイルテスト"""
        file = FantiaFileFactory.build(comment=None)

        assert file.comment is None


@pytest.mark.unit
class TestFantiaPhotoGallery:
    """FantiaPhotoGallery ドメインエンティティテスト"""

    def test_create_gallery_with_photos(self) -> None:
        """写真付きギャラリー作成テスト"""
        photos = [
            FantiaURLFactory.build(url="https://example.com/photo1.jpg"),
            FantiaURLFactory.build(url="https://example.com/photo2.jpg"),
        ]
        gallery = FantiaPhotoGalleryFactory.build(
            id="gallery123", title="テストギャラリー", photos=photos
        )

        assert gallery.id == "gallery123"
        assert gallery.title == "テストギャラリー"
        assert len(gallery.photos) == 2
        assert gallery.photos[0].url == "https://example.com/photo1.jpg"

    def test_gallery_empty_photos_list(self) -> None:
        """空写真リストギャラリーテスト"""
        gallery = FantiaPhotoGalleryFactory.build(photos=[])

        assert len(gallery.photos) == 0


@pytest.mark.unit
class TestFantiaPostData:
    """FantiaPostData メインドメインエンティティテスト"""

    def test_create_post_with_all_content_types(self) -> None:
        """全コンテンツタイプ付き投稿作成テスト"""
        post = FantiaPostDataFactory.build(
            id="post123",
            title="テスト投稿",
            creator_name="クリエイター",
        )

        assert post.id == "post123"
        assert post.title == "テスト投稿"
        assert post.creator_name == "クリエイター"
        assert isinstance(post.contents_photo_gallery, list)
        assert isinstance(post.contents_files, list)
        assert isinstance(post.contents_text, list)
        assert isinstance(post.contents_products, list)

    def test_post_timestamps_validation(self) -> None:
        """投稿タイムスタンプバリデーションテスト"""
        post = FantiaPostDataFactory.build(posted_at=1691683200, converted_at=1691683260)

        assert post.posted_at == 1691683200
        assert post.converted_at == 1691683260
        # converted_at should be after posted_at
        assert post.converted_at > post.posted_at

    def test_post_with_thumbnail(self) -> None:
        """サムネイル付き投稿テスト"""
        thumbnail = FantiaURLFactory.build(url="https://example.com/thumb.jpg")
        post = FantiaPostDataFactory.build(thumbnail=thumbnail)

        assert post.thumbnail is not None
        assert post.thumbnail.url == "https://example.com/thumb.jpg"

    def test_post_without_thumbnail(self) -> None:
        """サムネイルなし投稿テスト"""
        post = FantiaPostDataFactory.build(thumbnail=None)

        assert post.thumbnail is None

    def test_post_allows_empty_id(self) -> None:
        """空ID許可テスト（現在の実装確認）"""
        post = FantiaPostData(
            id="",
            title="テスト",
            creator_name="クリエイター",
            creator_id="creator123",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1691683200,
            converted_at=1691683260,
            comment=None,
            thumbnail=None,
        )
        assert post.id == ""

    def test_post_allows_empty_title(self) -> None:
        """空タイトル許可テスト（現在の実装確認）"""
        post = FantiaPostData(
            id="post123",
            title="",
            creator_name="クリエイター",
            creator_id="creator123",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1691683200,
            converted_at=1691683260,
            comment=None,
            thumbnail=None,
        )
        assert post.title == ""


@pytest.mark.unit
class TestFantiaProduct:
    """FantiaProduct ドメインエンティティテスト"""

    def test_create_product_with_required_fields(self) -> None:
        """必須フィールドでのプロダクト作成テスト"""
        product = FantiaProductFactory.build(
            id="prod123",
            title="テストプロダクト",
            name="test_product",
            url="https://example.com/product",
        )

        assert product.id == "prod123"
        assert product.title == "テストプロダクト"
        assert product.name == "test_product"
        assert product.url == "https://example.com/product"


@pytest.mark.unit
class TestFantiaText:
    """FantiaText ドメインエンティティテスト"""

    def test_create_text_content(self) -> None:
        """テキストコンテンツ作成テスト"""
        text = FantiaTextFactory.build(
            id="text123", title="テキストタイトル", comment="テキストコメント"
        )

        assert text.id == "text123"
        assert text.title == "テキストタイトル"
        assert text.comment == "テキストコメント"


@pytest.mark.unit
class TestSessionIdProvider:
    """SessionIdProvider プロトコルテスト"""

    def test_session_id_provider_protocol(self) -> None:
        """SessionIdProviderプロトコル実装テスト"""

        class TestProvider:
            def get_cookies(self) -> dict[str, str]:
                return {"_session_id": "test123", "jp_chatplus_vtoken": "token456"}

        provider: SessionIdProvider = TestProvider()
        cookies = provider.get_cookies()

        assert "_session_id" in cookies
        assert cookies["_session_id"] == "test123"
        assert "jp_chatplus_vtoken" in cookies

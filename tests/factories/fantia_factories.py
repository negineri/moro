"""Fantiaモジュール専用Factory - type hints完全対応"""

from typing import Any

from polyfactory.factories.pydantic_factory import ModelFactory

from moro.modules.fantia.domain import (
    FantiaFile,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaProduct,
    FantiaText,
    FantiaURL,
)


class FantiaURLFactory(ModelFactory[FantiaURL]):
    """FantiaURL用Factory"""

    __model__ = FantiaURL

    @classmethod
    def url(cls) -> str:
        return "https://example.com/test-image.jpg"

    @classmethod
    def ext(cls) -> str:
        return ".jpg"


class FantiaPhotoGalleryFactory(ModelFactory[FantiaPhotoGallery]):
    """FantiaPhotoGallery用Factory"""

    __model__ = FantiaPhotoGallery

    @classmethod
    def id(cls) -> str:
        return "test_gallery_001"

    @classmethod
    def title(cls) -> str:
        return "テストフォトギャラリー"

    @classmethod
    def comment(cls) -> str | None:
        return "テストギャラリーコメント"

    @classmethod
    def photos(cls) -> list[FantiaURL]:
        return [FantiaURLFactory.build() for _ in range(2)]


class FantiaFileFactory(ModelFactory[FantiaFile]):
    """FantiaFile用Factory"""

    __model__ = FantiaFile

    @classmethod
    def id(cls) -> str:
        return "test_file_001"

    @classmethod
    def title(cls) -> str:
        return "テストファイル"

    @classmethod
    def comment(cls) -> str | None:
        return "テストファイルコメント"

    @classmethod
    def url(cls) -> str:
        return "https://example.com/test-file.zip"

    @classmethod
    def name(cls) -> str:
        return "test_file.zip"


class FantiaTextFactory(ModelFactory[FantiaText]):
    """FantiaText用Factory"""

    __model__ = FantiaText

    @classmethod
    def id(cls) -> str:
        return "test_text_001"

    @classmethod
    def title(cls) -> str:
        return "テストテキスト"

    @classmethod
    def comment(cls) -> str | None:
        return "テストテキストコメント"


class FantiaProductFactory(ModelFactory[FantiaProduct]):
    """FantiaProduct用Factory"""

    __model__ = FantiaProduct

    @classmethod
    def id(cls) -> str:
        return "test_product_001"

    @classmethod
    def title(cls) -> str:
        return "テストプロダクト"

    @classmethod
    def comment(cls) -> str | None:
        return "テストプロダクトコメント"

    @classmethod
    def name(cls) -> str:
        return "test_product"

    @classmethod
    def url(cls) -> str:
        return "https://example.com/product"


class FantiaPostDataFactory(ModelFactory[FantiaPostData]):
    """FantiaPostData用Factory"""

    __model__ = FantiaPostData

    @classmethod
    def id(cls) -> str:
        return "test_post_123"

    @classmethod
    def title(cls) -> str:
        return "テスト投稿タイトル"

    @classmethod
    def creator_name(cls) -> str:
        return "テストクリエイター"

    @classmethod
    def creator_id(cls) -> str:
        return "creator_123"

    @classmethod
    def contents(cls) -> list[Any]:
        return []

    @classmethod
    def contents_photo_gallery(cls) -> list[FantiaPhotoGallery]:
        return [FantiaPhotoGalleryFactory.build()]

    @classmethod
    def contents_files(cls) -> list[FantiaFile]:
        return [FantiaFileFactory.build()]

    @classmethod
    def contents_text(cls) -> list[FantiaText]:
        return [FantiaTextFactory.build()]

    @classmethod
    def contents_products(cls) -> list[FantiaProduct]:
        return [FantiaProductFactory.build()]

    @classmethod
    def posted_at(cls) -> int:
        return 1691683200  # 2023-08-10

    @classmethod
    def converted_at(cls) -> int:
        return 1691683260  # 2023-08-10 + 1min

    @classmethod
    def comment(cls) -> str | None:
        return "テスト投稿コメント"

    @classmethod
    def thumbnail(cls) -> FantiaURL | None:
        return FantiaURLFactory.build()

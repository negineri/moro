"""Tests for Fantia CLI functionality."""


from moro.cli.fantia import _estimate_file_count
from moro.modules.fantia.domain import (
    FantiaFile,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaProduct,
    FantiaURL,
)


class TestFantiaCLI:
    """Fantia CLI機能のテストクラス."""

    def test_estimate_file_count_with_photo_gallery(self) -> None:
        """写真ギャラリーありのファイル数推定テスト."""
        photos = [
            FantiaURL(url="https://example.com/photo1.jpg", ext=".jpg"),
            FantiaURL(url="https://example.com/photo2.jpg", ext=".jpg"),
            FantiaURL(url="https://example.com/photo3.jpg", ext=".jpg"),
        ]
        gallery = FantiaPhotoGallery(
            id="gallery1",
            title="Test Gallery",
            comment="Test comment",
            photos=photos
        )

        post = FantiaPostData(
            id="123",
            title="Test Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[gallery],
            contents_photo_gallery=[gallery],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1609459200,
            converted_at=1609459200,
            comment="Test comment",
            thumbnail=None
        )

        count = _estimate_file_count(post)
        assert count == 3  # 3つの写真

    def test_estimate_file_count_with_files(self) -> None:
        """ファイルコンテンツありのファイル数推定テスト."""
        file1 = FantiaFile(
            id="file1",
            title="File 1",
            url="https://example.com/file1.pdf",
            name="document1.pdf",
            comment="Test file 1"
        )
        file2 = FantiaFile(
            id="file2",
            title="File 2",
            url="https://example.com/file2.zip",
            name="archive.zip",
            comment="Test file 2"
        )

        post = FantiaPostData(
            id="123",
            title="Test Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[file1, file2],
            contents_photo_gallery=[],
            contents_files=[file1, file2],
            contents_text=[],
            contents_products=[],
            posted_at=1609459200,
            converted_at=1609459200,
            comment="Test comment",
            thumbnail=None
        )

        count = _estimate_file_count(post)
        assert count == 2  # 2つのファイル

    def test_estimate_file_count_with_products(self) -> None:
        """商品ありのファイル数推定テスト."""
        product1 = FantiaProduct(
            id="product1",
            title="Product 1",
            name="product1.zip",
            url="https://example.com/product1.zip",
            comment="Test product 1"
        )
        product2 = FantiaProduct(
            id="product2",
            title="Product 2",
            name="product2.pdf",
            url="https://example.com/product2.pdf",
            comment="Test product 2"
        )

        post = FantiaPostData(
            id="123",
            title="Test Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[product1, product2],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[product1, product2],
            posted_at=1609459200,
            converted_at=1609459200,
            comment="Test comment",
            thumbnail=None
        )

        count = _estimate_file_count(post)
        assert count == 2  # 2つの商品

    def test_estimate_file_count_with_thumbnail(self) -> None:
        """サムネイルありのファイル数推定テスト."""
        thumbnail = FantiaURL(
            url="https://example.com/thumb.jpg",
            ext=".jpg"
        )

        post = FantiaPostData(
            id="123",
            title="Test Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1609459200,
            converted_at=1609459200,
            comment="Test comment",
            thumbnail=thumbnail
        )

        count = _estimate_file_count(post)
        assert count == 1  # サムネイルのみ

    def test_estimate_file_count_mixed_content(self) -> None:
        """複数種類のコンテンツ混合のファイル数推定テスト."""
        # 写真ギャラリー (2枚)
        photos = [
            FantiaURL(url="https://example.com/photo1.jpg", ext=".jpg"),
            FantiaURL(url="https://example.com/photo2.jpg", ext=".jpg"),
        ]
        gallery = FantiaPhotoGallery(
            id="gallery1",
            title="Test Gallery",
            comment="Test comment",
            photos=photos
        )

        # ファイル (1つ)
        file_content = FantiaFile(
            id="file1",
            title="Test File",
            url="https://example.com/file.pdf",
            name="document.pdf",
            comment="Test file"
        )

        # 商品 (1つ)
        product = FantiaProduct(
            id="product1",
            title="Product 1",
            name="product.zip",
            url="https://example.com/product.zip",
            comment="Test product"
        )

        # サムネイル (1つ)
        thumbnail = FantiaURL(
            url="https://example.com/thumb.jpg",
            ext=".jpg"
        )

        post = FantiaPostData(
            id="123",
            title="Test Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[gallery, file_content, product],
            contents_photo_gallery=[gallery],
            contents_files=[file_content],
            contents_text=[],
            contents_products=[product],
            posted_at=1609459200,
            converted_at=1609459200,
            comment="Test comment",
            thumbnail=thumbnail
        )

        count = _estimate_file_count(post)
        assert count == 5  # 写真2 + ファイル1 + 商品1 + サムネイル1

    def test_estimate_file_count_empty_post(self) -> None:
        """空のpostのファイル数推定テスト（最小値1を返す）."""
        post = FantiaPostData(
            id="123",
            title="Empty Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1609459200,
            converted_at=1609459200,
            comment="Empty comment",
            thumbnail=None
        )

        count = _estimate_file_count(post)
        assert count == 1  # 最小値1

    def test_estimate_file_count_zero_photos_in_gallery(self) -> None:
        """写真0枚のギャラリーを持つpostのファイル数推定テスト."""
        empty_gallery = FantiaPhotoGallery(
            id="gallery1",
            title="Empty Gallery",
            comment="Empty gallery",
            photos=[]  # 写真0枚
        )

        post = FantiaPostData(
            id="123",
            title="Test Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[empty_gallery],
            contents_photo_gallery=[empty_gallery],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1609459200,
            converted_at=1609459200,
            comment="Test comment",
            thumbnail=None
        )

        count = _estimate_file_count(post)
        assert count == 1  # 最小値1（写真0枚なので）

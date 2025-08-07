"""Fantia Repository 具体実装のテスト."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from moro.modules.fantia import FantiaClient
from moro.modules.fantia.config import FantiaConfig
from moro.modules.fantia.domain import FantiaFanclub, FantiaPostData
from moro.modules.fantia.infrastructure import (
    FantiaFanclubRepositoryImpl,
    FantiaPostRepositoryImpl,
)


@pytest.fixture
def mock_fantia_client() -> MagicMock:
    """FantiaClient のモックオブジェクト."""
    return MagicMock(spec=FantiaClient)


@pytest.fixture
def mock_fantia_config() -> FantiaConfig:
    """FantiaConfig のインスタンス."""
    return FantiaConfig()


@pytest.fixture
def sample_post_data() -> FantiaPostData:
    """テスト用のサンプル投稿データ."""
    return FantiaPostData(
        id="test_post",
        title="Test Post",
        creator_name="Test Creator",
        creator_id="creator_123",
        contents=[],
        contents_photo_gallery=[],
        contents_files=[],
        contents_text=[],
        contents_products=[],
        posted_at=1672531200,
        converted_at=1672531200,
        comment=None,
        thumbnail=None,
    )


class TestFantiaPostRepository:
    """FantiaPostRepositoryImpl のテスト."""

    def test_instantiation_and_basic_methods(
        self, mock_fantia_client: MagicMock, mock_fantia_config: FantiaConfig
    ) -> None:
        """Repository のインスタンス化と基本メソッドの存在確認."""
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        assert repo is not None
        assert hasattr(repo, "get")
        assert hasattr(repo, "get_many")

    def test_edge_cases(
        self, mock_fantia_client: MagicMock, mock_fantia_config: FantiaConfig
    ) -> None:
        """エッジケースのテスト."""
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        # 空のIDでは None が返される
        assert repo.get("") is None

        # 空のリストでは空のリストが返される
        assert repo.get_many([]) == []

    def test_exception_handling(
        self, mock_fantia_client: MagicMock, mock_fantia_config: FantiaConfig
    ) -> None:
        """例外発生時のエラーハンドリングテスト."""
        # Mock で例外を発生させる
        mock_fantia_client.get.side_effect = Exception("Test error")
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        result = repo.get("test_post_id")
        assert result is None

    @patch("moro.modules.fantia.parse_post")
    def test_get_many_with_mixed_results(
        self,
        mock_parse_post: MagicMock,
        mock_fantia_client: MagicMock,
        mock_fantia_config: FantiaConfig,
        sample_post_data: FantiaPostData,
    ) -> None:
        """一部成功・一部失敗の複数取得テスト."""
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        def side_effect(client: FantiaClient, post_id: str) -> FantiaPostData:
            if post_id == "valid_post":
                return sample_post_data
            raise Exception("Post not found")

        mock_parse_post.side_effect = side_effect
        result = repo.get_many(["valid_post", "invalid_post"])

        assert len(result) == 1
        assert result[0].id == sample_post_data.id

    @patch("moro.modules.fantia.parse_post")
    def test_network_error_handling(
        self,
        mock_parse_post: MagicMock,
        mock_fantia_client: MagicMock,
        mock_fantia_config: FantiaConfig,
    ) -> None:
        """ネットワークエラーの適切な処理テスト."""
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)
        mock_parse_post.side_effect = httpx.RequestError("Network error")

        result = repo.get("post_123")
        assert result is None

    @patch("moro.modules.fantia.parse_post")
    def test_backward_compatibility(
        self,
        mock_parse_post: MagicMock,
        mock_fantia_client: MagicMock,
        mock_fantia_config: FantiaConfig,
        sample_post_data: FantiaPostData,
    ) -> None:
        """既存の parse_post() との互換性テスト."""
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)
        mock_parse_post.return_value = sample_post_data

        result = repo.get("test_post_id")

        assert result == sample_post_data
        assert result.id == sample_post_data.id


class TestFantiaFanclubRepository:
    """FantiaFanclubRepositoryImpl のテスト."""

    def test_instantiation_and_basic_methods(self, mock_fantia_client: MagicMock) -> None:
        """Repository のインスタンス化と基本メソッドの存在確認."""
        repo = FantiaFanclubRepositoryImpl(mock_fantia_client)

        assert repo is not None
        assert hasattr(repo, "get")

    def test_edge_cases(self, mock_fantia_client: MagicMock) -> None:
        """エッジケースのテスト."""
        repo = FantiaFanclubRepositoryImpl(mock_fantia_client)

        # 空のIDでは None が返される
        assert repo.get("") is None

    @patch("moro.modules.fantia.infrastructure.get_posts_by_user")
    def test_get_returns_creator_for_valid_id(
        self, mock_get_posts: MagicMock, mock_fantia_client: MagicMock
    ) -> None:
        """有効なクリエイターIDで FantiaFanclub が返されるテスト."""
        repo = FantiaFanclubRepositoryImpl(mock_fantia_client)
        mock_get_posts.return_value = ["post1", "post2", "post3"]

        result = repo.get("valid_creator_id")

        assert result is not None
        assert isinstance(result, FantiaFanclub)
        assert result.id == "valid_creator_id"
        assert result.posts == ["post1", "post2", "post3"]

    @patch("moro.modules.fantia.infrastructure.get_posts_by_user")
    def test_get_returns_none_for_invalid_id(
        self, mock_get_posts: MagicMock, mock_fantia_client: MagicMock
    ) -> None:
        """存在しないクリエイターIDで None が返されるテスト."""
        repo = FantiaFanclubRepositoryImpl(mock_fantia_client)
        mock_get_posts.side_effect = Exception("Creator not found")

        result = repo.get("nonexistent_creator_id")
        assert result is None

    @patch("moro.modules.fantia.infrastructure.get_posts_by_user")
    def test_authentication_error_handling(
        self, mock_get_posts: MagicMock, mock_fantia_client: MagicMock
    ) -> None:
        """認証エラーの適切な処理テスト."""
        repo = FantiaFanclubRepositoryImpl(mock_fantia_client)
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get_posts.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        result = repo.get("creator_123")
        assert result is None

    @patch("moro.modules.fantia.infrastructure.get_posts_by_user")
    def test_backward_compatibility(
        self, mock_get_posts: MagicMock, mock_fantia_client: MagicMock
    ) -> None:
        """既存の get_posts_by_user() との互換性テスト."""
        repo = FantiaFanclubRepositoryImpl(mock_fantia_client)
        expected_posts = ["post1", "post2", "post3"]
        mock_get_posts.return_value = expected_posts

        creator = repo.get("test_creator_id")

        assert creator is not None
        assert creator.posts == expected_posts


class TestRepositoryIntegration:
    """Repository 間の統合テスト."""

    @patch("moro.modules.fantia.infrastructure.get_posts_by_user")
    @patch("moro.modules.fantia.parse_post")
    def test_repositories_work_together(
        self,
        mock_parse_post: MagicMock,
        mock_get_posts: MagicMock,
        mock_fantia_client: MagicMock,
        mock_fantia_config: FantiaConfig,
        sample_post_data: FantiaPostData,
    ) -> None:
        """Repository が連携して動作するテスト."""
        creator_repo = FantiaFanclubRepositoryImpl(mock_fantia_client)
        post_repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        mock_post_ids = ["post1", "post2"]
        mock_get_posts.return_value = mock_post_ids

        def mock_parse_side_effect(client: FantiaClient, post_id: str) -> FantiaPostData:
            return FantiaPostData(
                id=post_id,
                title=f"Post {post_id}",
                creator_name="Test Creator",
                creator_id="creator_123",
                contents=[],
                contents_photo_gallery=[],
                contents_files=[],
                contents_text=[],
                contents_products=[],
                posted_at=1672531200,
                converted_at=1672531200,
                comment=None,
                thumbnail=None,
            )

        mock_parse_post.side_effect = mock_parse_side_effect

        # CreatorRepository で取得した投稿一覧を PostRepository で取得
        creator = creator_repo.get("test_creator")
        assert creator is not None
        assert creator.posts == mock_post_ids

        posts = post_repo.get_many(creator.posts)
        assert len(posts) == 2
        assert all(isinstance(post, FantiaPostData) for post in posts)
        assert posts[0].id == "post1"
        assert posts[1].id == "post2"

    def test_repositories_share_same_client(
        self, mock_fantia_client: MagicMock, mock_fantia_config: FantiaConfig
    ) -> None:
        """Repository が同じクライアントを共有するテスト."""
        creator_repo = FantiaFanclubRepositoryImpl(mock_fantia_client)
        post_repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        # 同じクライアントインスタンスを使用していることを確認
        assert creator_repo._client is mock_fantia_client
        assert post_repo._client is mock_fantia_client

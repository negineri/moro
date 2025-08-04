"""Fantia Repository 具体実装のテスト."""

from unittest.mock import MagicMock

from moro.modules.fantia import FantiaClient
from moro.modules.fantia.domain import FantiaFanclub, FantiaPostData

# ===== Repository 実装の失敗テスト（Red フェーズ） =====


class TestFantiaPostRepositoryImpl:
    """FantiaPostRepositoryImpl のテスト（Green フェーズ）."""

    def test_repository_implementation_can_be_imported(self) -> None:
        """Repository 実装が正しくインポートできることを確認するテスト."""
        from moro.modules.fantia.infrastructure import FantiaPostRepositoryImpl

        # Repository 実装が存在することを確認
        assert FantiaPostRepositoryImpl is not None

    def test_repository_can_be_instantiated(self) -> None:
        """Repository が正しくインスタンス化できることを確認するテスト."""
        from moro.modules.fantia.infrastructure import FantiaPostRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaPostRepositoryImpl(mock_client)

        assert repo is not None
        assert hasattr(repo, "get")
        assert hasattr(repo, "get_many")

    def test_get_method_returns_none_for_empty_id(self) -> None:
        """空のIDで None が返されることを確認するテスト."""
        from moro.modules.fantia.infrastructure import FantiaPostRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaPostRepositoryImpl(mock_client)

        result = repo.get("")
        assert result is None

    def test_get_many_returns_empty_list_for_empty_input(self) -> None:
        """空のリストで空のリストが返されることを確認するテスト."""
        from moro.modules.fantia.infrastructure import FantiaPostRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaPostRepositoryImpl(mock_client)

        result = repo.get_many([])
        assert result == []


class TestFantiaFanclubRepositoryImpl:
    """FantiaFanclubRepositoryImpl の失敗テスト（Red フェーズ）."""

    def test_repository_implementation_can_be_imported(self) -> None:
        """Repository 実装が正しくインポートできることを確認するテスト."""
        from moro.modules.fantia.infrastructure import FantiaFanclubRepositoryImpl

        # Repository 実装が存在することを確認
        assert FantiaFanclubRepositoryImpl is not None

    def test_repository_can_be_instantiated(self) -> None:
        """Repository が正しくインスタンス化できることを確認するテスト."""
        from moro.modules.fantia.infrastructure import FantiaFanclubRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaFanclubRepositoryImpl(mock_client)

        assert repo is not None
        assert hasattr(repo, "get")

    def test_get_method_returns_none_for_empty_id(self) -> None:
        """空のIDで None が返されることを確認するテスト."""
        from moro.modules.fantia.infrastructure import FantiaFanclubRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaFanclubRepositoryImpl(mock_client)

        result = repo.get("")
        assert result is None


# ===== Repository 動作テスト（Green フェーズ） =====


class TestFantiaPostRepositoryImplBehavior:
    """FantiaPostRepositoryImpl の動作テスト."""

    def test_get_handles_exception_and_returns_none(self) -> None:
        """例外発生時に None が返されることのテスト."""
        from moro.modules.fantia.infrastructure import FantiaPostRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        # Mock で例外を発生させる
        mock_client.get.side_effect = Exception("Test error")

        repo = FantiaPostRepositoryImpl(mock_client)
        result = repo.get("test_post_id")

        assert result is None

    def test_get_many_with_mixed_results(self) -> None:
        """一部成功・一部失敗の複数取得テスト."""
        from unittest.mock import patch

        from moro.modules.fantia.infrastructure import FantiaPostRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaPostRepositoryImpl(mock_client)

        # Mock parse_post to return data for some IDs and raise exceptions for others
        def mock_parse_post(client: FantiaClient, post_id: str) -> FantiaPostData:
            if post_id == "valid_post":
                return FantiaPostData(
                    id=post_id,
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
            raise Exception("Post not found")

        with patch("moro.modules.fantia.parse_post", side_effect=mock_parse_post):
            result = repo.get_many(["valid_post", "invalid_post"])

            assert len(result) == 1
            assert result[0].id == "valid_post"


class TestFantiaFanclubRepositoryImplBehavior:
    """FantiaFanclubRepositoryImpl の動作テスト."""

    def test_get_returns_creator_for_valid_id(self) -> None:
        """有効なクリエイターIDで FantiaFanclub が返されることのテスト."""
        from unittest.mock import patch

        from moro.modules.fantia.infrastructure import FantiaFanclubRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaFanclubRepositoryImpl(mock_client)

        # Mock get_posts_by_user to return valid posts
        def mock_get_posts_by_user(client: FantiaClient, creator_id: str) -> list[str]:
            return ["post1", "post2", "post3"]

        with patch("moro.modules.fantia.get_posts_by_user", side_effect=mock_get_posts_by_user):
            result = repo.get("valid_creator_id")
            assert result is not None
            assert isinstance(result, FantiaFanclub)
            assert result.id == "valid_creator_id"
            assert result.posts == ["post1", "post2", "post3"]

    def test_get_returns_none_for_invalid_id(self) -> None:
        """存在しないクリエイターIDで None が返されることのテスト."""
        from unittest.mock import patch

        from moro.modules.fantia.infrastructure import FantiaFanclubRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaFanclubRepositoryImpl(mock_client)

        # Mock get_posts_by_user to raise an exception for invalid ID
        def mock_get_posts_by_user(client: FantiaClient, creator_id: str) -> list[str]:
            raise Exception("Creator not found")

        with patch("moro.modules.fantia.get_posts_by_user", side_effect=mock_get_posts_by_user):
            result = repo.get("nonexistent_creator_id")
            assert result is None

    def test_get_includes_posts_list(self) -> None:
        """クリエイター取得時に投稿一覧が含まれることのテスト."""
        from unittest.mock import patch

        from moro.modules.fantia.infrastructure import FantiaFanclubRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaFanclubRepositoryImpl(mock_client)

        # Mock get_posts_by_user to return posts
        mock_posts = ["post1", "post2", "post3"]

        def mock_get_posts_by_user(client: FantiaClient, creator_id: str) -> list[str]:
            return mock_posts

        with patch("moro.modules.fantia.get_posts_by_user", side_effect=mock_get_posts_by_user):
            result = repo.get("creator_with_posts")
            assert result is not None
            assert isinstance(result.posts, list)
            assert len(result.posts) > 0
            assert result.posts == mock_posts


# ===== Integration テスト（失敗ケース） =====


class TestRepositoryIntegration:
    """Repository 間の統合テスト."""

    def test_repositories_can_be_used_together(self) -> None:
        """Repository が連携して動作することのテスト."""
        from unittest.mock import patch

        from moro.modules.fantia.infrastructure import (
            FantiaFanclubRepositoryImpl,
            FantiaPostRepositoryImpl,
        )

        mock_client = MagicMock(spec=FantiaClient)
        creator_repo = FantiaFanclubRepositoryImpl(mock_client)
        post_repo = FantiaPostRepositoryImpl(mock_client)

        # Mock get_posts_by_user and parse_post
        mock_post_ids = ["post1", "post2"]

        def mock_get_posts_by_user(client: FantiaClient, creator_id: str) -> list[str]:
            return mock_post_ids

        def mock_parse_post(client: FantiaClient, post_id: str) -> FantiaPostData:
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

        with (
            patch("moro.modules.fantia.get_posts_by_user", side_effect=mock_get_posts_by_user),
            patch("moro.modules.fantia.parse_post", side_effect=mock_parse_post),
        ):
            # CreatorRepository で取得した投稿一覧を PostRepository で取得
            creator = creator_repo.get("test_creator")
            assert creator is not None
            assert creator.posts == mock_post_ids

            posts = post_repo.get_many(creator.posts)
            assert len(posts) == 2
            assert all(isinstance(post, FantiaPostData) for post in posts)
            assert posts[0].id == "post1"
            assert posts[1].id == "post2"

    def test_repositories_share_same_client(self) -> None:
        """Repository が同じクライアントを共有することのテスト."""
        from moro.modules.fantia.infrastructure import (
            FantiaFanclubRepositoryImpl,
            FantiaPostRepositoryImpl,
        )

        mock_client = MagicMock(spec=FantiaClient)
        creator_repo = FantiaFanclubRepositoryImpl(mock_client)
        post_repo = FantiaPostRepositoryImpl(mock_client)

        # 同じクライアントインスタンスを使用していることを確認
        assert creator_repo._client is mock_client
        assert post_repo._client is mock_client


# ===== 既存実装との互換性テスト（失敗ケース） =====


class TestBackwardCompatibility:
    """既存実装との互換性テスト."""

    def test_post_repository_compatible_with_parse_post(self) -> None:
        """PostRepository が既存の parse_post() と互換性があることのテスト."""
        from unittest.mock import patch

        from moro.modules.fantia.infrastructure import FantiaPostRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaPostRepositoryImpl(mock_client)
        post_id = "test_post_id"

        # 期待されるデータ
        expected_data = FantiaPostData(
            id=post_id,
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

        # parse_post をモック化
        with patch("moro.modules.fantia.parse_post", return_value=expected_data):
            # Repository実装の結果
            repo_result = repo.get(post_id)

            # 同じ結果が得られることを確認
            assert repo_result == expected_data
            assert repo_result.id == post_id

    def test_creator_repository_compatible_with_get_posts_by_user(self) -> None:
        """CreatorRepository が既存の get_posts_by_user() と互換性があることのテスト."""
        from unittest.mock import patch

        from moro.modules.fantia.infrastructure import FantiaFanclubRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaFanclubRepositoryImpl(mock_client)
        creator_id = "test_creator_id"
        expected_posts = ["post1", "post2", "post3"]

        # get_posts_by_user をモック化
        with patch("moro.modules.fantia.get_posts_by_user", return_value=expected_posts):
            # Repository実装の結果
            creator = repo.get(creator_id)
            assert creator is not None
            repo_posts = creator.posts

            # 同じ投稿一覧が得られることを確認
            assert repo_posts == expected_posts


# ===== エラーハンドリングテスト（失敗ケース） =====


class TestRepositoryErrorHandling:
    """Repository のエラーハンドリングテスト."""

    def test_post_repository_handles_network_errors(self) -> None:
        """PostRepository がネットワークエラーを適切に処理することのテスト."""
        from unittest.mock import patch

        import httpx

        from moro.modules.fantia.infrastructure import FantiaPostRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaPostRepositoryImpl(mock_client)

        # parse_post がネットワークエラーを発生させるモック
        def mock_parse_post_error(client: FantiaClient, post_id: str) -> FantiaPostData:
            raise httpx.RequestError("Network error")

        with patch("moro.modules.fantia.parse_post", side_effect=mock_parse_post_error):
            # Repository は例外をキャッチして None を返す
            result = repo.get("post_123")
            assert result is None

    def test_creator_repository_handles_authentication_errors(self) -> None:
        """CreatorRepository が認証エラーを適切に処理することのテスト."""
        from unittest.mock import patch

        import httpx

        from moro.modules.fantia.infrastructure import FantiaFanclubRepositoryImpl

        mock_client = MagicMock(spec=FantiaClient)
        repo = FantiaFanclubRepositoryImpl(mock_client)

        # get_posts_by_user が認証エラーを発生させるモック
        mock_response = MagicMock()
        mock_response.status_code = 401

        def mock_get_posts_by_user_error(client: FantiaClient, creator_id: str) -> list[str]:
            raise httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)

        with patch(
            "moro.modules.fantia.get_posts_by_user", side_effect=mock_get_posts_by_user_error
        ):
            # Repository は例外をキャッチして None を返す
            result = repo.get("creator_123")
            assert result is None

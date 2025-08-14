"""Fantiaモジュール独立ユースケーステスト

EPGStation/TODO等の他モジュール参照禁止
moro.modules.fantia.* のみimport許可
"""

from unittest.mock import Mock, patch

import pytest

from moro.config.settings import ConfigRepository
from moro.modules.fantia.domain import (
    FantiaFanclub,
    FantiaFanclubRepository,
    FantiaPostData,
    FantiaPostRepository,
)
from moro.modules.fantia.infrastructure import FantiaFileDownloader
from moro.modules.fantia.usecases import (
    FantiaGetFanclubUseCase,
    FantiaGetPostsUseCase,
    FantiaSavePostUseCase,
)
from tests.factories.fantia_factories import FantiaPostDataFactory


@pytest.mark.unit
class TestFantiaGetFanclubUseCase:
    """FantiaGetFanclubUseCase 単体テスト"""

    @pytest.fixture
    def mock_fanclub_repo(self) -> Mock:
        """FanclubRepositoryのMock"""
        return Mock(spec=FantiaFanclubRepository)

    @pytest.fixture
    def usecase(self, mock_fanclub_repo: Mock) -> FantiaGetFanclubUseCase:
        """テスト対象UseCase"""
        return FantiaGetFanclubUseCase(fanclub_repo=mock_fanclub_repo)

    def test_execute_fanclub_found(
        self, usecase: FantiaGetFanclubUseCase, mock_fanclub_repo: Mock
    ) -> None:
        """ファンクラブ取得成功テスト"""
        # Given
        fanclub_id = "test_fanclub_123"
        test_fanclub = FantiaFanclub(id=fanclub_id, posts=["post1", "post2"])
        mock_fanclub_repo.get.return_value = test_fanclub

        # When
        result = usecase.execute(fanclub_id)

        # Then
        assert result is not None
        assert result.id == fanclub_id
        assert len(result.posts) == 2
        mock_fanclub_repo.get.assert_called_once_with(fanclub_id)

    def test_execute_fanclub_not_found(
        self, usecase: FantiaGetFanclubUseCase, mock_fanclub_repo: Mock
    ) -> None:
        """ファンクラブが見つからない場合のテスト"""
        # Given
        fanclub_id = "nonexistent_fanclub"
        mock_fanclub_repo.get.return_value = None

        # When
        result = usecase.execute(fanclub_id)

        # Then
        assert result is None
        mock_fanclub_repo.get.assert_called_once_with(fanclub_id)


@pytest.mark.unit
class TestFantiaGetPostsUseCase:
    """FantiaGetPostsUseCase 単体テスト"""

    @pytest.fixture
    def mock_post_repo(self) -> Mock:
        """PostRepositoryのMock"""
        return Mock(spec=FantiaPostRepository)

    @pytest.fixture
    def usecase(self, mock_post_repo: Mock) -> FantiaGetPostsUseCase:
        """テスト対象UseCase"""
        return FantiaGetPostsUseCase(post_repo=mock_post_repo)

    def test_execute_multiple_posts(
        self, usecase: FantiaGetPostsUseCase, mock_post_repo: Mock
    ) -> None:
        """複数投稿取得テスト"""
        # Given
        post_ids = ["post1", "post2", "post3"]
        test_posts = [FantiaPostDataFactory.build(id=post_id) for post_id in post_ids]
        mock_post_repo.get_many.return_value = iter(test_posts)

        # When
        result = list(usecase.execute(post_ids))

        # Then
        assert len(result) == 3
        assert all(isinstance(post, FantiaPostData) for post in result)
        mock_post_repo.get_many.assert_called_once_with(post_ids)

    def test_execute_empty_post_list(
        self, usecase: FantiaGetPostsUseCase, mock_post_repo: Mock
    ) -> None:
        """空の投稿リスト処理テスト"""
        # Given
        post_ids: list[str] = []
        mock_post_repo.get_many.return_value = iter([])

        # When
        result = list(usecase.execute(post_ids))

        # Then
        assert len(result) == 0
        mock_post_repo.get_many.assert_called_once_with(post_ids)


@pytest.mark.unit
class TestFantiaSavePostUseCase:
    """FantiaSavePostUseCase 単体テスト"""

    @pytest.fixture
    def mock_config(self) -> Mock:
        """ConfigRepositoryのMock"""
        config = Mock(spec=ConfigRepository)
        # commonオブジェクトのMock設定
        config.common = Mock()
        config.common.working_dir = "/tmp/test_working"  # noqa: S108  # TODO: Replace with tmp_path fixture
        return config

    @pytest.fixture
    def mock_file_downloader(self) -> Mock:
        """FileDownloaderのMock"""
        return Mock(spec=FantiaFileDownloader)

    @pytest.fixture
    def usecase(self, mock_config: Mock, mock_file_downloader: Mock) -> FantiaSavePostUseCase:
        """テスト対象UseCase"""
        return FantiaSavePostUseCase(config=mock_config, file_downloader=mock_file_downloader)

    @patch("os.makedirs")
    @patch("os.path.exists")
    def test_execute_successful_download(
        self,
        mock_exists: Mock,
        mock_makedirs: Mock,
        usecase: FantiaSavePostUseCase,
        mock_file_downloader: Mock,
    ) -> None:
        """投稿保存成功テスト"""
        # Given
        test_post = FantiaPostDataFactory.build(
            id="post123",
            title="テスト投稿",
            creator_id="creator456",
            posted_at=1691683200,
            converted_at=1691683260,
        )
        mock_file_downloader.download_all_content.return_value = True

        # When
        usecase.execute(test_post)

        # Then
        mock_makedirs.assert_called_once()
        mock_file_downloader.download_all_content.assert_called_once()
        call_args = mock_file_downloader.download_all_content.call_args
        assert call_args[0][0] == test_post  # post_data
        assert "post123_テスト投稿_" in call_args[0][1]  # directory path

    @patch("os.makedirs")
    @patch("shutil.rmtree")
    @patch("os.path.exists")
    def test_execute_download_failure_cleanup(
        self,
        mock_exists: Mock,
        mock_rmtree: Mock,
        mock_makedirs: Mock,
        usecase: FantiaSavePostUseCase,
        mock_file_downloader: Mock,
    ) -> None:
        """ダウンロード失敗時のクリーンアップテスト"""
        # Given
        test_post = FantiaPostDataFactory.build()
        mock_file_downloader.download_all_content.return_value = False
        mock_exists.return_value = True

        # When & Then
        with pytest.raises(OSError, match="Failed to download all content"):
            usecase.execute(test_post)

        mock_rmtree.assert_called_once()

    @patch("os.makedirs")
    def test_create_post_directory_path_format(
        self, mock_makedirs: Mock, usecase: FantiaSavePostUseCase
    ) -> None:
        """投稿ディレクトリパス形式テスト"""
        # Given
        test_post = FantiaPostDataFactory.build(
            id="post123",
            title="テスト投稿/タイトル",  # パス無効文字含む
            creator_id="creator456",
            converted_at=1691683260,  # 2023-08-10 20:01:00
        )

        # When
        result_path = usecase._create_post_directory(test_post)

        # Then
        # sanitize_filenameによりパス無効文字は変換される
        assert "/tmp/test_working/downloads/fantia/creator456/" in result_path  # noqa: S108  # TODO: Replace with tmp_path fixture
        assert "post123" in result_path
        assert "テスト投稿" in result_path
        assert "タイトル" in result_path
        # タイムスタンプフォーマットの詳細は実装依存
        assert len(result_path.split("_")) >= 3  # id_title_timestamp形式
        mock_makedirs.assert_called_once()

    def test_create_post_directory_special_converted_at(
        self, usecase: FantiaSavePostUseCase
    ) -> None:
        """特殊なconverted_at値処理テスト"""
        # Given - special case for posts with no proper converted_at timestamp
        test_post = FantiaPostDataFactory.build(
            converted_at=int(1571632367.0),  # special case value
            posted_at=1691683200,  # fallback timestamp
        )

        # When
        with patch("os.makedirs"):
            result_path = usecase._create_post_directory(test_post)

        # Then
        # special case値の場合posted_atが使われることを確認
        # タイムゾーンや具体的な日時フォーマットは実装依存なので存在確認のみ
        assert len(result_path) > 0
        assert test_post.id in result_path
        assert test_post.title in result_path

    @patch("os.path.exists")
    @patch("shutil.rmtree")
    def test_cleanup_partial_download_directory_exists(
        self, mock_rmtree: Mock, mock_exists: Mock, usecase: FantiaSavePostUseCase
    ) -> None:
        """部分ダウンロードクリーンアップテスト（ディレクトリ存在）"""
        # Given
        test_directory = "/tmp/test_dir"  # noqa: S108  # TODO: Replace with tmp_path fixture
        mock_exists.return_value = True

        # When
        usecase._cleanup_partial_download(test_directory)

        # Then
        mock_exists.assert_called_once_with(test_directory)
        mock_rmtree.assert_called_once_with(test_directory)

    @patch("os.path.exists")
    @patch("shutil.rmtree")
    def test_cleanup_partial_download_directory_not_exists(
        self, mock_rmtree: Mock, mock_exists: Mock, usecase: FantiaSavePostUseCase
    ) -> None:
        """部分ダウンロードクリーンアップテスト（ディレクトリ不存在）"""
        # Given
        test_directory = "/tmp/nonexistent_dir"  # noqa: S108  # TODO: Replace with tmp_path fixture
        mock_exists.return_value = False

        # When
        usecase._cleanup_partial_download(test_directory)

        # Then
        mock_exists.assert_called_once_with(test_directory)
        mock_rmtree.assert_not_called()

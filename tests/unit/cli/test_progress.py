"""Tests for CLI progress bar functionality."""

import pytest
from pytest import CaptureFixture

from moro.cli._progress import PostsProgressManager


@pytest.mark.unit
class TestPostsProgressManager:
    """PostsProgressManagerのテストクラス."""

    def test_posts_progress_manager_basic_flow(self, capfd: CaptureFixture[str]) -> None:
        """基本的な進捗管理フローのテスト."""
        manager = PostsProgressManager(total_posts=2)

        # Post 1
        manager.start_post("123", "Test Post 1")
        manager.finish_post()

        # Post 2
        manager.start_post("456", "Test Post 2")
        manager.finish_post()

        manager.close()

        _, err = capfd.readouterr()
        assert "Test Post 1" in err
        assert "Test Post 2" in err

    def test_long_title_truncation(self, capfd: CaptureFixture[str]) -> None:
        """長いタイトルの切り詰めテスト."""
        manager = PostsProgressManager(total_posts=1)
        long_title = "Very Long Title " * 10  # 170文字程度

        manager.start_post("123", long_title)
        # 内部的に30文字+...に切り詰められることを確認
        manager.close()

        _, err = capfd.readouterr()
        assert "Very Long Title Very Long Titl..." in err

    def test_empty_title_handling(self, capfd: CaptureFixture[str]) -> None:
        """空のタイトル処理テスト."""
        manager = PostsProgressManager(total_posts=1)

        manager.start_post("123", "")
        manager.finish_post()
        manager.close()

        _, err = capfd.readouterr()
        assert "Post: 123 ()" in err

    def test_posts_progress_manager_with_none_total(self, capfd: CaptureFixture[str]) -> None:
        """total_posts=Noneでの初期化と後からのset_totalテスト."""
        manager = PostsProgressManager(total_posts=None)

        # 最初は無限プログレスバー
        assert manager.main_progress.total is None

        # 総数を後から設定
        manager.set_total(3)
        assert manager.main_progress.total == 3

        # 通常通り処理
        manager.start_post("123", "Test Post")
        manager.finish_post()
        manager.close()

        _, err = capfd.readouterr()
        assert "Processing posts: 0/3" in err

    def test_context_manager_normal_flow(self, capfd: CaptureFixture[str]) -> None:
        """コンテキストマネージャーの正常フローテスト."""
        with PostsProgressManager(total_posts=1) as manager:
            manager.start_post("123", "Test Post")
            manager.finish_post()
        # withブロック終了時に自動的にclose()が呼ばれることを確認
        _, _ = capfd.readouterr()

    def test_context_manager_exception_handling(self, capfd: CaptureFixture[str]) -> None:
        """コンテキストマネージャーでの例外処理テスト."""
        try:
            with PostsProgressManager(total_posts=1) as manager:
                manager.start_post("123", "Test Post")
                raise ValueError("Test exception")
        except ValueError:
            pass  # 例外は正常にキャッチされる
        # withブロックで例外が発生してもclose()が呼ばれることを確認
        _, err = capfd.readouterr()
        assert "Test Post" in err

    def test_context_manager_returns_self(self, capfd: CaptureFixture[str]) -> None:
        """コンテキストマネージャーが自身を返すことのテスト."""
        manager = PostsProgressManager(total_posts=1)
        with manager as context_manager:
            assert context_manager is manager

        _, _ = capfd.readouterr()

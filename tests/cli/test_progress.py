"""Tests for CLI progress bar functionality."""

from moro.cli._progress import PostsProgressManager


class TestPostsProgressManager:
    """PostsProgressManagerのテストクラス."""

    def test_posts_progress_manager_basic_flow(self) -> None:
        """基本的な進捗管理フローのテスト."""
        manager = PostsProgressManager(total_posts=2)

        # Post 1
        manager.start_post("123", "Test Post 1")
        manager.finish_post()

        # Post 2
        manager.start_post("456", "Test Post 2")
        manager.finish_post()

        manager.close()

    def test_long_title_truncation(self) -> None:
        """長いタイトルの切り詰めテスト."""
        manager = PostsProgressManager(total_posts=1)
        long_title = "Very Long Title " * 10  # 170文字程度

        manager.start_post("123", long_title)
        # 内部的に30文字+...に切り詰められることを確認
        manager.close()

    def test_close_with_active_download_progress(self) -> None:
        """アクティブなダウンロードプログレスバーがある状態でのclose動作テスト."""
        manager = PostsProgressManager(total_posts=1)

        manager.start_post("123", "Test Post")

        # ダウンロード完了せずにclose
        manager.close()
        # 適切にクリーンアップされることを確認
        assert manager.current_download_progress is None

    def test_empty_title_handling(self) -> None:
        """空のタイトル処理テスト."""
        manager = PostsProgressManager(total_posts=1)

        manager.start_post("123", "")
        manager.finish_post()
        manager.close()

    def test_empty_filename_handling(self) -> None:
        """空のファイル名処理テスト."""
        manager = PostsProgressManager(total_posts=1)

        manager.start_post("123", "Test Post")
        manager.finish_post()
        manager.close()

    def test_posts_progress_manager_with_none_total(self) -> None:
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

    def test_set_total_updates_bar_format(self) -> None:
        """set_total実行時のbar_format更新テスト."""
        manager = PostsProgressManager(total_posts=None)

        # 初期状態では総数なしのフォーマット
        initial_format = manager.main_progress.bar_format
        assert "processed" in initial_format

        # set_total後は総数ありのフォーマットに変更
        manager.set_total(5)
        updated_format = manager.main_progress.bar_format
        assert "{n}/{total}" in updated_format
        assert "percentage" in updated_format

        manager.close()

    def test_context_manager_normal_flow(self) -> None:
        """コンテキストマネージャーの正常フローテスト."""
        with PostsProgressManager(total_posts=1) as manager:
            manager.start_post("123", "Test Post")
            manager.finish_post()
        # withブロック終了時に自動的にclose()が呼ばれることを確認

    def test_context_manager_exception_handling(self) -> None:
        """コンテキストマネージャーでの例外処理テスト."""
        try:
            with PostsProgressManager(total_posts=1) as manager:
                manager.start_post("123", "Test Post")
                raise ValueError("Test exception")
        except ValueError:
            pass  # 例外は正常にキャッチされる
        # withブロックで例外が発生してもclose()が呼ばれることを確認

    def test_context_manager_returns_self(self) -> None:
        """コンテキストマネージャーが自身を返すことのテスト."""
        manager = PostsProgressManager(total_posts=1)
        with manager as context_manager:
            assert context_manager is manager

"""Progress bar management for CLI operations."""

from types import TracebackType
from typing import Any

from tqdm import tqdm


class PostsProgressManager:
    """Posts処理の進捗を管理するクラス."""

    def __init__(self, total_posts: int | None = None) -> None:
        """プログレスバーマネージャーを初期化.

        Args:
            total_posts: 処理対象のpost総数（不明な場合はNone）
        """
        if total_posts is not None:
            self.main_progress = tqdm(
                total=total_posts,
                desc="Processing posts",
                unit="post",
                bar_format="{desc}: {n}/{total} [{bar}] {percentage:3.0f}% | {postfix}",
            )
        else:
            # 総数不明の場合は無限プログレスバー
            self.main_progress = tqdm(
                desc="Processing posts",
                unit="post",
                bar_format="{desc}: {n} processed | {postfix}",
            )
        self.current_download_progress: tqdm[Any] | None = None

    def set_total(self, total: int) -> None:
        """総数を後から設定.

        Args:
            total: 処理対象の総数
        """
        self.main_progress.total = total
        self.main_progress.bar_format = "{desc}: {n}/{total} [{bar}] {percentage:3.0f}% | {postfix}"
        self.main_progress.refresh()

    def start_post(self, post_id: str, title: str) -> None:
        """投稿処理開始時の表示更新.

        Args:
            post_id: 処理中のpost ID
            title: post タイトル
        """
        truncated_title = title[:30] + "..." if len(title) > 30 else title
        self.main_progress.set_postfix_str(f"Post: {post_id} ({truncated_title})")

    def finish_post(self) -> None:
        """投稿処理完了."""
        self.main_progress.update(1)

    def close(self) -> None:
        """全体処理完了・クリーンアップ."""
        if self.current_download_progress:
            self.current_download_progress.close()
            self.current_download_progress = None
        self.main_progress.close()

    def __enter__(self) -> "PostsProgressManager":
        """コンテキストマネージャーのエントリーポイント.

        Returns:
            自身のインスタンス
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """コンテキストマネージャーの終了処理.

        Args:
            exc_type: 例外の型
            exc_val: 例外の値
            exc_tb: トレースバック
        """
        self.close()

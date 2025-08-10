"""Progress bar management for CLI operations."""

from types import TracebackType

from tqdm import tqdm


class PostsProgressManager:
    """Class to manage progress for posts processing."""

    def __init__(self, total_posts: int | None = None) -> None:
        """Initialize the progress bar manager.

        Args:
            total_posts: Total number of posts to process (None if unknown)
        """
        if total_posts is not None:
            self.main_progress = tqdm(
                total=total_posts,
                desc="Processing posts",
                unit="post",
                bar_format="{desc}: {n}/{total} [{bar}] {percentage:3.0f}% | {postfix}",
            )
        else:
            # Infinite progress bar if total is unknown
            self.main_progress = tqdm(
                desc="Processing posts",
                unit="post",
                bar_format="{desc}: {n} processed | {postfix}",
            )

    def set_total(self, total: int) -> None:
        """Set the total number of posts later.

        Args:
            total: Total number of posts to process
        """
        self.main_progress.total = total
        self.main_progress.bar_format = "{desc}: {n}/{total} [{bar}] {percentage:3.0f}% | {postfix}"
        self.main_progress.refresh()

    def start_post(self, post_id: str, title: str) -> None:
        """Update display when starting to process a post.

        Args:
            post_id: ID of the post being processed
            title: Title of the post
        """
        truncated_title = title[:30] + "..." if len(title) > 30 else title
        self.main_progress.set_postfix_str(f"Post: {post_id} ({truncated_title})")

    def finish_post(self) -> None:
        """Mark post processing as finished."""
        self.main_progress.update(1)

    def close(self) -> None:
        """Cleanup after all processing is done."""
        self.main_progress.close()

    def __enter__(self) -> "PostsProgressManager":
        """Context manager entry point.

        Returns:
            Instance of self
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit processing.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Traceback
        """
        self.close()

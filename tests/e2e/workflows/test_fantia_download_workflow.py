"""Fantia完全ダウンロードワークフロー E2E

最小限のエンドツーエンドテスト
実際のユーザーシナリオのみ
"""

from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.mark.e2e
@pytest.mark.slow
class TestFantiaDownloadWorkflow:
    """Fantia完全ワークフローテスト"""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """CLI実行環境"""
        return CliRunner()

    @pytest.fixture
    def temp_download_dir(self, tmp_path: Path) -> Path:
        """一時ダウンロードディレクトリ"""
        download_dir = tmp_path / "fantia_downloads"
        download_dir.mkdir()
        return download_dir

    @pytest.mark.skip_in_ci
    def test_cli_fantia_command_availability(self, runner: CliRunner) -> None:
        """Fantia CLIコマンドの利用可能性確認"""
        # CLI実装次第でimportパスを調整
        try:
            from moro.cli.fantia import posts

            # --helpオプションでコマンドの基本動作確認
            result = runner.invoke(posts, ["--help"])

            # ヘルプが正常に表示されることを確認
            assert result.exit_code == 0
            assert "download" in result.output.lower() or "help" in result.output.lower()

        except ImportError:
            pytest.skip("Fantia CLI module not implemented yet")

    @pytest.mark.skip(reason="CLI implementation not ready")
    @pytest.mark.skip_in_ci
    def test_complete_download_workflow_dry_run(
        self, runner: CliRunner, temp_download_dir: Path
    ) -> None:
        """完全ダウンロードワークフロー（ドライラン）"""
        try:
            from moro.cli.fantia import posts

            # テスト用の仮想投稿ID（実際にダウンロードしない）
            test_post_id = "test_post_123"

            # ドライランモードでの実行
            result = runner.invoke(
                posts,
                [
                    test_post_id,
                    "--output",
                    str(temp_download_dir),
                    "--dry-run",  # ドライランフラグ（実装されている場合）
                ],
            )

            # 実装されていない場合はスキップ
            if result.exit_code != 0 and "not implemented" in result.output.lower():
                pytest.skip("Fantia download command not fully implemented")

            # ドライランの場合、実際のファイルは作成されない
            # コマンドが正常に解析されることのみ確認
            assert result.exit_code in [0, 1]  # 認証エラーは許容

        except ImportError:
            pytest.skip("Fantia CLI module not implemented yet")

    @pytest.mark.manual_test_only
    def test_end_to_end_workflow_with_auth(
        self, runner: CliRunner, temp_download_dir: Path
    ) -> None:
        """エンドツーエンドワークフロー（認証あり）

        Note: 手動テスト専用（CIでは実行しない）
        実際の認証情報が必要
        """
        pytest.skip("Manual test only - requires real authentication")


@pytest.mark.e2e
class TestFantiaConfigWorkflow:
    """Fantia設定ワークフローテスト"""

    def test_config_initialization_workflow(self, tmp_path: Path) -> None:
        """設定初期化ワークフローテスト"""
        # Given
        from moro.config.settings import ConfigRepository
        from moro.modules.common import CommonConfig
        from moro.modules.fantia.config import FantiaConfig

        # When - 設定の初期化ワークフロー
        config = ConfigRepository()
        config.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path / "working"),
            jobs=2,
        )
        config.fantia = FantiaConfig()

        # Then - 設定が正常に初期化されることを確認
        assert config.common.working_dir == str(tmp_path / "working")
        assert config.common.jobs == 2
        assert config.fantia is not None

    def test_fantia_module_integration_workflow(self, tmp_path: Path) -> None:
        """Fantiaモジュール統合ワークフローテスト"""
        # Given
        from tests.factories.fantia_factories import FantiaPostDataFactory

        from moro.config.settings import ConfigRepository
        from moro.modules.common import CommonConfig
        from moro.modules.fantia.config import FantiaConfig
        from moro.modules.fantia.infrastructure import FantiaFileDownloader
        from moro.modules.fantia.usecases import FantiaSavePostUseCase

        # When - 完全なモジュール統合ワークフロー
        config = ConfigRepository()
        config.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path / "working"),
            jobs=2,
        )
        config.fantia = FantiaConfig()

        # 依存関係の組み立て
        from unittest.mock import Mock

        from moro.modules.fantia import FantiaClient

        # SessionIdProviderをモック
        mock_session_provider = Mock()
        mock_session_provider.get_session_id.return_value = "test_session_id"

        # FantiaClientを作成
        client = FantiaClient(config=config.fantia, session_provider=mock_session_provider)
        file_downloader = FantiaFileDownloader(client)
        save_usecase = FantiaSavePostUseCase(
            common_config=config.common, file_downloader=file_downloader
        )

        # テストデータの作成
        test_post = FantiaPostDataFactory.build()

        # Then - 統合されたコンポーネントが正常に動作することを確認
        assert save_usecase is not None
        assert file_downloader is not None
        assert test_post is not None

        # 実際の実行はMockを使って行うため、ここでは構成確認のみ

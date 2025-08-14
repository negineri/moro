"""CLI レイヤーのテスト

Todo CLI コマンドのテスト実装。

教育的ポイント:
- Click のテスト方法
- CLI インターフェースのテスト戦略
- 統合テストの実装
- ユーザーインターフェースのテスト
"""

from datetime import datetime
from unittest.mock import Mock, patch

from click.testing import CliRunner

from moro.cli.todo import todo
from moro.modules.todo.usecases import (
    CreateTodoRequest,
    TodoResponse,
    UpdateTodoRequest,
)


class TestTodoCliAdd:
    """todo add コマンドのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.runner = CliRunner()

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_add_command_success(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """Add コマンド成功テスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase

        # レスポンスのモック
        mock_response = TodoResponse(
            id="test-id-123",
            title="テストタスク",
            description="テスト説明",
            priority="high",
            is_completed=False,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 10, 0, 0),
        )
        mock_usecase.execute.return_value = mock_response

        # コマンド実行
        result = self.runner.invoke(
            todo, ["add", "テストタスク", "--description", "テスト説明", "--priority", "high"]
        )

        # 結果検証
        assert result.exit_code == 0
        assert "Todo を作成しました: テストタスク" in result.output
        assert "ID: test-id-123" in result.output
        assert "優先度: high" in result.output
        assert "説明: テスト説明" in result.output

        # ユースケースが正しい引数で呼ばれることを確認
        mock_usecase.execute.assert_called_once()
        call_args = mock_usecase.execute.call_args[0][0]
        assert isinstance(call_args, CreateTodoRequest)
        assert call_args.title == "テストタスク"
        assert call_args.description == "テスト説明"
        assert call_args.priority == "high"

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_add_command_with_defaults(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """デフォルト値での add コマンドテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase

        # レスポンスのモック
        mock_response = TodoResponse(
            id="test-id-456",
            title="最小限タスク",
            description="",
            priority="medium",
            is_completed=False,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 10, 0, 0),
        )
        mock_usecase.execute.return_value = mock_response

        # コマンド実行（最小限の引数）
        result = self.runner.invoke(todo, ["add", "最小限タスク"])

        # 結果検証
        assert result.exit_code == 0
        assert "Todo を作成しました: 最小限タスク" in result.output
        assert "優先度: medium" in result.output  # デフォルト値
        assert "説明:" not in result.output  # 空の説明は表示されない

        # ユースケースが正しい引数で呼ばれることを確認
        call_args = mock_usecase.execute.call_args[0][0]
        assert call_args.title == "最小限タスク"
        assert call_args.description == ""
        assert call_args.priority == "medium"

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_add_command_validation_error(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """バリデーションエラーのテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase

        # ユースケースでバリデーションエラーを発生させる
        mock_usecase.execute.side_effect = ValueError("タイトルは必須です")

        # コマンド実行
        result = self.runner.invoke(todo, ["add", ""])

        # エラー結果の検証
        assert result.exit_code == 1
        assert "エラー: タイトルは必須です" in result.output

    def test_add_command_invalid_priority(self) -> None:
        """不正な優先度のテスト"""
        result = self.runner.invoke(todo, ["add", "テストタスク", "--priority", "invalid"])

        # Click の Choice バリデーションでエラーになる
        assert result.exit_code == 2
        assert "Invalid value for '--priority'" in result.output


class TestTodoCliList:
    """todo list コマンドのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.runner = CliRunner()

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_list_command_success(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """List コマンド成功テスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase

        # レスポンスのモック
        mock_responses = [
            TodoResponse(
                id="todo-1-abcdef12",
                title="高優先度タスク",
                description="重要なタスク",
                priority="high",
                is_completed=False,
                created_at=datetime(2024, 1, 1, 10, 0, 0),
                updated_at=datetime(2024, 1, 1, 10, 0, 0),
            ),
            TodoResponse(
                id="todo-2-ghijkl34",
                title="完了済みタスク",
                description="",
                priority="medium",
                is_completed=True,
                created_at=datetime(2024, 1, 1, 9, 0, 0),
                updated_at=datetime(2024, 1, 1, 11, 0, 0),
            ),
        ]
        mock_usecase.execute.return_value = mock_responses

        # コマンド実行
        result = self.runner.invoke(todo, ["list"])

        # 結果検証
        assert result.exit_code == 0
        assert "Todo 一覧 - 作成日時順" in result.output
        assert "高優先度タスク" in result.output
        assert "完了済みタスク" in result.output
        assert "[todo-1-a]" in result.output  # ID の短縮表示
        assert "🔴" in result.output  # high priority indicator
        assert "重要なタスク" in result.output
        assert "合計: 2件 (完了: 1件, 未完了: 1件)" in result.output

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_list_command_empty(self, mock_config_create: Mock, mock_create_injector: Mock) -> None:
        """空の結果のテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = []

        # コマンド実行
        result = self.runner.invoke(todo, ["list"])

        # 結果検証
        assert result.exit_code == 0
        assert "Todo はありません" in result.output

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_list_command_with_completed_filter(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """--completed フィルターのテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = []

        # コマンド実行
        result = self.runner.invoke(todo, ["list", "--completed"])

        # 結果検証
        assert result.exit_code == 0
        assert "完了済みの Todo はありません" in result.output

        # ユースケースが正しい引数で呼ばれることを確認
        mock_usecase.execute.assert_called_once_with(completed_only=True, sort_by_priority=False)

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_list_command_with_pending_filter(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """--pending フィルターのテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = []

        # コマンド実行
        result = self.runner.invoke(todo, ["list", "--pending"])

        # 結果検証
        assert result.exit_code == 0

        # ユースケースが正しい引数で呼ばれることを確認
        mock_usecase.execute.assert_called_once_with(completed_only=False, sort_by_priority=False)

    def test_list_command_conflicting_filters(self) -> None:
        """競合するフィルターのテスト"""
        result = self.runner.invoke(todo, ["list", "--completed", "--pending"])

        # エラー結果の検証
        assert result.exit_code == 1
        assert "--completed と --pending は同時に指定できません" in result.output

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_list_command_with_priority_sort(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """--sort-by-priority のテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = []

        # コマンド実行
        result = self.runner.invoke(todo, ["list", "--sort-by-priority"])

        # 結果検証
        assert result.exit_code == 0

        # ユースケースが正しい引数で呼ばれることを確認
        mock_usecase.execute.assert_called_once_with(completed_only=None, sort_by_priority=True)


class TestTodoCliUpdate:
    """todo update コマンドのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.runner = CliRunner()

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_update_command_success(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """Update コマンド成功テスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase

        # レスポンスのモック
        mock_response = TodoResponse(
            id="test-id-789",
            title="更新されたタスク",
            description="新しい説明",
            priority="low",
            is_completed=False,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_usecase.execute.return_value = mock_response

        # コマンド実行
        result = self.runner.invoke(
            todo,
            [
                "update",
                "test-id-789",
                "--title",
                "更新されたタスク",
                "--description",
                "新しい説明",
                "--priority",
                "low",
            ],
        )

        # 結果検証
        assert result.exit_code == 0
        assert "Todo を更新しました: 更新されたタスク" in result.output
        assert "優先度: low" in result.output

        # ユースケースが正しい引数で呼ばれることを確認
        call_args = mock_usecase.execute.call_args[0][0]
        assert isinstance(call_args, UpdateTodoRequest)
        assert call_args.todo_id == "test-id-789"
        assert call_args.title == "更新されたタスク"
        assert call_args.description == "新しい説明"
        assert call_args.priority == "low"

    def test_update_command_no_options(self) -> None:
        """オプションが指定されていない場合のエラーテスト"""
        result = self.runner.invoke(todo, ["update", "test-id"])

        # エラー結果の検証
        assert result.exit_code == 1
        assert "更新する項目を指定してください" in result.output

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_update_command_not_found(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """存在しない Todo の更新でエラーテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.side_effect = ValueError("指定された Todo が見つかりません")

        # コマンド実行
        result = self.runner.invoke(
            todo, ["update", "non-existent-id", "--title", "新しいタイトル"]
        )

        # エラー結果の検証
        assert result.exit_code == 1
        assert "エラー: 指定された Todo が見つかりません" in result.output


class TestTodoCliToggle:
    """todo toggle コマンドのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.runner = CliRunner()

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_toggle_command_to_completed(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """完了状態への切り替えテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase

        # 完了状態のレスポンス
        mock_response = TodoResponse(
            id="toggle-id-123",
            title="切り替えタスク",
            description="",
            priority="medium",
            is_completed=True,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_usecase.execute.return_value = mock_response

        # コマンド実行
        result = self.runner.invoke(todo, ["toggle", "toggle-id-123"])

        # 結果検証
        assert result.exit_code == 0
        assert "✅ Todo を完了にしました: 切り替えタスク" in result.output

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_toggle_command_to_incomplete(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """未完了状態への切り替えテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase

        # 未完了状態のレスポンス
        mock_response = TodoResponse(
            id="toggle-id-456",
            title="戻したタスク",
            description="",
            priority="medium",
            is_completed=False,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        mock_usecase.execute.return_value = mock_response

        # コマンド実行
        result = self.runner.invoke(todo, ["toggle", "toggle-id-456"])

        # 結果検証
        assert result.exit_code == 0
        assert "○ Todo を未完了にしました: 戻したタスク" in result.output


class TestTodoCliDelete:
    """todo delete コマンドのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.runner = CliRunner()

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_delete_command_with_confirmation(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """確認ありでの削除テスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = True  # 削除成功

        # コマンド実行（確認に 'y' で応答）
        result = self.runner.invoke(todo, ["delete", "delete-id-123"], input="y\n")

        # 結果検証
        assert result.exit_code == 0
        assert "Todo を削除しました" in result.output
        assert "(ID: delete-i" in result.output  # ID の短縮表示

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_delete_command_with_force(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """--force での削除テスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = True  # 削除成功

        # コマンド実行
        result = self.runner.invoke(todo, ["delete", "delete-id-456", "--force"])

        # 結果検証
        assert result.exit_code == 0
        assert "Todo を削除しました" in result.output
        # 確認プロンプトは表示されない

    def test_delete_command_cancelled(self) -> None:
        """削除のキャンセルテスト"""
        result = self.runner.invoke(todo, ["delete", "cancel-id-789"], input="n\n")

        # 結果検証
        assert result.exit_code == 0
        assert "削除をキャンセルしました" in result.output

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_delete_command_not_found(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """存在しない Todo の削除テスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = False  # 削除失敗（存在しない）

        # コマンド実行
        result = self.runner.invoke(todo, ["delete", "non-existent-id", "--force"])

        # エラー結果の検証
        assert result.exit_code == 1
        assert "指定された Todo が見つかりません" in result.output


class TestTodoCliCleanup:
    """todo cleanup コマンドのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.runner = CliRunner()

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_cleanup_command_success(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """Cleanup コマンド成功テスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.delete_completed.return_value = 3  # 3件削除

        # コマンド実行（確認に 'y' で応答）
        result = self.runner.invoke(todo, ["cleanup"], input="y\n")

        # 結果検証
        assert result.exit_code == 0
        assert "3件の完了済み Todo を削除しました" in result.output

    @patch("moro.cli.todo.create_injector")
    @patch("moro.cli.todo.ConfigRepository.create")
    def test_cleanup_command_no_todos(
        self, mock_config_create: Mock, mock_create_injector: Mock
    ) -> None:
        """削除対象がない場合のテスト"""
        # モックの設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.delete_completed.return_value = 0  # 削除対象なし

        # コマンド実行
        result = self.runner.invoke(todo, ["cleanup", "--force"])

        # 結果検証
        assert result.exit_code == 0
        assert "削除対象の完了済み Todo はありませんでした" in result.output

    def test_cleanup_command_cancelled(self) -> None:
        """Cleanup のキャンセルテスト"""
        result = self.runner.invoke(todo, ["cleanup"], input="n\n")

        # 結果検証
        assert result.exit_code == 0
        assert "削除をキャンセルしました" in result.output


class TestTodoCliHelp:
    """todo ヘルプのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.runner = CliRunner()

    def test_todo_help(self) -> None:
        """Todo --help のテスト"""
        result = self.runner.invoke(todo, ["--help"])

        assert result.exit_code == 0
        assert "Todo 管理コマンド" in result.output
        assert "add" in result.output
        assert "list" in result.output
        assert "update" in result.output
        assert "toggle" in result.output
        assert "delete" in result.output
        assert "cleanup" in result.output

    def test_todo_add_help(self) -> None:
        """Todo add --help のテスト"""
        result = self.runner.invoke(todo, ["add", "--help"])

        assert result.exit_code == 0
        assert "新しい Todo を追加する" in result.output
        assert "--description" in result.output
        assert "--priority" in result.output

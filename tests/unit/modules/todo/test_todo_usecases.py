"""Use Cases のテスト

Todo モジュールのユースケースレイヤーのテスト実装。

教育的ポイント:
- モックオブジェクトの使用方法
- ユースケースの責務とテスト戦略
- エラーハンドリングの検証
- リクエスト・レスポンスパターンのテスト
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from moro.modules.todo.domain import Todo, TodoID
from moro.modules.todo.usecases import (
    CreateTodoRequest,
    CreateTodoUseCase,
    DeleteTodoUseCase,
    ListTodosUseCase,
    TodoResponse,
    ToggleTodoUseCase,
    UpdateTodoRequest,
    UpdateTodoUseCase,
)


class TestTodoResponse:
    """TodoResponse のテスト"""

    def test_from_domain_conversion(self) -> None:
        """ドメインオブジェクトからレスポンスオブジェクトへの変換テスト"""
        todo_id = TodoID.generate()
        now = datetime.now()

        todo = Todo(
            id=todo_id,
            title="テストタスク",
            description="テスト説明",
            priority="high",
            is_completed=True,
            created_at=now,
            updated_at=now,
        )

        response = TodoResponse.from_domain(todo)

        assert response.id == str(todo_id)
        assert response.title == "テストタスク"
        assert response.description == "テスト説明"
        assert response.priority == "high"
        assert response.is_completed is True
        assert response.created_at == now
        assert response.updated_at == now

    def test_from_domain_with_empty_description(self) -> None:
        """空の説明での変換テスト"""
        todo_id = TodoID.generate()
        now = datetime.now()

        todo = Todo(
            id=todo_id,
            title="タイトルのみ",
            description="",
            priority="low",
            is_completed=False,
            created_at=now,
            updated_at=now,
        )

        response = TodoResponse.from_domain(todo)

        assert response.description == ""
        assert response.title == "タイトルのみ"


class TestCreateTodoUseCase:
    """CreateTodoUseCase のテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.mock_repository = Mock()
        self.usecase = CreateTodoUseCase(self.mock_repository)

    def test_create_todo_success(self) -> None:
        """Todo 作成成功テスト"""
        # リクエストの準備
        request = CreateTodoRequest(title="新しいタスク", description="詳細説明", priority="high")

        # モックの設定（保存時は受け取った Todo をそのまま返す）
        def save_todo(todo: Todo) -> Todo:
            return todo

        self.mock_repository.save.side_effect = save_todo

        # ユースケース実行
        response = self.usecase.execute(request)

        # 結果の検証
        assert isinstance(response, TodoResponse)
        assert response.title == "新しいタスク"
        assert response.description == "詳細説明"
        assert response.priority == "high"
        assert response.is_completed is False
        assert response.created_at is not None
        assert response.updated_at is not None

        # Repository の save が呼ばれたことを確認
        self.mock_repository.save.assert_called_once()
        saved_todo = self.mock_repository.save.call_args[0][0]
        assert isinstance(saved_todo, Todo)
        assert saved_todo.title == "新しいタスク"

    def test_create_todo_with_default_values(self) -> None:
        """デフォルト値での Todo 作成テスト"""
        request = CreateTodoRequest(title="最小限タスク")

        def save_todo(todo: Todo) -> Todo:
            return todo

        self.mock_repository.save.side_effect = save_todo

        response = self.usecase.execute(request)

        assert response.title == "最小限タスク"
        assert response.description == ""
        assert response.priority == "medium"  # デフォルト値

    def test_create_todo_empty_title_error(self) -> None:
        """空のタイトルでエラーが発生することをテスト"""
        request = CreateTodoRequest(title="")

        with pytest.raises(ValueError, match="タイトルは必須です"):
            self.usecase.execute(request)

        # Repository の save は呼ばれない
        self.mock_repository.save.assert_not_called()

    def test_create_todo_whitespace_only_title_error(self) -> None:
        """空白のみのタイトルでエラーが発生することをテスト"""
        request = CreateTodoRequest(title="   ")

        with pytest.raises(ValueError, match="タイトルは必須です"):
            self.usecase.execute(request)

    def test_create_todo_title_too_long_error(self) -> None:
        """長すぎるタイトルでエラーが発生することをテスト"""
        long_title = "あ" * 101  # 101文字
        request = CreateTodoRequest(title=long_title)

        with pytest.raises(ValueError, match="タイトルは100文字以内"):
            self.usecase.execute(request)

    def test_create_todo_description_too_long_error(self) -> None:
        """長すぎる説明でエラーが発生することをテスト"""
        long_description = "あ" * 501  # 501文字
        request = CreateTodoRequest(title="有効なタイトル", description=long_description)

        with pytest.raises(ValueError, match="説明は500文字以内"):
            self.usecase.execute(request)

    def test_create_todo_invalid_priority_error(self) -> None:
        """不正な優先度でエラーが発生することをテスト"""
        request = CreateTodoRequest(title="有効なタイトル", priority="invalid")

        with pytest.raises(ValueError, match="優先度の指定が不正です"):
            self.usecase.execute(request)

    def test_create_todo_title_trimming(self) -> None:
        """タイトルの前後の空白がトリムされることをテスト"""
        request = CreateTodoRequest(title="  前後に空白  ")

        def save_todo(todo: Todo) -> Todo:
            return todo

        self.mock_repository.save.side_effect = save_todo

        response = self.usecase.execute(request)

        assert response.title == "前後に空白"

    def test_create_todo_repository_exception(self) -> None:
        """Repository で例外が発生した場合のテスト"""
        request = CreateTodoRequest(title="有効なタスク")

        # Repository で例外を発生させる
        self.mock_repository.save.side_effect = Exception("保存エラー")

        with pytest.raises(Exception, match="保存エラー"):
            self.usecase.execute(request)


class TestListTodosUseCase:
    """ListTodosUseCase のテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.mock_repository = Mock()
        self.usecase = ListTodosUseCase(self.mock_repository)

        # テスト用 Todo の準備
        self.todo1 = Todo(
            id=TodoID.generate(),
            title="タスク1",
            description="説明1",
            priority="high",
            is_completed=False,
            created_at=datetime(2024, 1, 1, 10, 0),
            updated_at=datetime(2024, 1, 1, 10, 0),
        )

        self.todo2 = Todo(
            id=TodoID.generate(),
            title="タスク2",
            description="説明2",
            priority="medium",
            is_completed=True,
            created_at=datetime(2024, 1, 2, 10, 0),
            updated_at=datetime(2024, 1, 2, 10, 0),
        )

        self.todo3 = Todo(
            id=TodoID.generate(),
            title="タスク3",
            description="説明3",
            priority="low",
            is_completed=False,
            created_at=datetime(2024, 1, 3, 10, 0),
            updated_at=datetime(2024, 1, 3, 10, 0),
        )

    def test_list_all_todos(self) -> None:
        """全件取得テスト"""
        todos = [self.todo1, self.todo2, self.todo3]
        self.mock_repository.find_all.return_value = todos

        responses = self.usecase.execute()

        assert len(responses) == 3
        # デフォルトは作成日時順（新しい順）
        assert responses[0].title == "タスク3"  # 最新
        assert responses[1].title == "タスク2"
        assert responses[2].title == "タスク1"  # 最古

        self.mock_repository.find_all.assert_called_once()

    def test_list_completed_todos_only(self) -> None:
        """完了済みのみ取得テスト"""
        completed_todos = [self.todo2]
        self.mock_repository.find_by_completion_status.return_value = completed_todos

        responses = self.usecase.execute(completed_only=True)

        assert len(responses) == 1
        assert responses[0].title == "タスク2"
        assert responses[0].is_completed is True

        self.mock_repository.find_by_completion_status.assert_called_once_with(True)

    def test_list_pending_todos_only(self) -> None:
        """未完了のみ取得テスト"""
        pending_todos = [self.todo1, self.todo3]
        self.mock_repository.find_by_completion_status.return_value = pending_todos

        responses = self.usecase.execute(completed_only=False)

        assert len(responses) == 2
        # デフォルトは作成日時順（新しい順）
        assert responses[0].title == "タスク3"  # 新しい
        assert responses[1].title == "タスク1"  # 古い

        self.mock_repository.find_by_completion_status.assert_called_once_with(False)

    def test_list_todos_sorted_by_priority(self) -> None:
        """優先度順ソートテスト"""
        todos = [self.todo1, self.todo2, self.todo3]  # high, medium, low
        self.mock_repository.find_all.return_value = todos

        responses = self.usecase.execute(sort_by_priority=True)

        assert len(responses) == 3
        # 優先度順: high -> medium -> low
        assert responses[0].priority == "high"  # todo1
        assert responses[1].priority == "medium"  # todo2
        assert responses[2].priority == "low"  # todo3

    def test_list_empty_result(self) -> None:
        """空の結果のテスト"""
        self.mock_repository.find_all.return_value = []

        responses = self.usecase.execute()

        assert responses == []

    def test_list_todos_priority_sort_with_same_priority(self) -> None:
        """同じ優先度での作成日時ソートテスト"""
        # 同じ優先度（medium）の Todo を作成
        todo_same_priority1 = Todo(
            id=TodoID.generate(),
            title="medium1",
            description="",
            priority="medium",
            is_completed=False,
            created_at=datetime(2024, 1, 1, 10, 0),
            updated_at=datetime(2024, 1, 1, 10, 0),
        )

        todo_same_priority2 = Todo(
            id=TodoID.generate(),
            title="medium2",
            description="",
            priority="medium",
            is_completed=False,
            created_at=datetime(2024, 1, 2, 10, 0),  # より新しい
            updated_at=datetime(2024, 1, 2, 10, 0),
        )

        todos = [todo_same_priority1, todo_same_priority2]
        self.mock_repository.find_all.return_value = todos

        responses = self.usecase.execute(sort_by_priority=True)

        # 同じ優先度の場合は作成日時順（古い順）
        assert responses[0].title == "medium1"  # 古い方が先
        assert responses[1].title == "medium2"


class TestUpdateTodoUseCase:
    """UpdateTodoUseCase のテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.mock_repository = Mock()
        self.usecase = UpdateTodoUseCase(self.mock_repository)

        self.todo_id = TodoID.generate()
        self.existing_todo = Todo(
            id=self.todo_id,
            title="既存タスク",
            description="既存説明",
            priority="medium",
            is_completed=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def test_update_todo_success_full(self) -> None:
        """全項目更新成功テスト"""
        self.mock_repository.find_by_id.return_value = self.existing_todo

        # 更新後の Todo を返すモック
        def save_todo(todo: Todo) -> Todo:
            return todo

        self.mock_repository.save.side_effect = save_todo

        request = UpdateTodoRequest(
            todo_id=str(self.todo_id),
            title="更新されたタスク",
            description="更新された説明",
            priority="high",
        )

        response = self.usecase.execute(request)

        assert response.title == "更新されたタスク"
        assert response.description == "更新された説明"
        assert response.priority == "high"

        self.mock_repository.find_by_id.assert_called_once()
        self.mock_repository.save.assert_called_once()

    def test_update_todo_success_partial(self) -> None:
        """部分更新成功テスト"""
        self.mock_repository.find_by_id.return_value = self.existing_todo

        def save_todo(todo: Todo) -> Todo:
            return todo

        self.mock_repository.save.side_effect = save_todo

        request = UpdateTodoRequest(
            todo_id=str(self.todo_id),
            title="新しいタイトルのみ",
            # description と priority は None（更新しない）
        )

        response = self.usecase.execute(request)

        assert response.title == "新しいタイトルのみ"
        assert response.description == self.existing_todo.description  # 元のまま
        assert response.priority == self.existing_todo.priority  # 元のまま

    def test_update_todo_not_found(self) -> None:
        """存在しない Todo の更新でエラーテスト"""
        self.mock_repository.find_by_id.return_value = None

        request = UpdateTodoRequest(todo_id="non-existent-id", title="新しいタイトル")

        with pytest.raises(ValueError, match="指定された Todo が見つかりません"):
            self.usecase.execute(request)

        # save は呼ばれない
        self.mock_repository.save.assert_not_called()

    def test_update_todo_empty_title_error(self) -> None:
        """空のタイトルに更新しようとしてエラーテスト"""
        self.mock_repository.find_by_id.return_value = self.existing_todo

        request = UpdateTodoRequest(todo_id=str(self.todo_id), title="")

        with pytest.raises(ValueError, match="タイトルは必須です"):
            self.usecase.execute(request)

    def test_update_todo_title_too_long_error(self) -> None:
        """長すぎるタイトルでエラーテスト"""
        self.mock_repository.find_by_id.return_value = self.existing_todo

        request = UpdateTodoRequest(todo_id=str(self.todo_id), title="あ" * 101)

        with pytest.raises(ValueError, match="タイトルは100文字以内"):
            self.usecase.execute(request)

    def test_update_todo_description_too_long_error(self) -> None:
        """長すぎる説明でエラーテスト"""
        self.mock_repository.find_by_id.return_value = self.existing_todo

        request = UpdateTodoRequest(todo_id=str(self.todo_id), description="あ" * 501)

        with pytest.raises(ValueError, match="説明は500文字以内"):
            self.usecase.execute(request)

    def test_update_todo_invalid_priority_error(self) -> None:
        """不正な優先度でエラーテスト"""
        self.mock_repository.find_by_id.return_value = self.existing_todo

        request = UpdateTodoRequest(todo_id=str(self.todo_id), priority="invalid")

        with pytest.raises(ValueError, match="無効な優先度"):
            self.usecase.execute(request)


class TestToggleTodoUseCase:
    """ToggleTodoUseCase のテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.mock_repository = Mock()
        self.usecase = ToggleTodoUseCase(self.mock_repository)

        self.todo_id = TodoID.generate()
        self.incomplete_todo = Todo(
            id=self.todo_id,
            title="未完了タスク",
            description="説明",
            priority="medium",
            is_completed=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def test_toggle_incomplete_to_complete(self) -> None:
        """未完了から完了への切り替えテスト"""
        self.mock_repository.find_by_id.return_value = self.incomplete_todo

        def save_todo(todo: Todo) -> Todo:
            return todo

        self.mock_repository.save.side_effect = save_todo

        response = self.usecase.execute(str(self.todo_id))

        assert response.is_completed is True
        assert response.title == self.incomplete_todo.title

        self.mock_repository.find_by_id.assert_called_once()
        self.mock_repository.save.assert_called_once()

    def test_toggle_complete_to_incomplete(self) -> None:
        """完了から未完了への切り替えテスト"""
        completed_todo = self.incomplete_todo.mark_completed()
        self.mock_repository.find_by_id.return_value = completed_todo

        def save_todo(todo: Todo) -> Todo:
            return todo

        self.mock_repository.save.side_effect = save_todo

        response = self.usecase.execute(str(self.todo_id))

        assert response.is_completed is False
        assert response.title == completed_todo.title

    def test_toggle_todo_not_found(self) -> None:
        """存在しない Todo の切り替えでエラーテスト"""
        self.mock_repository.find_by_id.return_value = None

        with pytest.raises(ValueError, match="指定された Todo が見つかりません"):
            self.usecase.execute("non-existent-id")

        # save は呼ばれない
        self.mock_repository.save.assert_not_called()


class TestDeleteTodoUseCase:
    """DeleteTodoUseCase のテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.mock_repository = Mock()
        self.usecase = DeleteTodoUseCase(self.mock_repository)

    def test_delete_todo_success(self) -> None:
        """Todo 削除成功テスト"""
        self.mock_repository.delete.return_value = True

        result = self.usecase.execute("existing-id")

        assert result is True
        self.mock_repository.delete.assert_called_once()

    def test_delete_todo_not_found(self) -> None:
        """存在しない Todo の削除テスト"""
        self.mock_repository.delete.return_value = False

        result = self.usecase.execute("non-existent-id")

        assert result is False
        self.mock_repository.delete.assert_called_once()

    def test_delete_completed_todos_success(self) -> None:
        """完了済み Todo 一括削除成功テスト"""
        self.mock_repository.delete_completed.return_value = 3

        result = self.usecase.delete_completed()

        assert result == 3
        self.mock_repository.delete_completed.assert_called_once()

    def test_delete_completed_todos_none(self) -> None:
        """削除対象の完了済み Todo がない場合のテスト"""
        self.mock_repository.delete_completed.return_value = 0

        result = self.usecase.delete_completed()

        assert result == 0
        self.mock_repository.delete_completed.assert_called_once()


class TestRequestObjects:
    """リクエストオブジェクトのテスト"""

    def test_create_todo_request_defaults(self) -> None:
        """CreateTodoRequest のデフォルト値テスト"""
        request = CreateTodoRequest(title="テストタスク")

        assert request.title == "テストタスク"
        assert request.description == ""
        assert request.priority == "medium"

    def test_create_todo_request_full(self) -> None:
        """CreateTodoRequest の全項目指定テスト"""
        request = CreateTodoRequest(title="フルタスク", description="詳細説明", priority="high")

        assert request.title == "フルタスク"
        assert request.description == "詳細説明"
        assert request.priority == "high"

    def test_update_todo_request_defaults(self) -> None:
        """UpdateTodoRequest のデフォルト値テスト"""
        request = UpdateTodoRequest(todo_id="test-id")

        assert request.todo_id == "test-id"
        assert request.title is None
        assert request.description is None
        assert request.priority is None

    def test_update_todo_request_partial(self) -> None:
        """UpdateTodoRequest の部分指定テスト"""
        request = UpdateTodoRequest(todo_id="test-id", title="新しいタイトル")

        assert request.todo_id == "test-id"
        assert request.title == "新しいタイトル"
        assert request.description is None
        assert request.priority is None

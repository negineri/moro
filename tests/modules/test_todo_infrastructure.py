"""Infrastructure Layer のテスト

Todo モジュールのインフラストラクチャレイヤーのテスト実装。

教育的ポイント:
- Repository パターンの具体実装テスト
- Pydantic による設定管理のテスト
- メモリ内データ構造の動作検証
- エラーハンドリングの確認
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from moro.modules.todo.domain import Todo, TodoID
from moro.modules.todo.infrastructure import InMemoryTodoRepository, TodoConfig


class TestTodoConfig:
    """TodoConfig の設定管理テスト"""

    def test_default_values(self) -> None:
        """デフォルト値のテスト"""
        config = TodoConfig()

        assert config.max_todos == 1000
        assert config.auto_cleanup_days == 30
        assert config.default_priority == "medium"

    def test_pydantic_validation_success(self) -> None:
        """有効な値での Pydantic バリデーション成功テスト"""
        config = TodoConfig(max_todos=500, auto_cleanup_days=15, default_priority="high")

        assert config.max_todos == 500
        assert config.auto_cleanup_days == 15
        assert config.default_priority == "high"

    def test_max_todos_validation(self) -> None:
        """max_todos の値範囲バリデーションテスト"""
        # 有効な値
        TodoConfig(max_todos=1)  # 最小値
        TodoConfig(max_todos=10000)  # 最大値
        TodoConfig(max_todos=500)  # 中間値

        # 無効な値でエラー
        with pytest.raises(ValidationError):
            TodoConfig(max_todos=0)  # 最小値未満

        with pytest.raises(ValidationError):
            TodoConfig(max_todos=10001)  # 最大値超過

        with pytest.raises(ValidationError):
            TodoConfig(max_todos=-1)  # 負の値

    def test_auto_cleanup_days_validation(self) -> None:
        """auto_cleanup_days の値範囲バリデーションテスト"""
        # 有効な値
        TodoConfig(auto_cleanup_days=1)  # 最小値
        TodoConfig(auto_cleanup_days=365)  # 最大値
        TodoConfig(auto_cleanup_days=90)  # 中間値

        # 無効な値でエラー
        with pytest.raises(ValidationError):
            TodoConfig(auto_cleanup_days=0)  # 最小値未満

        with pytest.raises(ValidationError):
            TodoConfig(auto_cleanup_days=366)  # 最大値超過

    def test_default_priority_pattern_validation(self) -> None:
        """default_priority のパターンバリデーションテスト"""
        # 有効な値
        TodoConfig(default_priority="high")
        TodoConfig(default_priority="medium")
        TodoConfig(default_priority="low")

        # 無効な値でエラー
        with pytest.raises(ValidationError):
            TodoConfig(default_priority="urgent")

        with pytest.raises(ValidationError):
            TodoConfig(default_priority="normal")

        with pytest.raises(ValidationError):
            TodoConfig(default_priority="")

    def test_config_serialization(self) -> None:
        """設定のシリアライゼーションテスト"""
        config = TodoConfig(max_todos=2000, auto_cleanup_days=60, default_priority="low")

        # 辞書への変換
        config_dict = config.model_dump()
        expected = {"max_todos": 2000, "auto_cleanup_days": 60, "default_priority": "low"}
        assert config_dict == expected

        # JSON への変換
        config_json = config.model_dump_json()
        assert '"max_todos":2000' in config_json
        assert '"default_priority":"low"' in config_json


class TestInMemoryTodoRepository:
    """InMemoryTodoRepository のテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.config = TodoConfig(max_todos=10)  # テスト用に十分な値
        self.repository = InMemoryTodoRepository(self.config)
        self.todo_id = TodoID.generate()
        self.now = datetime.now()
        self.sample_todo = Todo(
            id=self.todo_id,
            title="テストタスク",
            description="テスト用の説明",
            priority="medium",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

    def test_save_and_find_by_id_success(self) -> None:
        """保存と ID による取得の成功テスト"""
        # 保存
        saved_todo = self.repository.save(self.sample_todo)
        assert saved_todo is self.sample_todo  # 同じインスタンスが返される

        # 取得
        found_todo = self.repository.find_by_id(self.todo_id)
        assert found_todo == self.sample_todo
        assert found_todo is self.sample_todo  # 同じインスタンス

    def test_find_by_id_not_found(self) -> None:
        """存在しない ID での取得テスト"""
        non_existent_id = TodoID.generate()
        result = self.repository.find_by_id(non_existent_id)
        assert result is None

    def test_save_update_existing(self) -> None:
        """既存 Todo の更新保存テスト"""
        # 初回保存
        self.repository.save(self.sample_todo)

        # 更新された Todo を保存
        updated_todo = self.sample_todo.update_content(
            title="更新されたタイトル",
            description=self.sample_todo.description,
            priority=self.sample_todo.priority,
        )
        saved_updated = self.repository.save(updated_todo)

        # 更新されたインスタンスが返される
        assert saved_updated is updated_todo

        # リポジトリからも更新されたバージョンが取得される
        found_todo = self.repository.find_by_id(self.todo_id)
        assert found_todo == updated_todo
        assert found_todo is not None
        assert found_todo.title == "更新されたタイトル"

    def test_save_max_todos_limit_new_todo(self) -> None:
        """新規 Todo の最大件数制限テスト"""
        # max_todos=10 まで保存
        for i in range(10):
            todo = Todo(
                id=TodoID.generate(),
                title=f"タスク{i}",
                description="",
                priority="medium",
                is_completed=False,
                created_at=self.now,
                updated_at=self.now,
            )
            self.repository.save(todo)

        # 11件目で制限に引っかかる
        extra_todo = Todo(
            id=TodoID.generate(),
            title="制限超過",
            description="",
            priority="medium",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        with pytest.raises(ValueError, match="最大 Todo 件数"):
            self.repository.save(extra_todo)

    def test_save_max_todos_limit_update_allowed(self) -> None:
        """既存 Todo の更新は最大件数制限に影響しないテスト"""
        # max_todos=10 まで保存
        todos: list[Todo] = []
        for i in range(10):
            todo = Todo(
                id=TodoID.generate(),
                title=f"タスク{i}",
                description="",
                priority="medium",
                is_completed=False,
                created_at=self.now,
                updated_at=self.now,
            )
            self.repository.save(todo)
            todos.append(todo)

        # 既存 Todo の更新は制限に引っかからない
        updated_todo = todos[0].update_content(
            title="更新されたタスク", description=todos[0].description, priority=todos[0].priority
        )

        # 例外が発生しないことを確認
        self.repository.save(updated_todo)

        # 正しく更新されていることを確認
        found = self.repository.find_by_id(todos[0].id)
        assert found is not None
        assert found.title == "更新されたタスク"

    def test_find_all_empty(self) -> None:
        """空のリポジトリでの全件取得テスト"""
        result = self.repository.find_all()
        assert result == []

    def test_find_all_with_todos(self) -> None:
        """Todo が存在する状態での全件取得テスト"""
        # 複数の Todo を保存
        todos: list[Todo] = []
        for i in range(3):
            todo = Todo(
                id=TodoID.generate(),
                title=f"タスク{i}",
                description=f"説明{i}",
                priority="medium",
                is_completed=i % 2 == 0,  # 偶数番号は完了済み
                created_at=self.now,
                updated_at=self.now,
            )
            self.repository.save(todo)
            todos.append(todo)

        # 全件取得
        all_todos = self.repository.find_all()
        assert len(all_todos) == 3

        # すべての Todo が含まれていることを確認
        all_ids = {todo.id for todo in all_todos}
        expected_ids = {todo.id for todo in todos}
        assert all_ids == expected_ids

    def test_find_by_completion_status(self) -> None:
        """完了状態による検索テスト"""
        # 完了済み、未完了の Todo を保存
        completed_todo = Todo(
            id=TodoID.generate(),
            title="完了済みタスク",
            description="",
            priority="high",
            is_completed=True,
            created_at=self.now,
            updated_at=self.now,
        )

        pending_todo = Todo(
            id=TodoID.generate(),
            title="未完了タスク",
            description="",
            priority="low",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        self.repository.save(completed_todo)
        self.repository.save(pending_todo)

        # 完了済みのみ取得
        completed_todos = self.repository.find_by_completion_status(True)
        assert len(completed_todos) == 1
        assert completed_todos[0] == completed_todo

        # 未完了のみ取得
        pending_todos = self.repository.find_by_completion_status(False)
        assert len(pending_todos) == 1
        assert pending_todos[0] == pending_todo

    def test_find_by_completion_status_empty_result(self) -> None:
        """該当する完了状態の Todo が存在しない場合のテスト"""
        # 未完了の Todo のみ保存
        self.repository.save(self.sample_todo)

        # 完了済みを検索（該当なし）
        completed_todos = self.repository.find_by_completion_status(True)
        assert completed_todos == []

    def test_delete_existing_todo(self) -> None:
        """存在する Todo の削除テスト"""
        # Todo を保存
        self.repository.save(self.sample_todo)

        # 削除実行
        result = self.repository.delete(self.todo_id)
        assert result is True

        # 削除後は取得できない
        found = self.repository.find_by_id(self.todo_id)
        assert found is None

    def test_delete_non_existent_todo(self) -> None:
        """存在しない Todo の削除テスト"""
        non_existent_id = TodoID.generate()
        result = self.repository.delete(non_existent_id)
        assert result is False

    def test_delete_completed_with_completed_todos(self) -> None:
        """完了済み Todo の一括削除テスト（完了済みあり）"""
        # 完了済み、未完了の Todo を保存
        completed_ids: list[TodoID] = []
        pending_ids: list[TodoID] = []

        for i in range(5):
            todo = Todo(
                id=TodoID.generate(),
                title=f"タスク{i}",
                description="",
                priority="medium",
                is_completed=i < 3,  # 最初の3件は完了済み
                created_at=self.now,
                updated_at=self.now,
            )
            self.repository.save(todo)

            if todo.is_completed:
                completed_ids.append(todo.id)
            else:
                pending_ids.append(todo.id)

        # 一括削除実行
        deleted_count = self.repository.delete_completed()
        assert deleted_count == 3  # 完了済み 3 件が削除される

        # 完了済み Todo は削除されている
        for todo_id in completed_ids:
            assert self.repository.find_by_id(todo_id) is None

        # 未完了 Todo は残っている
        for todo_id in pending_ids:
            assert self.repository.find_by_id(todo_id) is not None

    def test_delete_completed_no_completed_todos(self) -> None:
        """完了済み Todo の一括削除テスト（完了済みなし）"""
        # 未完了の Todo のみ保存
        for i in range(3):
            todo = Todo(
                id=TodoID.generate(),
                title=f"タスク{i}",
                description="",
                priority="medium",
                is_completed=False,
                created_at=self.now,
                updated_at=self.now,
            )
            self.repository.save(todo)

        # 一括削除実行（削除対象なし）
        deleted_count = self.repository.delete_completed()
        assert deleted_count == 0

        # すべての Todo が残っている
        remaining_todos = self.repository.find_all()
        assert len(remaining_todos) == 3

    def test_count_empty(self) -> None:
        """空のリポジトリでの件数取得テスト"""
        assert self.repository.count() == 0

    def test_count_with_todos(self) -> None:
        """Todo が存在する状態での件数取得テスト"""
        # 複数の Todo を保存
        for i in range(4):
            todo = Todo(
                id=TodoID.generate(),
                title=f"タスク{i}",
                description="",
                priority="medium",
                is_completed=False,
                created_at=self.now,
                updated_at=self.now,
            )
            self.repository.save(todo)

        assert self.repository.count() == 4

    def test_clear_for_testing(self) -> None:
        """テスト用 clear メソッドのテスト"""
        # Todo を保存
        for i in range(3):
            todo = Todo(
                id=TodoID.generate(),
                title=f"タスク{i}",
                description="",
                priority="medium",
                is_completed=False,
                created_at=self.now,
                updated_at=self.now,
            )
            self.repository.save(todo)

        assert self.repository.count() == 3

        # 全削除
        self.repository.clear()

        assert self.repository.count() == 0
        assert self.repository.find_all() == []

    def test_repository_isolation(self) -> None:
        """複数のリポジトリインスタンス間の独立性テスト"""
        another_repository = InMemoryTodoRepository(self.config)

        # 最初のリポジトリに保存
        self.repository.save(self.sample_todo)

        # 別のリポジトリには存在しない
        assert another_repository.find_by_id(self.todo_id) is None
        assert another_repository.count() == 0

    def test_complex_scenario(self) -> None:
        """複合的なシナリオテスト"""
        # 1. 複数の Todo を保存
        todos: list[Todo] = []
        for i in range(3):
            todo = Todo(
                id=TodoID.generate(),
                title=f"タスク{i}",
                description=f"説明{i}",
                priority=["high", "medium", "low"][i],  # type: ignore
                is_completed=False,
                created_at=self.now,
                updated_at=self.now,
            )
            self.repository.save(todo)
            todos.append(todo)

        assert self.repository.count() == 3

        # 2. 一つを完了状態に更新
        completed_todo = todos[0].mark_completed()
        self.repository.save(completed_todo)

        # 3. 完了済みのみ取得
        completed_list = self.repository.find_by_completion_status(True)
        assert len(completed_list) == 1
        assert completed_list[0].title == "タスク0"

        # 4. 一つを削除
        deleted = self.repository.delete(todos[1].id)
        assert deleted is True
        assert self.repository.count() == 2

        # 5. 完了済み一括削除
        deleted_count = self.repository.delete_completed()
        assert deleted_count == 1
        assert self.repository.count() == 1

        # 6. 残っているのは todos[2] のみ
        remaining = self.repository.find_all()
        assert len(remaining) == 1
        assert remaining[0].title == "タスク2"

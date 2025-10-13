"""TODOモジュール独立ドメインテスト

他モジュールへの依存・参照は一切禁止
moro.modules.todo.* のみimport許可
"""

import uuid
from datetime import datetime

import pytest

from moro.modules.todo.domain import Todo, TodoID, validate_priority


@pytest.mark.unit
class TestPriority:
    """Priority 型とバリデーション関数のテスト"""

    def test_validate_priority_success(self) -> None:
        """有効な優先度文字列のテスト"""
        assert validate_priority("high") == "high"
        assert validate_priority("medium") == "medium"
        assert validate_priority("low") == "low"

    def test_validate_priority_case_insensitive(self) -> None:
        """大文字小文字を区別しないテスト"""
        assert validate_priority("HIGH") == "high"
        assert validate_priority("Medium") == "medium"
        assert validate_priority("LOW") == "low"
        assert validate_priority("HiGh") == "high"

    def test_validate_priority_invalid_raises_error(self) -> None:
        """不正な優先度文字列でエラーが発生することをテスト"""
        with pytest.raises(ValueError, match="無効な優先度"):
            validate_priority("invalid")

        with pytest.raises(ValueError, match="無効な優先度"):
            validate_priority("")

        with pytest.raises(ValueError, match="無効な優先度"):
            validate_priority("urgent")


@pytest.mark.unit
class TestTodoID:
    """TodoID 値オブジェクトのテスト"""

    def test_todo_id_creation(self) -> None:
        """TodoID の作成テスト"""
        test_id = "test-id-123"
        todo_id = TodoID(test_id)

        assert todo_id.value == test_id
        assert str(todo_id) == test_id

    def test_todo_id_generate(self) -> None:
        """ランダム TodoID の生成テスト"""
        todo_id1 = TodoID.generate()
        todo_id2 = TodoID.generate()

        # 異なる ID が生成されることを確認
        assert todo_id1.value != todo_id2.value

        # UUID 形式であることを確認
        uuid.UUID(todo_id1.value)  # 有効でなければ例外が発生
        uuid.UUID(todo_id2.value)

    def test_todo_id_immutable(self) -> None:
        """TodoID の不変性テスト"""
        todo_id = TodoID("test-id")

        # frozen=True により属性変更は不可
        with pytest.raises(AttributeError):
            todo_id.value = "new-id"  # type: ignore[misc]

    def test_todo_id_equality(self) -> None:
        """TodoID の等価性テスト"""
        todo_id1 = TodoID("same-id")
        todo_id2 = TodoID("same-id")
        todo_id3 = TodoID("different-id")

        assert todo_id1 == todo_id2
        assert todo_id1 != todo_id3


@pytest.mark.unit
class TestTodo:
    """Todo エンティティのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行される共通セットアップ"""
        self.todo_id = TodoID.generate()
        self.now = datetime.now()
        self.base_todo = Todo(
            id=self.todo_id,
            title="テストタスク",
            description="テスト用の説明",
            priority="medium",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

    def test_todo_creation(self) -> None:
        """Todo エンティティの作成テスト"""
        todo = Todo(
            id=self.todo_id,
            title="買い物",
            description="スーパーで食材を購入",
            priority="high",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        assert todo.id == self.todo_id
        assert todo.title == "買い物"
        assert todo.description == "スーパーで食材を購入"
        assert todo.priority == "high"
        assert todo.is_completed is False
        assert todo.created_at == self.now
        assert todo.updated_at == self.now

    def test_todo_immutable(self) -> None:
        """Todo エンティティの不変性テスト"""
        # frozen=True により属性変更は不可
        with pytest.raises(AttributeError):
            self.base_todo.title = "新しいタイトル"  # type: ignore[misc]

        with pytest.raises(AttributeError):
            self.base_todo.is_completed = True  # type: ignore[misc]

    def test_mark_completed_creates_new_instance(self) -> None:
        """完了状態への変更が新しいインスタンスを返すことをテスト"""
        completed_todo = self.base_todo.mark_completed()

        # 元のインスタンスは変更されない
        assert self.base_todo.is_completed is False

        # 新しいインスタンスは完了状態
        assert completed_todo.is_completed is True
        assert completed_todo.id == self.base_todo.id
        assert completed_todo.title == self.base_todo.title
        assert completed_todo.description == self.base_todo.description
        assert completed_todo.priority == self.base_todo.priority
        assert completed_todo.created_at == self.base_todo.created_at

        # 更新日時は変更される
        assert completed_todo.updated_at > self.base_todo.updated_at

    def test_mark_completed_idempotent(self) -> None:
        """既に完了済みの Todo を完了状態にした場合、同じインスタンスを返すテスト"""
        completed_todo = self.base_todo.mark_completed()
        same_todo = completed_todo.mark_completed()

        # 同じインスタンスが返される（同一オブジェクト）
        assert same_todo is completed_todo

    def test_mark_incomplete_creates_new_instance(self) -> None:
        """未完了状態への変更が新しいインスタンスを返すことをテスト"""
        completed_todo = self.base_todo.mark_completed()
        incomplete_todo = completed_todo.mark_incomplete()

        # 完了状態から未完了状態に変更
        assert completed_todo.is_completed is True
        assert incomplete_todo.is_completed is False

        # その他の属性は保持
        assert incomplete_todo.id == completed_todo.id
        assert incomplete_todo.title == completed_todo.title
        assert incomplete_todo.description == completed_todo.description
        assert incomplete_todo.priority == completed_todo.priority
        assert incomplete_todo.created_at == completed_todo.created_at

        # 更新日時は変更される
        assert incomplete_todo.updated_at > completed_todo.updated_at

    def test_mark_incomplete_idempotent(self) -> None:
        """既に未完了の Todo を未完了状態にした場合、同じインスタンスを返すテスト"""
        same_todo = self.base_todo.mark_incomplete()

        # 同じインスタンスが返される（同一オブジェクト）
        assert same_todo is self.base_todo

    def test_update_content_creates_new_instance(self) -> None:
        """内容更新が新しいインスタンスを返すことをテスト"""
        updated_todo = self.base_todo.update_content(
            title="新しいタイトル", description="新しい説明", priority="high"
        )

        # 元のインスタンスは変更されない
        assert self.base_todo.title == "テストタスク"
        assert self.base_todo.description == "テスト用の説明"
        assert self.base_todo.priority == "medium"

        # 新しいインスタンスは更新されている
        assert updated_todo.title == "新しいタイトル"
        assert updated_todo.description == "新しい説明"
        assert updated_todo.priority == "high"

        # その他の属性は保持
        assert updated_todo.id == self.base_todo.id
        assert updated_todo.is_completed == self.base_todo.is_completed
        assert updated_todo.created_at == self.base_todo.created_at

        # 更新日時は変更される
        assert updated_todo.updated_at > self.base_todo.updated_at

    def test_update_content_with_whitespace_trimming(self) -> None:
        """内容更新時の空白トリムテスト"""
        updated_todo = self.base_todo.update_content(
            title="  新しいタイトル  ", description="  新しい説明  ", priority="high"
        )

        assert updated_todo.title == "新しいタイトル"
        assert updated_todo.description == "新しい説明"

    def test_update_content_no_change_returns_same_instance(self) -> None:
        """内容に変更がない場合、同じインスタンスを返すテスト"""
        same_todo = self.base_todo.update_content(
            title=self.base_todo.title,
            description=self.base_todo.description,
            priority=self.base_todo.priority,
        )

        # 同じインスタンスが返される（同一オブジェクト）
        assert same_todo is self.base_todo

    def test_update_content_partial_change(self) -> None:
        """一部のみ変更した場合の動作テスト"""
        # タイトルのみ変更
        updated_todo = self.base_todo.update_content(
            title="新しいタイトル",
            description=self.base_todo.description,
            priority=self.base_todo.priority,
        )

        assert updated_todo.title == "新しいタイトル"
        assert updated_todo.description == self.base_todo.description
        assert updated_todo.priority == self.base_todo.priority
        assert updated_todo.updated_at > self.base_todo.updated_at

    def test_is_high_priority_property(self) -> None:
        """高優先度判定プロパティのテスト"""
        high_todo = Todo(
            id=self.todo_id,
            title="緊急タスク",
            description="",
            priority="high",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        medium_todo = Todo(
            id=self.todo_id,
            title="通常タスク",
            description="",
            priority="medium",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        low_todo = Todo(
            id=self.todo_id,
            title="低優先タスク",
            description="",
            priority="low",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        assert high_todo.is_high_priority is True
        assert medium_todo.is_high_priority is False
        assert low_todo.is_high_priority is False

    def test_todo_equality(self) -> None:
        """Todo エンティティの等価性テスト"""
        todo1 = Todo(
            id=self.todo_id,
            title="同じタスク",
            description="同じ説明",
            priority="medium",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        todo2 = Todo(
            id=self.todo_id,
            title="同じタスク",
            description="同じ説明",
            priority="medium",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        different_todo = Todo(
            id=TodoID.generate(),
            title="異なるタスク",
            description="異なる説明",
            priority="high",
            is_completed=True,
            created_at=self.now,
            updated_at=self.now,
        )

        assert todo1 == todo2
        assert todo1 != different_todo

    def test_todo_with_empty_description(self) -> None:
        """空の説明での Todo 作成テスト"""
        todo = Todo(
            id=self.todo_id,
            title="タイトルのみ",
            description="",
            priority="low",
            is_completed=False,
            created_at=self.now,
            updated_at=self.now,
        )

        assert todo.description == ""
        assert todo.title == "タイトルのみ"

    def test_todo_state_transitions(self) -> None:
        """Todo の状態遷移の包括的テスト"""
        # 初期状態: 未完了
        assert self.base_todo.is_completed is False

        # 未完了 → 完了
        completed = self.base_todo.mark_completed()
        assert completed.is_completed is True

        # 完了 → 未完了
        back_to_incomplete = completed.mark_incomplete()
        assert back_to_incomplete.is_completed is False

        # 内容更新後も完了状態は保持
        updated_completed = completed.update_content(
            title="更新されたタイトル",
            description=completed.description,
            priority=completed.priority,
        )
        assert updated_completed.is_completed is True
        assert updated_completed.title == "更新されたタイトル"

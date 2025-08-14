"""Use cases for Todo module.

アプリケーションレイヤー - ユースケースの実行とドメインオブジェクトの協調

教育的ポイント:
- ユースケースの責務分離
- リクエスト・レスポンスパターン
- バリデーション戦略
- エラーハンドリングの統一
- ドメインサービスの協調
"""

from dataclasses import dataclass
from datetime import datetime

from injector import inject

from .domain import Todo, TodoID, TodoRepository, validate_priority

# リクエスト・レスポンスオブジェクト


@dataclass
class CreateTodoRequest:
    """Todo 作成リクエスト

    設計判断：
    - プリミティブな型から適切なドメインオブジェクトへの変換を担当
    - バリデーションロジックの集約点
    - 外部インターフェース（CLI/API）との境界

    教育的ポイント:
    - Request パターンによる入力データのカプセル化
    - プリミティブ型とドメイン型の橋渡し
    - デフォルト値による使いやすさの向上
    """

    title: str
    description: str = ""
    priority: str = "medium"


@dataclass
class UpdateTodoRequest:
    """Todo 更新リクエスト

    設計判断:
    - 部分更新に対応（Optional フィールド）
    - ID による対象特定
    - None と空文字列の明確な区別

    教育的ポイント:
    - 部分更新パターンの実装
    - Optional の活用による柔軟性
    - リクエストオブジェクトの設計原則
    """

    todo_id: str
    title: str | None = None
    description: str | None = None
    priority: str | None = None


@dataclass
class TodoResponse:
    """Todo レスポンス（表示用）

    設計判断：
    - ドメインオブジェクトをそのまま外部に公開しない
    - 必要な情報のみを含む軽量なオブジェクト
    - 外部システム向けのデータ形式

    教育的ポイント:
    - レスポンスパターンによる出力データのカプセル化
    - ドメインとプレゼンテーションの分離
    - データ変換の責務の所在
    """

    id: str
    title: str
    description: str
    priority: str
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, todo: Todo) -> "TodoResponse":
        """ドメインオブジェクトから変換

        Args:
            todo: 変換元の Todo エンティティ

        Returns:
            外部向けの TodoResponse

        教育的ポイント:
        - ファクトリーメソッドパターン
        - ドメインオブジェクトからの適切な変換
        - レイヤー間のデータ変換責務
        """
        return cls(
            id=str(todo.id),
            title=todo.title,
            description=todo.description,
            priority=todo.priority,
            is_completed=todo.is_completed,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
        )


# ユースケース実装


class CreateTodoUseCase:
    """Todo 作成ユースケース

    ユースケースの責務：
    - ビジネスルールの実行
    - ドメインオブジェクトの協調
    - インフラストラクチャへの委譲
    - 入力データの検証と変換

    教育的ポイント:
    - ユースケースパターンの実装
    - 依存性注入による疎結合
    - レイヤー間の適切な責務分離
    - エラーハンドリングの統一
    """

    @inject
    def __init__(self, repository: TodoRepository) -> None:
        """ユースケースを初期化

        Args:
            repository: Todo リポジトリ

        教育的ポイント:
        - コンストラクタインジェクション
        - インターフェースへの依存
        - 具体実装への非依存
        """
        self._repository = repository

    def execute(self, request: CreateTodoRequest) -> TodoResponse:
        """Todo を作成する

        フロー：
        1. リクエストのバリデーション
        2. ドメインオブジェクトの生成
        3. ビジネスルールの適用
        4. 永続化の実行
        5. レスポンスオブジェクトの生成

        Args:
            request: 作成リクエスト

        Returns:
            作成された Todo の情報

        Raises:
            ValueError: バリデーションエラーまたはビジネスルール違反

        教育的ポイント:
        - ユースケースの実行フロー
        - バリデーション戦略
        - ドメインオブジェクト生成パターン
        - エラーハンドリングの階層化
        """
        # Step 1: 入力バリデーション（ドメインルール）
        if not request.title.strip():
            raise ValueError("タイトルは必須です")
        if len(request.title.strip()) > 100:
            raise ValueError("タイトルは100文字以内で入力してください")
        if len(request.description) > 500:
            raise ValueError("説明は500文字以内で入力してください")

        # Step 2: 優先度の変換とバリデーション
        try:
            priority = validate_priority(request.priority)
        except ValueError as e:
            raise ValueError(f"優先度の指定が不正です: {e}") from e

        # Step 3: ドメインオブジェクトの生成
        todo_id = TodoID.generate()
        now = datetime.now()

        todo = Todo(
            id=todo_id,
            title=request.title.strip(),
            description=request.description.strip(),
            priority=priority,
            is_completed=False,
            created_at=now,
            updated_at=now,
        )

        # Step 4: 永続化
        saved_todo = self._repository.save(todo)

        # Step 5: レスポンス生成
        return TodoResponse.from_domain(saved_todo)


class ListTodosUseCase:
    """Todo 一覧取得ユースケース

    責務:
    - データ取得とフィルタリング
    - ソート処理の実行
    - レスポンスオブジェクトへの変換

    教育的ポイント:
    - クエリ型ユースケースの設計
    - フィルタリングとソートの実装
    - パフォーマンスを考慮したデータ処理
    """

    @inject
    def __init__(self, repository: TodoRepository) -> None:
        """ユースケースを初期化

        Args:
            repository: Todo リポジトリ
        """
        self._repository = repository

    def execute(
        self, completed_only: bool | None = None, sort_by_priority: bool = False
    ) -> list[TodoResponse]:
        """Todo 一覧を取得する

        Args:
            completed_only: 完了状態でフィルタ（None=全件）
            sort_by_priority: 優先度でソートするか

        Returns:
            Todo のリスト

        教育的ポイント:
        - クエリパラメータによる柔軟な検索
        - Optional による条件指定
        - ソート戦略の実装
        """
        # Step 1: データ取得
        if completed_only is None:
            todos = self._repository.find_all()
        else:
            todos = self._repository.find_by_completion_status(completed_only)

        # Step 2: ソート処理
        if sort_by_priority:
            # 優先度順: high -> medium -> low
            priority_order = {"high": 0, "medium": 1, "low": 2}
            todos.sort(key=lambda t: (priority_order[t.priority], t.created_at))
        else:
            # デフォルトは作成日時順（新しい順）
            todos.sort(key=lambda t: t.created_at, reverse=True)

        # Step 3: レスポンス変換
        return [TodoResponse.from_domain(todo) for todo in todos]


class UpdateTodoUseCase:
    """Todo 更新ユースケース

    責務:
    - 対象 Todo の存在確認
    - 部分更新の処理
    - ビジネスルールの適用
    - 不変エンティティの更新パターン

    教育的ポイント:
    - 部分更新の実装戦略
    - 存在確認と例外処理
    - イミュータブルオブジェクトの更新パターン
    """

    @inject
    def __init__(self, repository: TodoRepository) -> None:
        """ユースケースを初期化

        Args:
            repository: Todo リポジトリ
        """
        self._repository = repository

    def execute(self, request: UpdateTodoRequest) -> TodoResponse:
        """Todo を更新する

        Args:
            request: 更新リクエスト

        Returns:
            更新された Todo の情報

        Raises:
            ValueError: バリデーションエラーまたは Todo が存在しない

        教育的ポイント:
        - 存在確認の重要性
        - 部分更新のロジック
        - イミュータブルパターンの実践
        """
        # Step 1: 存在確認
        todo_id = TodoID(request.todo_id)
        todo = self._repository.find_by_id(todo_id)
        if todo is None:
            raise ValueError(f"指定された Todo が見つかりません: {request.todo_id}")

        # Step 2: 更新データの準備（部分更新対応）
        title = request.title if request.title is not None else todo.title
        description = request.description if request.description is not None else todo.description
        priority = (
            validate_priority(request.priority) if request.priority is not None else todo.priority
        )

        # Step 3: バリデーション
        if not title.strip():
            raise ValueError("タイトルは必須です")
        if len(title.strip()) > 100:
            raise ValueError("タイトルは100文字以内で入力してください")
        if len(description) > 500:
            raise ValueError("説明は500文字以内で入力してください")

        # Step 4: 更新実行（イミュータブルパターン）
        updated_todo = todo.update_content(title, description, priority)
        saved_todo = self._repository.save(updated_todo)

        return TodoResponse.from_domain(saved_todo)


class ToggleTodoUseCase:
    """Todo 完了状態切り替えユースケース

    責務:
    - 対象 Todo の存在確認
    - 完了状態の切り替え
    - 状態変更の永続化

    教育的ポイント:
    - 状態切り替えの実装パターン
    - ビジネスロジックのドメインへの委譲
    - 単一責任の原則
    """

    @inject
    def __init__(self, repository: TodoRepository) -> None:
        """ユースケースを初期化

        Args:
            repository: Todo リポジトリ
        """
        self._repository = repository

    def execute(self, todo_id: str) -> TodoResponse:
        """Todo の完了状態を切り替える

        Args:
            todo_id: 対象の TodoID

        Returns:
            更新された Todo の情報

        Raises:
            ValueError: Todo が存在しない

        教育的ポイント:
        - 存在確認の一貫したパターン
        - 状態切り替えロジックの委譲
        - エラーメッセージの一貫性
        """
        # Step 1: 存在確認
        todo_id_obj = TodoID(todo_id)
        todo = self._repository.find_by_id(todo_id_obj)
        if todo is None:
            raise ValueError(f"指定された Todo が見つかりません: {todo_id}")

        # Step 2: 状態切り替え（イミュータブルパターン）
        updated_todo = todo.mark_incomplete() if todo.is_completed else todo.mark_completed()

        # Step 3: 永続化
        saved_todo = self._repository.save(updated_todo)
        return TodoResponse.from_domain(saved_todo)


class DeleteTodoUseCase:
    """Todo 削除ユースケース

    責務:
    - 単一 Todo の削除
    - 完了済み Todo の一括削除
    - 削除結果の報告

    教育的ポイント:
    - 削除操作の設計パターン
    - 一括操作と単一操作の統一インターフェース
    - 操作結果の適切な報告
    """

    @inject
    def __init__(self, repository: TodoRepository) -> None:
        """ユースケースを初期化

        Args:
            repository: Todo リポジトリ
        """
        self._repository = repository

    def execute(self, todo_id: str) -> bool:
        """Todo を削除する

        Args:
            todo_id: 削除する TodoID

        Returns:
            削除成功時は True、存在しない場合は False

        教育的ポイント:
        - 削除操作の結果表現
        - bool による簡潔な成功/失敗表現
        - 存在しない場合のエラーではない扱い
        """
        todo_id_obj = TodoID(todo_id)
        return self._repository.delete(todo_id_obj)

    def delete_completed(self) -> int:
        """完了済み Todo を一括削除する

        Returns:
            削除した Todo の件数

        教育的ポイント:
        - 一括操作の実装パターン
        - 操作結果の定量的報告
        - リポジトリへの適切な委譲
        """
        return self._repository.delete_completed()

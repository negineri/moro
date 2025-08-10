"""Infrastructure layer for Todo module.

インフラストラクチャレイヤー - 外部システムとの統合、データ永続化

教育的ポイント:
- Pydantic による設定管理
- Repository パターンの具体実装
- メモリ内データ構造の設計
- 設定値によるビジネスルール制御
- インフラとドメインの分離
"""


from injector import inject
from pydantic import BaseModel, Field

from .domain import Todo, TodoID


class TodoConfig(BaseModel):
    """Todo モジュールの設定

    Pydantic による設定管理の例：
    - 型安全性の確保
    - バリデーション機能
    - 設定ファイルとの自動連携
    - デフォルト値の管理

    教育的ポイント:
    - Pydantic による設定パターン
    - Field による詳細なバリデーション
    - ビジネス制約の設定への反映
    - 運用性を考慮した設定設計
    """
    max_todos: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="最大 Todo 保存件数"
    )
    auto_cleanup_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="完了済み Todo の自動削除日数"
    )
    default_priority: str = Field(
        default="medium",
        pattern="^(high|medium|low)$",
        description="デフォルト優先度"
    )


class InMemoryTodoRepository:
    """メモリ内 Todo リポジトリ実装

    Repository パターンの実装例：
    - インターフェース（Protocol）に準拠
    - メモリ内辞書による永続化（開発・テスト用）
    - 実際のプロダクトでは DB 実装に置き換え可能
    - 設定値によるビジネスルール制御

    教育的ポイント:
    - Repository パターンの具体実装
    - Protocol による duck typing の活用
    - メモリ効率を考慮したデータ構造
    - エラーハンドリングの統一
    - テスタビリティを考慮した設計
    """

    @inject
    def __init__(self, config: TodoConfig) -> None:
        """リポジトリを初期化

        Args:
            config: Todo モジュールの設定

        教育的ポイント:
        - 依存性注入による設定の受け取り
        - 内部状態の初期化
        - 型安全性の確保
        """
        self._todos: dict[str, Todo] = {}
        self._config = config

    def save(self, todo: Todo) -> Todo:
        """Todo を保存し、保存されたインスタンスを返す

        Args:
            todo: 保存する Todo エンティティ

        Returns:
            保存された Todo エンティティ（同一インスタンス）

        Raises:
            ValueError: 最大件数に達している場合

        実装詳細：
        - メモリ内辞書に保存
        - 最大件数チェック
        - 既存の場合は上書き更新
        - イミュータブルエンティティをそのまま保存

        教育的ポイント：
        - Repository がドメインエンティティの不変性を尊重
        - 保存処理は副作用なし（エンティティ自体は変更されない）
        - ビジネス制約の Infrastructure での実装
        - エラーハンドリングの適切な設計
        """
        # 最大件数チェック（新規追加の場合のみ）
        todo_key = str(todo.id)
        if (todo_key not in self._todos and
            len(self._todos) >= self._config.max_todos):
            raise ValueError(
                f"最大 Todo 件数 ({self._config.max_todos}) に達しています"
            )

        self._todos[todo_key] = todo
        return todo

    def find_by_id(self, todo_id: TodoID) -> Todo | None:
        """ID で Todo を取得する

        Args:
            todo_id: 検索する TodoID

        Returns:
            見つかった Todo、存在しない場合は None

        教育的ポイント:
        - Optional の適切な使用
        - 辞書アクセスのパフォーマンス特性
        - None の明示的な意味（存在しない）
        """
        return self._todos.get(str(todo_id))

    def find_all(self) -> list[Todo]:
        """全ての Todo を取得する

        Returns:
            全 Todo のリスト（空の場合は空リスト）

        教育的ポイント:
        - 辞書の値をリストに変換
        - 空コレクションの自然な扱い
        - メモリコピーのコスト考慮
        """
        return list(self._todos.values())

    def find_by_completion_status(self, is_completed: bool) -> list[Todo]:
        """完了状態で Todo を検索する

        Args:
            is_completed: 検索する完了状態

        Returns:
            条件に合致する Todo のリスト

        教育的ポイント:
        - リスト内包表記による効率的なフィルタリング
        - ビジネス条件のインフラでの実装
        - 関数型的なアプローチ
        """
        return [
            todo for todo in self._todos.values()
            if todo.is_completed == is_completed
        ]

    def delete(self, todo_id: TodoID) -> bool:
        """Todo を削除する

        Args:
            todo_id: 削除する TodoID

        Returns:
            削除成功時は True、対象が存在しない場合は False

        教育的ポイント:
        - 削除操作の結果を bool で表現
        - 存在チェックと削除の原子性
        - 副作用の明確化
        """
        todo_key = str(todo_id)
        if todo_key in self._todos:
            del self._todos[todo_key]
            return True
        return False

    def delete_completed(self) -> int:
        """完了済み Todo を一括削除する

        Returns:
            削除した Todo の件数

        教育的ポイント:
        - 一括操作の効率的な実装
        - 削除件数の定量的な報告
        - 辞書操作の原子性確保
        """
        # 完了済み Todo のキーを収集
        completed_keys = [
            str(todo.id) for todo in self._todos.values()
            if todo.is_completed
        ]

        # 一括削除実行
        for key in completed_keys:
            del self._todos[key]

        return len(completed_keys)

    def count(self) -> int:
        """Todo の総数を取得する

        Returns:
            Todo の総数

        教育的ポイント:
        - 集約操作の効率的な実装
        - O(1) の時間計算量
        - パフォーマンスを考慮した設計
        """
        return len(self._todos)

    def clear(self) -> None:
        """全ての Todo を削除する（テスト用）

        注意: この操作は不可逆です。
        テスト環境でのみ使用してください。

        教育的ポイント:
        - テスト支援メソッドの分離
        - 危険な操作の明示的な文書化
        - 開発とプロダクションの使い分け
        """
        self._todos.clear()

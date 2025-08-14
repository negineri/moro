"""Domain model for Todo module.

ドメインレイヤー - ビジネスロジックとドメインルールの実装

教育的ポイント:
- Literal 型による制約の表現
- 不変エンティティの設計パターン
- Protocol による duck typing
- 値オブジェクトの実装方法
- ビジネスルールのカプセル化
"""

import dataclasses
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

# 型制約による優先度表現
Priority = Literal["high", "medium", "low"]


def validate_priority(value: str) -> Priority:
    """優先度文字列をバリデーションして Priority 型を返す

    Args:
        value: 優先度文字列（大小文字区別なし）

    Returns:
        正規化された Priority 値

    Raises:
        ValueError: 不正な優先度文字列の場合

    教育的ポイント:
    - Literal 型による制約の表現
    - バリデーション関数の分離
    - 型安全性の確保
    - プロジェクト一貫性の維持
    """
    normalized = value.lower()
    if normalized in ("high", "medium", "low"):
        return normalized  # type: ignore[return-value]

    raise ValueError(f"無効な優先度: {value}. 有効な値: high, medium, low")


@dataclass(frozen=True)
class TodoID:
    """Todo の一意識別子

    設計判断：
    - プリミティブ型（str）をラップして型安全性を向上
    - ドメインの概念を明示的に表現
    - frozen=True で不変性を保証

    教育的ポイント:
    - 値オブジェクトパターンの実装
    - 型安全性の向上手法
    - ドメイン概念の明示的表現
    """

    value: str

    @classmethod
    def generate(cls) -> "TodoID":
        """新しい TodoID を生成

        Returns:
            ランダムな UUID をベースとした新しい TodoID

        教育的ポイント:
        - ファクトリーメソッドパターン
        - UUID による一意性保証
        """
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        """文字列表現を返す

        Returns:
            TodoID の文字列表現
        """
        return self.value


@dataclass(frozen=True)
class Todo:
    """Todo エンティティ（イミュータブル）

    ドメイン設計原則：
    - 一意のID を持つ
    - イミュータブル（不変）
    - ビジネスルールをカプセル化
    - 状態変更は新しいインスタンス生成により表現

    教育的ポイント：
    - ドメインエンティティの不変性による利点
    - Repository で状態管理を隠蔽
    - 関数型プログラミング的アプローチ
    - dataclasses.replace() の活用
    """

    id: TodoID
    title: str
    description: str
    priority: Priority
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    def mark_completed(self) -> "Todo":
        """完了状態にした新しいインスタンスを返す

        Returns:
            完了状態の新しい Todo インスタンス

        ビジネスルール：
        - 既に完了済みの場合は自身を返す（変更なし）
        - 更新日時を自動更新

        教育的ポイント:
        - 不変オブジェクトの状態変更パターン
        - ビジネスルールの実装場所
        - 副作用のない設計
        """
        if self.is_completed:
            return self

        return dataclasses.replace(self, is_completed=True, updated_at=datetime.now())

    def mark_incomplete(self) -> "Todo":
        """未完了状態にした新しいインスタンスを返す

        Returns:
            未完了状態の新しい Todo インスタンス

        ビジネスルール：
        - 既に未完了の場合は自身を返す（変更なし）
        - 更新日時を自動更新

        教育的ポイント:
        - 状態変更の対称性
        - 重複ロジックの回避
        """
        if not self.is_completed:
            return self

        return dataclasses.replace(self, is_completed=False, updated_at=datetime.now())

    def update_content(self, title: str, description: str, priority: Priority) -> "Todo":
        """内容を更新した新しいインスタンスを返す

        Args:
            title: 新しいタイトル
            description: 新しい説明
            priority: 新しい優先度

        Returns:
            更新された新しい Todo インスタンス

        ビジネスルール：
        - 何も変更がない場合は自身を返す（変更なし）
        - 少なくとも1つの項目が変更された場合のみ更新日時を更新
        - タイトルの空白は自動でトリム

        教育的ポイント:
        - 複合的な状態変更の扱い
        - 効率性と不変性の両立
        - ビジネスルールの集約
        """
        title = title.strip()
        description = description.strip()

        # 変更の有無をチェック（効率性のため）
        if self.title == title and self.description == description and self.priority == priority:
            return self

        return dataclasses.replace(
            self, title=title, description=description, priority=priority, updated_at=datetime.now()
        )

    @property
    def is_high_priority(self) -> bool:
        """高優先度かどうかを判定

        Returns:
            高優先度の場合 True

        教育的ポイント:
        - ドメインロジックのプロパティ化
        - ビジネス概念の明示的表現
        """
        return self.priority == "high"


class TodoRepository(Protocol):
    """Todo リポジトリインターフェース

    Repository パターンの利点：
    - ドメインレイヤーをインフラから分離
    - テストでモック化が容易
    - 永続化方法を抽象化（メモリ・DB・ファイル等）

    注意：Protocol を使用することで、duck typing による
    インターフェース実装を可能にしています。

    教育的ポイント:
    - Repository パターンの設計思想
    - Protocol による型安全な duck typing
    - インターフェース分離の原則
    - ドメインレイヤーの独立性確保
    """

    def save(self, todo: Todo) -> Todo:
        """Todo を保存し、保存されたインスタンスを返す

        Args:
            todo: 保存する Todo エンティティ

        Returns:
            保存された Todo エンティティ（同一インスタンス）

        教育的ポイント:
        - 不変エンティティの保存パターン
        - Repository の責務範囲
        """
        ...

    def find_by_id(self, todo_id: TodoID) -> Todo | None:
        """ID で Todo を取得する

        Args:
            todo_id: 検索する TodoID

        Returns:
            見つかった Todo、存在しない場合は None

        教育的ポイント:
        - Optional の活用
        - 存在しない場合の適切な表現
        """
        ...

    def find_all(self) -> list[Todo]:
        """全ての Todo を取得する

        Returns:
            全 Todo のリスト（空の場合は空リスト）

        教育的ポイント:
        - コレクション操作の設計
        - 空コレクションの扱い
        """
        ...

    def find_by_completion_status(self, is_completed: bool) -> list[Todo]:
        """完了状態で Todo を検索する

        Args:
            is_completed: 検索する完了状態

        Returns:
            条件に合致する Todo のリスト

        教育的ポイント:
        - 条件検索の抽象化
        - ビジネス条件のリポジトリでの表現
        """
        ...

    def delete(self, todo_id: TodoID) -> bool:
        """Todo を削除する

        Args:
            todo_id: 削除する TodoID

        Returns:
            削除成功時は True、対象が存在しない場合は False

        教育的ポイント:
        - 削除操作の結果表現
        - bool による成功/失敗の表現
        """
        ...

    def delete_completed(self) -> int:
        """完了済み Todo を一括削除する

        Returns:
            削除した Todo の件数

        教育的ポイント:
        - 一括操作の設計
        - 操作結果の定量的表現
        """
        ...

    def count(self) -> int:
        """Todo の総数を取得する

        Returns:
            Todo の総数

        教育的ポイント:
        - 集約操作の抽象化
        - パフォーマンスを考慮した設計
        """
        ...

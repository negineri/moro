"""Configuration for Todo module.

設定レイヤー - 設定管理とDIコンテナへの登録

教育的ポイント:
- moro プロジェクトの設定管理パターン
- モジュール間の疎結合設計
- 公開インターフェースの設計
- 設定の階層化と管理
"""

from pydantic import BaseModel, Field


class TodoConfig(BaseModel):
    """Todo モジュール全体の設定

    ConfigRepository への登録用設定クラス。
    moro プロジェクトの設定管理パターンに準拠。

    設計判断:
    - 将来の設定拡張に対応した構造
    - 型安全性を保証した設定管理

    教育的ポイント:
    - 設定の階層化による管理性向上
    - Pydantic による型安全な設定
    - モジュールレベルでの設定統一
    - デフォルト値による設定の簡略化
    - Field による詳細なバリデーション
    - ビジネス制約の設定への反映
    """

    max_todos: int = Field(default=1000, ge=1, le=10000, description="最大 Todo 保存件数")
    auto_cleanup_days: int = Field(
        default=30, ge=1, le=365, description="完了済み Todo の自動削除日数"
    )
    default_priority: str = Field(
        default="medium", pattern="^(high|medium|low)$", description="デフォルト優先度"
    )

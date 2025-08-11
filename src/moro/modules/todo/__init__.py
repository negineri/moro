"""Todo サンプルモジュール

新しい開発者向けの教育的サンプルモジュール。
moro プロジェクトのレイヤードアーキテクチャとDDD原則を実践的に学習できる。

教育的目標:
- レイヤードアーキテクチャの実装パターン
- ドメイン駆動設計の基本概念
- 依存性注入の具体的活用方法
- イミュータブル設計の利点と実装方法
- テスト駆動開発の実践手法
"""

# 公開インターフェース
from .config import TodoConfig
from .domain import Priority, Todo, TodoID, TodoRepository, validate_priority
from .infrastructure import InMemoryTodoRepository
from .usecases import (
    CreateTodoRequest,
    CreateTodoUseCase,
    DeleteTodoUseCase,
    ListTodosUseCase,
    TodoResponse,
    ToggleTodoUseCase,
    UpdateTodoRequest,
    UpdateTodoUseCase,
)

__all__ = [
    "CreateTodoRequest",
    "CreateTodoUseCase",
    "DeleteTodoUseCase",
    "InMemoryTodoRepository",
    "ListTodosUseCase",
    "Priority",
    "Todo",
    "TodoConfig",
    "TodoID",
    "TodoRepository",
    "TodoResponse",
    "ToggleTodoUseCase",
    "UpdateTodoRequest",
    "UpdateTodoUseCase",
    "validate_priority",
]

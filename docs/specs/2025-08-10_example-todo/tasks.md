# Implementation Tasks: Todo サンプルモジュール

## 実装概要

Todo サンプルモジュールの段階的実装計画。新しい開発者が moro プロジェクトのアーキテクチャパターンを学習できるよう、教育的観点を重視した実装順序で進める。

## Phase 3a: コア実装（高優先度）

### Task 3a-1: Domain Layer 実装

**期間**: 1-2日
**責務**: ビジネスロジックとドメインモデルの実装

#### 実装項目

- [ ] **Priority 型定義とバリデーション関数**

  ```python
  # src/moro/modules/todo/domain.py
  from typing import Literal

  Priority = Literal["high", "medium", "low"]

  def validate_priority(value: str) -> Priority:
      # 実装詳細は design.md を参照
  ```

- [ ] **TodoID 値オブジェクト**

  ```python
  @dataclass(frozen=True)
  class TodoID:
      value: str

      @classmethod
      def generate(cls) -> "TodoID":
          return cls(str(uuid.uuid4()))
  ```

- [ ] **Todo エンティティ（イミュータブル）**

  ```python
  @dataclass(frozen=True)
  class Todo:
      # 完全なイミュータブル設計
      # dataclasses.replace() による状態変更
  ```

- [ ] **TodoRepository インターフェース（Protocol）**
  ```python
  class TodoRepository(Protocol):
      def save(self, todo: Todo) -> Todo
      # その他のメソッド定義
  ```

#### 品質基準

- [ ] MyPy の型チェックをパス
- [ ] Ruff の lint チェックをパス
- [ ] 教育的コメントの充実
- [ ] 設計意図の文書化

#### 教育的ポイント

- Literal 型による制約表現
- 不変エンティティの設計パターン
- Protocol による duck typing
- 値オブジェクトの実装方法

---

### Task 3a-2: Infrastructure Layer 実装

**期間**: 1-2日
**責務**: データアクセスと外部システム統合

#### 実装項目

- [ ] **TodoConfig 設定クラス**

  ```python
  class TodoConfig(BaseModel):
      max_todos: int = Field(default=1000, ge=1, le=10000)
      auto_cleanup_days: int = Field(default=30, ge=1, le=365)
      default_priority: str = Field(default="medium", pattern="^(high|medium|low)$")
  ```

- [ ] **InMemoryTodoRepository 実装**
  ```python
  class InMemoryTodoRepository:
      def __init__(self, config: TodoConfig) -> None:
          self._todos: Dict[str, Todo] = {}
          self._config = config

      def save(self, todo: Todo) -> Todo:
          # イミュータブルエンティティをそのまま保存
          # 最大件数チェック等の実装
  ```

#### 品質基準

- [ ] Pydantic バリデーションの動作確認
- [ ] メモリ効率の最適化
- [ ] エラーハンドリングの実装
- [ ] テスト用メソッド（clear）の実装

#### 教育的ポイント

- Pydantic による設定管理
- Repository パターンの具体実装
- メモリ内データ構造の設計
- 設定値によるビジネスルール制御

---

### Task 3a-3: 基本ユースケース実装

**期間**: 2-3日
**責務**: アプリケーションサービスとビジネスルールの実行

#### 実装項目

- [ ] **リクエスト・レスポンスオブジェクト**

  ```python
  @dataclass
  class CreateTodoRequest:
      title: str
      description: str = ""
      priority: str = "medium"

  @dataclass
  class TodoResponse:
      # ドメインオブジェクトからの変換メソッド付き
  ```

- [ ] **CreateTodoUseCase**

  ```python
  class CreateTodoUseCase:
      def __init__(self, repository: TodoRepository) -> None:
          self._repository = repository

      def execute(self, request: CreateTodoRequest) -> TodoResponse:
          # バリデーション → ドメイン生成 → 永続化
  ```

- [ ] **ListTodosUseCase**

  ```python
  class ListTodosUseCase:
      def execute(self, completed_only: Optional[bool] = None,
                 sort_by_priority: bool = False) -> List[TodoResponse]:
          # データ取得 → フィルタ → ソート
  ```

- [ ] **UpdateTodoUseCase** / **ToggleTodoUseCase**
  ```python
  # イミュータブルパターンによる状態更新
  updated_todo = todo.update_content(title, description, priority)
  saved_todo = self._repository.save(updated_todo)
  ```

#### 品質基準

- [ ] バリデーションロジックの実装
- [ ] エラーメッセージの国際化対応
- [ ] ビジネスルールの適切なカプセル化
- [ ] イミュータブルパターンの徹底

#### 教育的ポイント

- ユースケースの責務分離
- リクエスト・レスポンスパターン
- バリデーション戦略
- エラーハンドリングの統一

---

## Phase 3b: 統合実装（中優先度）

### Task 3b-1: Configuration Layer 実装

**期間**: 1日
**責務**: DI設定と ConfigRepository 連携

#### 実装項目

- [ ] **config.py の実装**

  ```python
  class TodoModuleConfig(BaseModel):
      todo: TodoConfig = TodoConfig()
  ```

- [ ] **既存 ConfigRepository への登録**

  ```python
  # src/moro/config/repository.py に TodoModuleConfig を追加
  ```

- [ ] ****init**.py での公開設定**
  ```python
  from .domain import Todo, TodoID, Priority, validate_priority
  from .usecases import CreateTodoUseCase, ListTodosUseCase
  from .config import TodoModuleConfig
  ```

#### 品質基準

- [ ] 既存設定システムとの統合確認
- [ ] 設定値のデフォルト動作確認
- [ ] 型安全性の保証

#### 教育的ポイント

- moro プロジェクトの設定管理パターン
- モジュール間の疎結合設計
- 公開インターフェースの設計

---

### Task 3b-2: CLI Layer 実装

**期間**: 2-3日
**責務**: Click コマンドの実装と DI 統合

#### 実装項目

- [ ] **todo CLI コマンド群**

  ```python
  # src/moro/cli/todo.py
  import click
  from injector import inject

  @click.group()
  def todo():
      """Todo 管理コマンド"""
      pass

  @todo.command()
  @click.argument('title')
  @click.option('--description', '-d', default="")
  @click.option('--priority', '-p', default="medium")
  @inject
  def add(title: str, description: str, priority: str,
          create_usecase: CreateTodoUseCase):
      """Todo を追加"""
      # 実装詳細
  ```

- [ ] **DI コンテナ設定**

  ```python
  # src/moro/dependencies/ に Todo モジュール用の設定追加
  def configure_todo_module(binder: Binder) -> None:
      binder.bind(TodoRepository, to=InMemoryTodoRepository, scope=singleton)
  ```

- [ ] **メイン CLI への統合**

  ```python
  # src/moro/cli.py
  from .cli.todo import todo

  cli.add_command(todo)
  ```

#### 実装するコマンド

- [ ] `moro todo add "タイトル" --description="説明" --priority=high`
- [ ] `moro todo list --completed --sort-by-priority`
- [ ] `moro todo update <id> --title="新タイトル"`
- [ ] `moro todo toggle <id>`
- [ ] `moro todo delete <id>`
- [ ] `moro todo cleanup` (完了済み削除)

#### 品質基準

- [ ] Click の引数バリデーション
- [ ] エラーメッセージのユーザビリティ
- [ ] ヘルプメッセージの充実
- [ ] DI による依存関係の自動解決

#### 教育的ポイント

- Click による CLI 設計
- Injector による DI パターン
- コマンドラインインターフェースの設計
- エラーハンドリングとユーザビリティ

---

## Phase 3c: 品質保証（中優先度）

### Task 3c-1: テストスイート実装

**期間**: 3-4日
**責務**: 包括的テスト戦略の実装

#### 実装項目

- [ ] **Domain Layer テスト**

  ```python
  # tests/modules/todo/test_domain.py
  class TestTodo:
      def test_todo_creation(self):
          # イミュータブル特性のテスト

      def test_mark_completed_immutable(self):
          # 状態変更時の不変性確認

      def test_update_content_returns_new_instance(self):
          # 更新時の新インスタンス生成確認

  class TestPriority:
      def test_validate_priority_success(self):
      def test_validate_priority_case_insensitive(self):
      def test_validate_priority_invalid_raises_error(self):
  ```

- [ ] **Infrastructure Layer テスト**

  ```python
  # tests/modules/todo/test_infrastructure.py
  class TestInMemoryTodoRepository:
      def test_save_and_find_by_id(self):
      def test_save_max_todos_limit(self):
      def test_delete_returns_boolean(self):
      def test_find_by_completion_status(self):

  class TestTodoConfig:
      def test_pydantic_validation(self):
      def test_default_values(self):
  ```

- [ ] **Use Cases テスト**

  ```python
  # tests/modules/todo/test_usecases.py
  class TestCreateTodoUseCase:
      def test_create_todo_success(self):
      def test_create_todo_validation_error(self):
      def test_create_todo_max_limit_error(self):

  class TestUpdateTodoUseCase:
      def test_update_todo_success(self):
      def test_update_todo_not_found(self):
      def test_update_todo_immutable_pattern(self):
  ```

- [ ] **CLI テスト**
  ```python
  # tests/cli/test_todo.py
  class TestTodoCLI:
      def test_add_command(self):
      def test_list_command_with_filters(self):
      def test_toggle_command(self):
      def test_error_handling(self):
  ```

#### 品質基準

- [ ] テストカバレッジ 90% 以上
- [ ] 各レイヤーの独立したテスト
- [ ] モックを使用した統合テスト
- [ ] エラーケースの網羅的テスト

#### 教育的ポイント

- 各レイヤーのテスト戦略
- モックオブジェクトの使用方法
- pytest の高度な使用方法
- TDD サイクルの実践例

---

### Task 3c-2: ドキュメント整備

**期間**: 1-2日
**責務**: 教育的ドキュメントの充実

#### 実装項目

- [ ] **モジュール内 README.md**

  ```markdown
  # Todo サンプルモジュール

  ## 概要

  新しい開発者向けの教育的サンプルモジュール

  ## アーキテクチャ学習ポイント

  - レイヤードアーキテクチャの実装
  - DDD の基本概念
  - イミュータブルエンティティパターン

  ## 使用方法

  moro todo add "タスク" --priority=high
  ```

- [ ] **設計判断の記録**

  ```markdown
  # 設計判断記録 (ADR)

  ## ADR-001: Priority を Literal 型で実装

  **決定**: Enum ではなく Literal 型を採用
  **理由**: プロジェクト一貫性、教育的価値

  ## ADR-002: イミュータブルエンティティの採用

  **決定**: frozen=True による不変エンティティ
  **理由**: 関数型的アプローチ、スレッドセーフ性
  ```

- [ ] **チュートリアル**

  ```markdown
  # Todo モジュールで学ぶ moro アーキテクチャ

  ## Step 1: ドメインモデルの理解

  ## Step 2: Repository パターンの実装

  ## Step 3: ユースケースの設計

  ## Step 4: CLI インターフェースの統合
  ```

#### 品質基準

- [ ] 新規開発者が理解できる説明レベル
- [ ] 実行可能なサンプルコードの提供
- [ ] 設計原則の明確な説明
- [ ] トラブルシューティングガイド

#### 教育的ポイント

- 技術文書の書き方
- アーキテクチャ図の作成方法
- 設計判断の記録方法
- チュートリアル作成の手法

---

## 実装スケジュール

### Week 1: 基盤構築

- **Day 1-2**: Domain Layer 実装
- **Day 3-4**: Infrastructure Layer 実装
- **Day 5-7**: 基本ユースケース実装

### Week 2: 統合・インターフェース

- **Day 8**: Configuration Layer 実装
- **Day 9-11**: CLI Layer 実装
- **Day 12-14**: DI 統合とデバッグ

### Week 3: 品質保証・ドキュメント

- **Day 15-18**: テストスイート実装
- **Day 19-20**: ドキュメント整備
- **Day 21**: 最終レビューと調整

## 品質チェックポイント

### 各 Phase 完了時

- [ ] `uv run ruff check` でエラーなし
- [ ] `uv run mypy` で型チェック合格
- [ ] `uv run pytest --cov=src --cov-report=term-missing` でカバレッジ確認
- [ ] 既存機能への影響なし確認

### 最終完了基準

- [ ] 新規開発者が 1 時間以内に理解可能
- [ ] 全てのコマンドが正常動作
- [ ] テストカバレッジ 90% 以上
- [ ] ドキュメントの完全性
- [ ] 既存 fantia モジュールとの一貫性

## リスク管理

### 技術的リスク

- **複雑性増大**: 段階的実装とレビューで軽減
- **既存システム影響**: 独立性の確保と統合テスト
- **パフォーマンス**: メモリ使用量の監視

### 教育的リスク

- **学習コスト**: 適切なコメントと文書化
- **理解困難**: 段階的な複雑さの導入
- **保守負荷**: 自動テストによる品質保証

## 完了後の活用方法

### 新規開発者オンボーディング

1. Todo モジュールコードリーディング（1時間）
2. 新機能追加演習（2-3時間）
3. 類似モジュール作成演習（1日）

### プロジェクト品質向上

1. 設計パターンの標準化
2. テスト戦略の統一
3. ドキュメント作成手法の共有

### 継続的改善

- 新しいアーキテクチャパターンの実験場
- パフォーマンス最適化の検証
- 教育効果の測定と改善

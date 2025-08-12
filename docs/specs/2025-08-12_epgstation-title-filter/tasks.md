# EPGStation タイトルフィルター機能 - 実装タスク

## 実装戦略

### TDD（Test-Driven Development）強制適用

すべての実装で以下のサイクルを厳格に適用：

1. **Red**: 失敗するテストを書く
2. **Green**: テストを通す最小限のコードを実装
3. **Refactor**: コードを改善・整理

### 品質保証チェックポイント

各Phase完了時に以下を自動実行：

- [ ] `uv run pytest --cov=src --cov-report=term-missing`
- [ ] `uv run ruff check`
- [ ] `uv run mypy`
- [ ] パフォーマンステスト（1000件データで1秒以内）

## Phase A: ドメインサービス実装 (1-2日)

### Task A1: TitleFilterService の TDD実装

**所要時間**: 4-6時間

#### A1.1: テストファースト実装 (Red)

```python
# tests/modules/epgstation/test_title_filter_service.py
def test_apply_filter_with_no_filter_returns_all():
    """フィルター条件なしの場合、全データを返却"""
    # 失敗するテストから開始

def test_apply_filter_case_insensitive_basic():
    """大文字・小文字非区別の基本フィルタリング"""
    # 失敗するテストから開始

def test_apply_filter_regex_mode():
    """正規表現モードでのフィルタリング"""
    # 失敗するテストから開始
```

**チェックポイント**: テストが適切に失敗することを確認

#### A1.2: 最小実装 (Green)

```python
# src/moro/modules/epgstation/domain.py に追加
class TitleFilterService:
    """番組タイトルフィルタリングサービス"""

    def apply_filter(
        self,
        recordings: list[RecordingData],
        title_filter: str | None = None,
        regex: bool = False
    ) -> list[RecordingData]:
        # テストを通すだけの最小実装から開始
        pass
```

**チェックポイント**: 全テストが通ることを確認

#### A1.3: リファクタリング (Refactor)

- メソッド分割
- エラーハンドリング追加
- パフォーマンス最適化

**成果物**:

- [ ] `TitleFilterService` クラス実装完了
- [ ] 基本テスト8ケース以上でカバレッジ100%
- [ ] 正規表現DoS対策実装済み

### Task A2: エラーハンドリング強化

**所要時間**: 2-3時間

#### A2.1: カスタム例外クラス定義

```python
# src/moro/modules/epgstation/domain.py に追加
class FilterError(Exception):
    """フィルター処理エラー基底クラス"""
    pass

class RegexPatternError(FilterError):
    """正規表現パターンエラー"""
    pass
```

#### A2.2: ReDoS（正規表現DoS）対策

```python
def _compile_regex_safely(self, pattern: str) -> Pattern[str]:
    """安全な正規表現コンパイル（ReDoS対策）"""
    # 実装前にテストを作成
```

**成果物**:

- [ ] エラーハンドリングテスト5ケース以上
- [ ] 危険パターン検出機能実装
- [ ] 適切なエラーメッセージ提供

## Phase B: UseCase層統合 (1日)

### Task B1: ListRecordingsUseCase 修正

**所要時間**: 3-4時間

#### B1.1: 依存性注入設定 (Red → Green)

```python
# tests/modules/epgstation/test_list_recordings_usecase.py
def test_execute_with_title_filter():
    """タイトルフィルター付きの実行テスト"""
    # モック使用のテスト作成

def test_execute_with_regex_filter():
    """正規表現フィルター付きの実行テスト"""
    # モック使用のテスト作成
```

#### B1.2: UseCase実装修正

```python
# src/moro/modules/epgstation/usecases.py 修正
@inject
class ListRecordingsUseCase:
    def __init__(
        self,
        recording_repository: "RecordingRepository",
        title_filter_service: "TitleFilterService"  # 新規追加
    ) -> None:
        self._repository = recording_repository
        self._filter_service = title_filter_service  # 新規追加

    def execute(
        self,
        limit: int = 100,
        title_filter: str | None = None,  # 新規追加
        regex: bool = False  # 新規追加
    ) -> list[RecordingData]:
        # 実装修正
```

#### B1.3: 依存性注入コンテナ更新

```python
# src/moro/dependencies/container.py 修正
# TitleFilterService を DI コンテナに登録
```

**成果物**:

- [ ] UseCase修正完了
- [ ] DI設定更新完了
- [ ] 統合テスト5ケース以上作成

## Phase C: CLI層統合 (1日)

### Task C1: CLI オプション拡張

**所要時間**: 3-4時間

#### C1.1: CLIテスト作成 (Red)

```python
# tests/cli/test_epgstation_title_filter.py
def test_list_with_title_filter():
    """--title オプションのテスト"""

def test_list_with_regex_filter():
    """--regex オプションのテスト"""

def test_list_with_invalid_regex():
    """無効正規表現のエラーハンドリングテスト"""
```

#### C1.2: CLI実装修正 (Green)

```python
# src/moro/cli/epgstation.py 修正
@epgstation.command(name="list")
@click.option("--limit", default=100, type=int, help="表示する録画数の上限（デフォルト: 100）")
@click.option("--format", "format_type", type=click.Choice(["table", "json"]), default="table", help="出力形式（デフォルト: table）")
@click.option("--title", help="番組タイトルでフィルタリング")  # 新規追加
@click.option("--regex/--no-regex", default=False, help="正規表現モード")  # 新規追加
@click_verbose_option
def list_recordings(
    limit: int,
    format_type: str,
    verbose: tuple[bool],
    title: str | None = None,  # 新規追加
    regex: bool = False  # 新規追加
) -> None:
    # 実装修正
```

**成果物**:

- [ ] CLI拡張完了
- [ ] ヘルプメッセージ更新
- [ ] CLIテスト3ケース以上作成

### Task C2: E2E テスト作成

**所要時間**: 2-3時間

#### C2.1: 統合テストスイート

```python
# tests/cli/test_epgstation_integration_filter.py
def test_end_to_end_title_filtering():
    """エンドツーエンドのタイトルフィルタリングテスト"""

def test_performance_with_large_dataset():
    """大量データでのパフォーマンステスト"""
```

**成果物**:

- [ ] E2Eテスト実装完了
- [ ] パフォーマンス検証完了
- [ ] 全機能結合テスト完了

## Phase D: 品質向上・最適化 (1-2日)

### Task D1: パフォーマンス最適化

**所要時間**: 2-3時間

#### D1.1: ベンチマークテスト作成

```python
def test_filter_performance_1000_records():
    """1000件データの1秒以内処理を検証"""

def test_memory_usage_optimization():
    """メモリ使用量の最適化検証"""
```

#### D1.2: 最適化実装

- 文字列検索の最適化
- 正規表現コンパイルの効率化
- メモリ使用量の削減

**成果物**:

- [ ] 1000件データを1秒以内で処理
- [ ] メモリ使用量20%以内増加
- [ ] ベンチマークテスト作成

### Task D2: ドキュメント・品質保証

**所要時間**: 2-3時間

#### D2.1: 使用例ドキュメント作成

```markdown
# EPGStation タイトルフィルター使用例

## 基本的な使用方法

moro epgstation list --title "ニュース"

## 正規表現モード

moro epgstation list --title "^ニュース.\*" --regex

## 他オプションとの併用

moro epgstation list --title "ドラマ" --limit 50 --format json
```

#### D2.2: 最終品質チェック

- [ ] 全テスト通過（カバレッジ90%以上）
- [ ] リント・タイプチェック通過
- [ ] パフォーマンス要件達成
- [ ] セキュリティ要件達成
- [ ] ドキュメント整備完了

**成果物**:

- [ ] README更新
- [ ] 使用例ドキュメント作成
- [ ] 最終品質チェック完了

## 自動品質保証プロセス

各Phase完了時に以下を自動実行：

### コード品質チェック

```bash
# 自動実行コマンド
uv run ruff check src/moro/modules/epgstation/
uv run mypy src/moro/modules/epgstation/
uv run pytest tests/modules/epgstation/test_*title_filter* -v
```

### パフォーマンス検証

```bash
# 1000件データでのベンチマーク
uv run pytest tests/modules/epgstation/test_performance_title_filter.py -v
```

### セキュリティ検証

```bash
# ReDoS対策の検証
uv run pytest tests/modules/epgstation/test_regex_security.py -v
```

## リスク管理

### 高リスク項目と対策

1. **正規表現パフォーマンス**
   - **対策**: 危険パターン検出・タイムアウト実装
   - **検証**: 専用テストケース作成

2. **大量データ処理**
   - **対策**: ベンチマークテストによる継続監視
   - **検証**: 1000件データで1秒以内の検証

3. **既存機能への影響**
   - **対策**: 既存テストの継続実行
   - **検証**: リグレッションテストの実行

### 完了基準

すべてのPhaseで以下を満たした場合に完了：

- [ ] 全テストが通過（カバレッジ90%以上）
- [ ] `uv run ruff check` がエラー0
- [ ] `uv run mypy` がエラー0
- [ ] パフォーマンス要件達成
- [ ] 受け入れ基準100%達成
- [ ] ドキュメント整備完了

この実装計画で開始しますか？

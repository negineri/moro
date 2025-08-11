# EPGStation 責務分離 - 実装タスク

**仕様書バージョン**: 1.0
**作成日**: 2025-08-11
**実装期間**: 7日間（2025-08-11 ～ 2025-08-18）
**優先度**: Critical

## 実装概要

Clean Architecture 原則に基づき、ユースケース層とプレゼンテーション層の責務分離を3段階で実装。既存機能の非劣化を保証しつつ、Table と JSON の複数出力形式に対応する。

## 実装戦略

### TDD サイクル適用

全ての実装で**Red-Green-Refactor**サイクルを厳格に適用：

1. **Red**: 失敗するテストを最初に記述
2. **Green**: テストを通す最小限の実装
3. **Refactor**: 品質を向上させる改善

### 品質ファースト原則

- **各タスク完了時**: 必須品質チェック実行
- **段階完了時**: 統合品質検証実行
- **最終完了時**: 全品質基準達成確認

## 段階1: 基礎リファクタリング（Day 1-2）

### タスク1.1: ユースケース層純化

**優先度**: Critical
**工数**: 2時間
**担当**: 実装者

#### 実装内容

**ファイル**: `src/moro/modules/epgstation/usecases.py`

```python
# 改修前（現在）
def execute(self, limit: int = 100) -> str:
    """録画一覧を取得してテーブル形式で返す"""
    try:
        recordings = self._repository.get_all(limit=limit)
        return self._format_table(recordings)  # ❌ プレゼンテーション混在
    except Exception as e:
        logger.error(f"Failed to get recordings: {e}")
        return f"エラー: 録画一覧の取得に失敗しました ({e})"

# 改修後（目標）
def execute(self, limit: int = 100) -> List[RecordingData]:
    """録画一覧を取得（純粋ビジネスロジック）"""
    try:
        return self._repository.get_all(limit=limit)
    except Exception as e:
        logger.error(f"Failed to get recordings: {e}")
        raise  # プレゼンテーション層に委譲
```

#### 実装手順

1. **Red: テストファースト実装**

   ```bash
   # テストファイル作成
   touch tests/modules/epgstation/test_usecases_refactored.py
   ```

   ```python
   # 失敗するテストを先に実装
   def test_list_recordings_returns_domain_objects():
       # Given
       mock_repo = Mock(spec=RecordingRepository)
       expected_recordings = [
           RecordingData(id=1, name="test", start_at=1000, end_at=2000,
                        video_files=[], is_recording=False, is_protected=False)
       ]
       mock_repo.get_all.return_value = expected_recordings

       use_case = ListRecordingsUseCase(mock_repo)

       # When
       result = use_case.execute(limit=50)

       # Then
       assert isinstance(result, list)
       assert len(result) == 1
       assert result[0].id == 1
       assert result[0].name == "test"
       mock_repo.get_all.assert_called_once_with(limit=50)
   ```

2. **Green: 最小実装**

   ```python
   # usecases.py の execute メソッドを最小限修正
   def execute(self, limit: int = 100) -> List[RecordingData]:
       return self._repository.get_all(limit=limit)
   ```

3. **Refactor: エラーハンドリング追加**
   ```python
   def execute(self, limit: int = 100) -> List[RecordingData]:
       try:
           return self._repository.get_all(limit=limit)
       except Exception as e:
           logger.error(f"Failed to get recordings: {e}")
           raise
   ```

#### 完了基準

- [ ] `ListRecordingsUseCase.execute()` が `List[RecordingData]` を返却
- [ ] プレゼンテーション処理コードの完全除去（`_format_table`, `_create_table`, `_truncate_text`）
- [ ] ユニットテスト実装・全テスト通過
- [ ] MyPy 厳格モード通過
- [ ] 行数: 35行 → 15行以下

---

### タスク1.2: TableFormatter 分離実装

**優先度**: Critical
**工数**: 3時間
**担当**: 実装者

#### 実装内容

**ファイル**: `src/moro/cli/epgstation.py`（プレゼンテーション層追加）

```python
# 新規追加: Strategy Pattern 実装
from abc import ABC, abstractmethod
from typing import List

class OutputFormatter(ABC):
    """出力フォーマットの抽象基底クラス"""

    @abstractmethod
    def format(self, recordings: List[RecordingData]) -> str:
        """録画データを指定形式でフォーマット"""

    @abstractmethod
    def format_empty_message(self) -> str:
        """データが空の場合のメッセージ"""

class TableFormatter(OutputFormatter):
    """テーブル形式フォーマッター"""

    def format(self, recordings: List[RecordingData]) -> str:
        if not recordings:
            return self.format_empty_message()

        # 既存の _format_table ロジックを移植
        headers = ["録画ID", "タイトル", "開始時刻", "ファイル名", "種別", "サイズ"]
        rows = []

        for recording in recordings:
            if not recording.video_files:
                rows.append([
                    str(recording.id),
                    self._truncate_text(recording.name, 40),
                    recording.formatted_start_time,
                    "N/A", "N/A", "N/A",
                ])
            else:
                for video_file in recording.video_files:
                    rows.append([
                        str(recording.id),
                        self._truncate_text(recording.name, 40),
                        recording.formatted_start_time,
                        video_file.filename or video_file.name,
                        video_file.type.upper(),
                        video_file.formatted_size,
                    ])

        return self._create_table(headers, rows)

    def format_empty_message(self) -> str:
        return "録画データが見つかりませんでした。"

    # 既存メソッドをそのまま移植
    def _truncate_text(self, text: str, max_length: int) -> str:
        # 既存実装をコピー
        pass

    def _create_table(self, headers: List[str], rows: List[List[str]]) -> str:
        # 既存実装をコピー
        pass
```

#### 実装手順

1. **Red: フォーマッターテスト実装**

   ```python
   def test_table_formatter_formats_recordings():
       # Given
       recordings = [create_test_recording()]
       formatter = TableFormatter()

       # When
       result = formatter.format(recordings)

       # Then
       assert "録画ID" in result
       assert "│" in result  # テーブル区切り文字
       assert str(recordings[0].id) in result
   ```

2. **Green: 抽象クラス・基本実装**

   ```python
   # OutputFormatter, TableFormatter の基本構造実装
   ```

3. **Refactor: 既存ロジック完全移植**
   ```python
   # usecases.py から全テーブル処理ロジックを移植
   ```

#### 完了基準

- [ ] `OutputFormatter` 抽象クラス実装
- [ ] `TableFormatter` 完全実装（既存出力と同一）
- [ ] 独立ユニットテスト実装・全テスト通過
- [ ] 既存出力との完全互換性確認
- [ ] コードカバレッジ > 90%

---

### タスク1.3: CLI統合（Table のみ）

**優先度**: Critical
**工数**: 1時間
**担当**: 実装者

#### 実装内容

**ファイル**: `src/moro/cli/epgstation.py`（修正）

```python
# 改修後の list_recordings コマンド
@epgstation.command(name="list")
@click.option("--limit", default=100, type=int,
              help="表示する録画数の上限（デフォルト: 100）")
@click_verbose_option
def list_recordings(limit: int, verbose: tuple[bool]) -> None:
    """録画一覧を表示"""
    config = ConfigRepository.create()
    config_logging(config, verbose)

    try:
        # 依存注入でユースケース取得
        injector = create_injector(config)
        use_case = injector.get(ListRecordingsUseCase)

        # ビジネスロジック実行
        recordings = use_case.execute(limit=limit)

        # プレゼンテーション処理（Tableのみ）
        formatter = TableFormatter()
        result = formatter.format(recordings)

        click.echo(result)

    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        raise click.ClickException(str(e)) from e
```

#### 実装手順

1. **Red: CLI統合テスト**

   ```python
   def test_cli_list_command_table_output():
       # Given: モックされたユースケース
       with patch('moro.cli.epgstation.ListRecordingsUseCase') as mock_uc:
           mock_uc.return_value.execute.return_value = [test_recording]

           # When: CLIコマンド実行
           result = runner.invoke(list_recordings, ['--limit', '10'])

           # Then: テーブル形式出力
           assert result.exit_code == 0
           assert "録画ID" in result.output
   ```

2. **Green: 基本統合実装**

3. **Refactor: エラーハンドリング強化**

#### 完了基準

- [ ] CLI コマンドが新しいアーキテクチャで動作
- [ ] 既存の `--limit`, `--verbose` オプション完全動作
- [ ] 既存出力形式の完全維持
- [ ] E2E テスト通過
- [ ] 後方互換性100%確保

---

## 段階2: JSON機能追加（Day 3-4）

### タスク2.1: JsonFormatter 実装

**優先度**: High
**工数**: 2時間
**担当**: 実装者

#### 実装内容

**ファイル**: `src/moro/cli/epgstation.py`（追加）

```python
class JsonFormatter(OutputFormatter):
    """JSON形式フォーマッター（堅牢性重視）"""

    def format(self, recordings: List[RecordingData]) -> str:
        if not recordings:
            return self.format_empty_message()

        try:
            # Pydantic model_dump() を使用
            data = [recording.model_dump() for recording in recordings]
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"JSON serialization failed: {e}")

            # フォールバック: 基本情報のみのJSON
            fallback_data = []
            for recording in recordings:
                try:
                    fallback_data.append({
                        "id": recording.id,
                        "name": recording.name,
                        "start_time": recording.formatted_start_time,
                        "duration_minutes": recording.duration_minutes,
                        "error": "詳細情報の取得に失敗"
                    })
                except Exception:
                    fallback_data.append({
                        "error": "データ取得エラー",
                        "id": getattr(recording, 'id', 'unknown')
                    })

            return json.dumps(fallback_data, ensure_ascii=False, indent=2)

    def format_empty_message(self) -> str:
        return json.dumps({
            "recordings": [],
            "message": "録画データが見つかりませんでした。"
        }, ensure_ascii=False, indent=2)
```

#### 実装手順

1. **Red: JSON フォーマッターテスト**

   ```python
   def test_json_formatter_produces_valid_json():
       # Given
       recordings = [create_test_recording()]
       formatter = JsonFormatter()

       # When
       result = formatter.format(recordings)

       # Then
       import json
       parsed = json.loads(result)  # JSON妥当性検証
       assert isinstance(parsed, list)
       assert len(parsed) == 1
       assert parsed[0]['id'] == recordings[0].id

   def test_json_formatter_handles_serialization_error():
       # Given: 問題のあるデータ
       # When: フォーマット実行
       # Then: フォールバック動作確認
       pass
   ```

2. **Green: 基本JSON出力実装**

3. **Refactor: フォールバック機能追加**

#### 完了基準

- [ ] `JsonFormatter` 完全実装
- [ ] 正常なJSON出力確認（`json.loads()` で検証）
- [ ] フォールバック機能動作確認
- [ ] 日本語文字列の適切な処理確認
- [ ] エラーケース網羅テスト通過

---

### タスク2.2: CLI フォーマット選択機能

**優先度**: High
**工数**: 2時間
**担当**: 実装者

#### 実装内容

**ファイル**: `src/moro/cli/epgstation.py`（修正）

```python
@epgstation.command(name="list")
@click.option("--limit", default=100, type=int,
              help="表示する録画数の上限（デフォルト: 100）")
@click.option("--format", "format_type",
              type=click.Choice(['table', 'json']),
              default='table',
              help="出力形式（デフォルト: table）")
@click_verbose_option
def list_recordings(limit: int, format_type: str, verbose: tuple[bool]) -> None:
    """録画一覧を表示"""
    config = ConfigRepository.create()
    config_logging(config, verbose)

    try:
        # 依存注入でユースケース取得
        injector = create_injector(config)
        use_case = injector.get(ListRecordingsUseCase)

        # ビジネスロジック実行
        recordings = use_case.execute(limit=limit)

        # プレゼンテーション処理（Strategy Pattern）
        formatter_map = {
            'table': TableFormatter(),
            'json': JsonFormatter()
        }
        formatter = formatter_map[format_type]

        # フォーマット・出力
        result = formatter.format(recordings)
        click.echo(result)

    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        raise click.ClickException(str(e)) from e
```

#### 実装手順

1. **Red: フォーマット選択テスト**

   ```python
   def test_cli_json_format_option():
       # Given
       with patch('moro.cli.epgstation.ListRecordingsUseCase') as mock_uc:
           mock_uc.return_value.execute.return_value = [test_recording]

           # When: JSON フォーマット指定
           result = runner.invoke(list_recordings, ['--format', 'json'])

           # Then: JSON 出力確認
           assert result.exit_code == 0
           import json
           parsed = json.loads(result.output)
           assert isinstance(parsed, list)

   def test_cli_invalid_format_option():
       # When: 無効なフォーマット指定
       result = runner.invoke(list_recordings, ['--format', 'xml'])

       # Then: エラーメッセージ確認
       assert result.exit_code != 0
       assert "Invalid value for '--format'" in result.output
   ```

2. **Green: オプション追加・基本動作**

3. **Refactor: エラーハンドリング・ログ強化**

#### 完了基準

- [ ] `--format table` 動作確認（既存と同一出力）
- [ ] `--format json` 動作確認（有効なJSON出力）
- [ ] デフォルト動作確認（`--format` 未指定時は table）
- [ ] 無効フォーマット指定時の適切なエラーメッセージ
- [ ] 全オプション組み合わせテスト通過

---

## 段階3: 品質向上・最適化（Day 5-7）

### タスク3.1: 包括的テストスイート

**優先度**: High
**工数**: 4時間
**担当**: 実装者

#### 実装内容

**テストファイル構成**:

```
tests/
├── modules/epgstation/
│   └── test_usecases_refactored.py      # ユースケース単体テスト
├── cli/
│   └── test_epgstation_integration.py   # CLI統合テスト
└── e2e/
    └── test_epgstation_e2e.py          # E2Eテスト
```

#### 3.1.1 ユニットテスト強化

```python
# tests/modules/epgstation/test_usecases_refactored.py
class TestListRecordingsUseCase:
    def test_execute_returns_recordings_from_repository(self):
        """正常系：リポジトリからの録画データ取得"""

    def test_execute_forwards_limit_parameter(self):
        """パラメータ転送：limit値がリポジトリに正しく渡される"""

    def test_execute_raises_exception_on_repository_failure(self):
        """異常系：リポジトリ例外の適切な委譲"""

    def test_execute_logs_errors_appropriately(self):
        """ログ出力：エラー時の適切なログレベル・メッセージ"""

# tests/cli/test_formatters.py
class TestTableFormatter:
    def test_format_single_recording_with_video_files(self):
        """単一録画（ビデオファイルあり）の正確なテーブル出力"""

    def test_format_recording_without_video_files(self):
        """ビデオファイルなし録画の N/A 表示確認"""

    def test_format_handles_long_titles(self):
        """長いタイトルの切り詰め動作確認"""

    def test_format_empty_message(self):
        """空データでの適切なメッセージ表示"""

class TestJsonFormatter:
    def test_format_produces_valid_json_structure(self):
        """有効なJSON構造の出力確認"""

    def test_format_includes_all_recording_fields(self):
        """全録画フィールドの完全出力確認"""

    def test_format_handles_japanese_characters(self):
        """日本語文字列の適切なエンコーディング"""

    def test_format_fallback_on_serialization_error(self):
        """シリアライゼーション失敗時のフォールバック動作"""
```

#### 3.1.2 統合テスト実装

```python
# tests/cli/test_epgstation_integration.py
class TestEPGStationCLIIntegration:
    def test_table_format_backward_compatibility(self):
        """既存CLIコマンドとの出力互換性確認"""

    def test_json_format_new_functionality(self):
        """JSON形式での新機能動作確認"""

    def test_error_handling_across_layers(self):
        """レイヤー間エラーハンドリングの統合確認"""

    def test_performance_within_acceptable_range(self):
        """パフォーマンス要件内での動作確認"""
```

#### 3.1.3 E2Eテスト実装

```python
# tests/e2e/test_epgstation_e2e.py
class TestEPGStationE2E:
    def test_full_table_output_workflow(self):
        """実際のEPGStation API → Table出力の完全フロー"""

    def test_full_json_output_workflow(self):
        """実際のEPGStation API → JSON出力の完全フロー"""

    def test_large_dataset_handling(self):
        """大量データでの安定動作確認"""
```

#### 完了基準

- [ ] **テストカバレッジ > 95%**（ユースケース、フォーマッター）
- [ ] **全テストケース通過**（ユニット・統合・E2E）
- [ ] **パフォーマンステスト通過**（100件データ < 60ms）
- [ ] **メモリリークテスト通過**（大量データ処理）
- [ ] **エラーケース網羅確認**（全異常系パターン）

---

### タスク3.2: パフォーマンス最適化

**優先度**: Medium
**工数**: 2時間
**担当**: 実装者

#### 実装内容

#### 3.2.1 メモリ使用量最適化

```python
# JsonFormatter の最適化
class JsonFormatter(OutputFormatter):
    def format(self, recordings: List[RecordingData]) -> str:
        if not recordings:
            return self.format_empty_message()

        # 最適化: ストリーミング JSON 生成（大量データ対応）
        if len(recordings) > 500:  # 閾値設定
            return self._stream_json(recordings)
        else:
            return self._standard_json(recordings)

    def _stream_json(self, recordings: List[RecordingData]) -> str:
        """大量データ向けストリーミング処理"""
        import io
        output = io.StringIO()
        output.write('[')

        for i, recording in enumerate(recordings):
            if i > 0:
                output.write(',')
            json.dump(recording.model_dump(), output, ensure_ascii=False)

        output.write(']')
        return output.getvalue()
```

#### 3.2.2 テーブル処理最適化

```python
# TableFormatter の最適化
class TableFormatter(OutputFormatter):
    def _create_table(self, headers: List[str], rows: List[List[str]]) -> str:
        # 最適化: 列幅計算の効率化
        col_widths = [len(h) for h in headers]

        # 一回のループで全行の幅計算（O(n) → O(1)改善）
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
```

#### 完了基準

- [ ] **メモリ使用量 < 上限**（1000件データで50MB以下）
- [ ] **レスポンス時間目標達成**（Table: 50ms, JSON: 40ms）
- [ ] **大量データ処理確認**（10,000件でのクラッシュ無し）
- [ ] **ベンチマークテスト通過**（改善前との比較）

---

### タスク3.3: 品質・セキュリティ最終チェック

**優先度**: High
**工数**: 1時間
**担当**: 実装者

#### 実装内容

#### 3.3.1 コード品質最終確認

```bash
# 全品質チェック実行
uv run ruff check src/moro/modules/epgstation/
uv run ruff check src/moro/cli/epgstation.py
uv run mypy --strict src/moro/modules/epgstation/
uv run mypy --strict src/moro/cli/epgstation.py
uv run pytest --cov=src --cov-report=term-missing tests/
```

#### 3.3.2 セキュリティ検証

```python
# セキュリティテスト
def test_json_output_prevents_xss():
    """JSON出力でのXSS対策確認"""
    recording = create_recording_with_script_tags()
    formatter = JsonFormatter()
    result = formatter.format([recording])

    # スクリプトタグが適切にエスケープされている確認
    assert "<script>" not in result
    assert "&lt;script&gt;" in result

def test_log_output_masks_sensitive_data():
    """ログ出力での機密データマスキング確認"""
    # APIキー等の機密情報がログに出力されない確認
    pass
```

#### 3.3.3 後方互換性最終確認

```python
def test_backward_compatibility_comprehensive():
    """既存機能の完全互換性確認"""
    # 既存のCLIスクリプトでの動作確認
    # 出力形式の完全一致確認
    # エラーメッセージの一致確認
    pass
```

#### 完了基準

- [ ] **Ruff**: 全チェックパス（警告0件）
- [ ] **MyPy**: 厳格モード全チェックパス（エラー0件）
- [ ] **セキュリティスキャン**: 脆弱性0件
- [ ] **後方互換性**: 100%確認
- [ ] **ドキュメント**: 更新完了

---

## 品質保証チェックリスト

### 段階別品質ゲート

#### 段階1完了時チェックリスト

- [ ] **ユースケース純化確認**
  - [ ] 戻り値が `List[RecordingData]`
  - [ ] プレゼンテーション処理コードの完全除去
  - [ ] ログ出力の適切性
- [ ] **TableFormatter 分離確認**
  - [ ] 既存出力との完全一致
  - [ ] 独立動作確認（ユースケースなしでの動作）
  - [ ] エッジケース処理（空データ、長いタイトル等）
- [ ] **CLI統合確認**
  - [ ] 既存コマンドの完全動作
  - [ ] エラーハンドリングの適切性
  - [ ] ログ出力の一貫性

#### 段階2完了時チェックリスト

- [ ] **JSON機能確認**
  - [ ] 有効なJSON出力（`json.loads()` で検証）
  - [ ] 全フィールドの完全出力
  - [ ] 日本語文字列の適切な処理
- [ ] **フォーマット選択確認**
  - [ ] `--format table` の完全動作
  - [ ] `--format json` の完全動作
  - [ ] デフォルト動作の維持
  - [ ] 無効フォーマットでの適切なエラー

#### 段階3（最終）完了時チェックリスト

- [ ] **テスト品質**
  - [ ] ユニットテストカバレッジ > 95%
  - [ ] 統合テスト全パス
  - [ ] E2Eテスト全パス
  - [ ] パフォーマンステスト全パス
- [ ] **コード品質**
  - [ ] Ruff チェック全パス
  - [ ] MyPy 厳格モード全パス
  - [ ] 循環的複雑度 < 10
  - [ ] メソッド行数 < 20
- [ ] **アーキテクチャ品質**
  - [ ] Clean Architecture 原則準拠
  - [ ] 依存関係方向の適切性
  - [ ] 単一責任原則の遵守
  - [ ] Strategy パターンの正しい実装

### 最終受け入れテスト

#### 機能受け入れ基準

```bash
# 1. 既存機能の完全動作
moro epgstation list
moro epgstation list --limit 10
moro epgstation list --verbose

# 2. 新機能の完全動作
moro epgstation list --format table
moro epgstation list --format json
moro epgstation list --format json --limit 5

# 3. エラーハンドリング
moro epgstation list --format xml  # 適切なエラーメッセージ
```

#### 性能受け入れ基準

- [ ] **レスポンス時間**: Table 50ms以下、JSON 40ms以下（100件データ）
- [ ] **メモリ使用量**: +4MB以下の増加（1000件データ）
- [ ] **CPU使用率**: 追加オーバーヘッド < 5%

#### セキュリティ受け入れ基準

- [ ] **データ保護**: 機密情報の適切なマスキング
- [ ] **入力検証**: 不正パラメーターでのクラッシュ無し
- [ ] **出力サニタイゼーション**: XSS脆弱性無し

---

## リスク管理・緊急対応

### 実装リスクと対策

#### Critical リスク（プロジェクト停止レベル）

**リスク**: 既存機能の破綻
**対策**:

- 段階1で既存動作の完全確認を必須とする
- 問題発生時の即座ロールバック体制
- 並行動作確認テストの実装

**リスク**: パフォーマンス大幅劣化
**対策**:

- 各段階でのベンチマークテスト必須実行
- 劣化検知時の最適化作業即座実施
- 大量データテストの事前実施

#### High リスク（機能制限レベル）

**リスク**: JSON シリアライゼーション失敗
**対策**:

- フォールバック機能の必須実装
- 異常データでの事前テスト強化
- エラー時のログ出力充実

**リスク**: メモリリーク発生
**対策**:

- 大量データでのメモリ監視テスト
- オブジェクト生成最小化の実装
- ガベージコレクション動作確認

### 緊急時対応手順

#### 段階1でのブロッカー発生時

1. **問題の即座切り分け**（5分以内）
2. **ロールバック判断**（15分以内）
3. **代替実装の検討**（30分以内）
4. **品質基準の一時的調整**（必要に応じて）

#### 段階2でのブロッカー発生時

1. **Table機能への影響評価**（10分以内）
2. **JSON機能の段階的無効化**（Feature Flag 利用）
3. **最小機能での段階3移行判断**
4. **追加工数の承認取得**

---

## 完了基準・成功指標

### 定量的成功指標

| 指標                       | 現在 | 目標 | 測定方法                          |
| -------------------------- | ---- | ---- | --------------------------------- |
| アーキテクチャ適合度       | 40%  | 95%  | Clean Architecture チェックリスト |
| テストカバレッジ           | 困難 | 95%  | pytest-cov                        |
| レスポンス時間（Table）    | 50ms | 50ms | ベンチマークテスト                |
| レスポンス時間（JSON）     | -    | 40ms | ベンチマークテスト                |
| メモリオーバーヘッド       | 0MB  | +4MB | プロファイリング                  |
| コード行数（ユースケース） | 35   | 15   | wc -l                             |
| 循環的複雑度               | 8    | 4    | radon                             |

### 定性的成功指標

- [ ] **開発者体験**: ビジネスロジックとプレゼンテーション処理の明確分離
- [ ] **保守性**: 新フォーマット追加コスト < 50行
- [ ] **拡張性**: CSV等の新フォーマット対応基盤整備
- [ ] **テスタビリティ**: 各レイヤーの独立テスト可能性
- [ ] **チーム学習**: 責務分離パターンの習得・標準化

### プロジェクト完了判定

**全ての以下条件を満たした時点で完了**:

1. **機能要件**: 全受け入れ基準の達成
2. **品質要件**: 全品質チェックリストの完了
3. **性能要件**: 全性能基準の達成
4. **アーキテクチャ要件**: Clean Architecture 原則の完全準拠
5. **ドキュメント**: 技術仕様書・運用手順書の整備完了

---

## 実装スケジュール

### 詳細タイムライン

```
Day 1 (2025-08-11):
├── 09:00-11:00: タスク1.1 ユースケース純化
├── 11:00-14:00: タスク1.2 TableFormatter分離
├── 14:00-15:00: タスク1.3 CLI統合
└── 15:00-17:00: 段階1品質確認・テスト

Day 2 (2025-08-12):
├── 09:00-11:00: タスク2.1 JsonFormatter実装
├── 11:00-13:00: タスク2.2 フォーマット選択機能
├── 13:00-17:00: 段階2品質確認・統合テスト

Day 3-4 (2025-08-13-14):
├── タスク3.1 包括的テストスイート（4時間）
├── タスク3.2 パフォーマンス最適化（2時間）
└── タスク3.3 最終品質チェック（2時間）

Day 5-7 (2025-08-15-18):
├── 全品質基準の最終確認
├── ドキュメント整備・更新
├── 受け入れテスト・承認プロセス
└── 本番デプロイ準備
```

### マイルストーン

- **M1 (Day 2 EOD)**: 段階1完了・既存機能非劣化確認
- **M2 (Day 4 EOD)**: 段階2完了・JSON機能完全実装
- **M3 (Day 7 EOD)**: 全機能完成・品質基準達成

## まとめ

本実装タスクは、Clean Architecture 原則に基づく体系的な責務分離により、EPGStation モジュールの技術的負債を解消し、将来の機能拡張に備えた堅牢な基盤を構築します。

**実装成功により得られる価値**:

- **技術的負債の解消**: アーキテクチャ適合度 40% → 95%
- **開発効率の向上**: 新機能追加コスト大幅削減
- **品質向上**: テスタビリティとメンテナビリティの抜本改善
- **チーム成長**: Clean Architecture パターンの実践的習得

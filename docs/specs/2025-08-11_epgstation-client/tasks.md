# EPGStation 録画データ管理クライアント機能 - 実装計画

## t-wada TDD 実践方針

全ての実装において、t-wada の Test-Driven Development 手法を厳格に適用する：

### TDD サイクル（Red-Green-Refactor）

1. **Red（失敗）フェーズ**
   - 最もシンプルな失敗するテストを先に書く
   - テスト名は動作を明確に記述（`should_xxx_when_yyy`形式）
   - 失敗メッセージが分かりやすいことを確認

2. **Green（成功）フェーズ**
   - テストを通す最小限のコードを実装
   - この段階では最適化や美しさは考慮しない
   - とにかくテストを通すことに集中

3. **Refactor（改善）フェーズ**
   - テストが通った後でのみリファクタリング
   - 重複を排除し、意図を明確に
   - 各リファクタリング後にテスト実行

### 変更管理の分離

以下の 2 種類の変更を明確に分離：

- **構造変更（Structural Changes）**：コードの配置・整理・フォーマット（動作変更なし）
- **動作変更（Behavioral Changes）**：機能の追加・修正・削除（テスト結果が変わる）

**重要**：構造変更と動作変更を同一コミットに含めない

## 実装タスク一覧

### Phase 1: 基盤実装（TDD重点フェーズ）

#### Task 1.1: プロジェクト基盤設定

**TDD アプローチ**：インフラ設定もテストファーストで

- [ ] **Red**: `test_epgstation_module_imports.py` - モジュールimportテストを作成（失敗）
- [ ] **Green**: `modules/epgstation/__init__.py` - 最小限のモジュール構造作成
- [ ] **Refactor**: モジュール構造の整理・ドキュメント追加

#### Task 1.2: EPGStationConfig 実装

**TDD アプローチ**：設定管理の堅牢性を確保

- [ ] **Red**: `test_epgstation_config.py` - 設定値検証テスト作成（失敗）

  ```python
  def test_should_validate_base_url_format_when_invalid_url_provided():
      # 不正なURL形式でValidationErrorが発生することを確認

  def test_should_set_default_values_when_optional_fields_omitted():
      # デフォルト値が正しく設定されることを確認
  ```

- [ ] **Green**: `config.py` - EPGStationConfig基本実装
- [ ] **Refactor**: バリデーションロジックの整理・可読性向上

#### Task 1.3: ドメインモデル実装（Value Object優先）

**TDD アプローチ**：ビジネスロジックの正確性を保証

- [ ] **Red**: `test_video_file.py` - VideoFile値オブジェクトテスト作成

  ```python
  def test_should_format_file_size_in_appropriate_unit_when_large_size():
      # ファイルサイズの単位変換ロジックをテスト

  def test_should_handle_zero_size_gracefully_when_empty_file():
      # ゼロバイトファイルの表示テスト
  ```

- [ ] **Green**: `domain.py` - VideoFile実装（最小限）
- [ ] **Refactor**: プロパティメソッドの最適化
- [ ] **Red**: `test_recording_data.py` - RecordingData エンティティテスト作成
- [ ] **Green**: `domain.py` - RecordingData実装
- [ ] **Refactor**: 時刻フォーマット・ビジネスロジック整理

### Phase 2: 認証・セッション管理（セキュリティ重点）

#### Task 2.1: Cookie キャッシュ機能

**TDD アプローチ**：セキュリティとパフォーマンスのバランス

- [ ] **Red**: `test_cookie_cache.py` - キャッシュ読み書きテスト作成

  ```python
  def test_should_save_cookies_with_secure_permissions_when_caching():
      # Cookie ファイルが 600 権限で保存されることを確認

  def test_should_return_none_when_cache_file_corrupted():
      # 破損したキャッシュファイルの処理テスト
  ```

- [ ] **Green**: `infrastructure.py` - Cookie キャッシュ基本機能
- [ ] **Refactor**: セキュリティ強化・エラーハンドリング改善

#### Task 2.2: Selenium認証プロバイダー

**TDD アプローチ**：外部依存を分離したテスタブル設計

- [ ] **Red**: `test_session_provider.py` - 認証プロバイダーテスト作成

  ```python
  def test_should_return_cached_cookies_when_session_valid():
      # 有効なキャッシュがある場合の動作テスト

  def test_should_perform_fresh_login_when_cache_expired():
      # キャッシュ期限切れ時の新規認証テスト（モック使用）
  ```

- [ ] **Green**: `infrastructure.py` - SeleniumEPGStationSessionProvider実装
- [ ] **Refactor**: WebDriver管理・リソース解放の最適化

#### Task 2.3: セッション有効性検証

**TDD アプローチ**：認証状態の確実な判定

- [ ] **Red**: `test_session_validation.py` - セッション検証テスト作成
- [ ] **Green**: セッション有効性チェック機能実装
- [ ] **Refactor**: API 呼び出し最適化・タイムアウト処理

### Phase 3: API連携・データアクセス

#### Task 3.1: EPGStation HTTP クライアント

**TDD アプローチ**：外部APIとの通信の信頼性確保

- [ ] **Red**: `test_recording_repository.py` - Repository テスト作成

  ```python
  def test_should_return_recordings_list_when_api_responds_successfully():
      # API成功時の録画データ取得テスト（モック使用）

  def test_should_handle_api_error_gracefully_when_server_unavailable():
      # APIエラー時の適切な例外処理テスト
  ```

- [ ] **Green**: `infrastructure.py` - EPGStationRecordingRepository実装
- [ ] **Refactor**: HTTP クライアント設定・リトライロジック最適化

#### Task 3.2: JSON レスポンス解析

**TDD アプローチ**：データマッピングの正確性保証

- [ ] **Red**: `test_response_parsing.py` - JSONパース処理テスト作成
- [ ] **Green**: API レスポンス → ドメインオブジェクト変換実装
- [ ] **Refactor**: パフォーマンス最適化・エラーハンドリング強化

### Phase 4: ユースケース・ビジネスロジック

#### Task 4.1: 録画一覧取得ユースケース

**TDD アプローチ**：ビジネス要件の完全な実現

- [ ] **Red**: `test_list_recordings_usecase.py` - ユースケーステスト作成

  ```python
  def test_should_return_formatted_table_when_recordings_exist():
      # 正常系：録画データのテーブル表示テスト

  def test_should_return_empty_message_when_no_recordings_found():
      # 録画データが0件の場合のメッセージテスト

  def test_should_display_all_video_files_when_multiple_files_exist():
      # 複数ビデオファイルの表示確認テスト
  ```

- [ ] **Green**: `usecases.py` - ListRecordingsUseCase実装
- [ ] **Refactor**: テーブルフォーマット・エラーメッセージ最適化

#### Task 4.2: 表示フォーマット機能

**TDD アプローチ**：ユーザーエクスペリエンスの向上

- [ ] **Red**: `test_table_formatter.py` - 表示フォーマットテスト作成
- [ ] **Green**: テーブル表示・文字列整形機能実装
- [ ] **Refactor**: 表示レイアウト・文字制限処理の改善

### Phase 5: CLI統合・ユーザーインターフェース

#### Task 5.1: CLI コマンド実装

**TDD アプローチ**：コマンドラインインターフェースの使いやすさ

- [ ] **Red**: `test_cli_epgstation.py` - CLIコマンドテスト作成

  ```python
  def test_should_execute_list_command_successfully_when_valid_options():
      # moro epgstation list コマンドの動作テスト

  def test_should_show_help_message_when_invalid_options_provided():
      # 不正なオプション時のヘルプ表示テスト
  ```

- [ ] **Green**: `cli/epgstation.py` - CLIコマンド実装
- [ ] **Refactor**: Click オプション・ヘルプメッセージ最適化

#### Task 5.2: メインCLI統合

**TDD アプローチ**：既存システムとの統合性確保

- [ ] **Red**: `test_cli_integration.py` - CLI統合テスト作成
- [ ] **Green**: `cli.py` へのepgstation コマンド追加
- [ ] **Refactor**: コマンドグループ・インポート整理

### Phase 6: 品質保証・運用準備

#### Task 6.1: エンドツーエンドテスト

**TDD アプローチ**：システム全体の動作確認

- [ ] **Red**: `test_e2e_epgstation.py` - E2Eテストシナリオ作成
- [ ] **Green**: E2Eテスト用のテストダブル・モック整備
- [ ] **Refactor**: テスト安定性・実行時間最適化

#### Task 6.2: パフォーマンステスト

**TDD アプローチ**：性能要件の確実な達成

- [ ] **Red**: `test_performance.py` - パフォーマンステスト作成
- [ ] **Green**: パフォーマンス計測・最適化実装
- [ ] **Refactor**: メモリ使用量・レスポンス時間改善

#### Task 6.3: セキュリティテスト

**TDD アプローチ**：セキュリティ要件の検証

- [ ] **Red**: `test_security.py` - セキュリティテスト作成
- [ ] **Green**: セキュリティ要件の実装確認
- [ ] **Refactor**: 脆弱性対策・セキュアコーディング強化

## 品質ゲートと完了基準

### 各Phase完了基準

1. **全テストが Pass 状態**（コード実装前にテスト作成）
2. **ruff・mypy チェック 0 警告**（静的解析クリア）
3. **カバレッジ 90% 以上**（重要なビジネスロジック）
4. **E2E テスト成功**（実際の使用シナリオ）

### コミット規律

- **TDD サイクル毎のコミット**：Red→Green→Refactor の各段階
- **構造変更・動作変更の分離**：別々のコミットとして管理
- **コミットメッセージ規約**：
  ```
  feat(epgstation): [Red] add failing test for video file size formatting
  feat(epgstation): [Green] implement video file size formatting logic
  refactor(epgstation): [Refactor] optimize file size calculation performance
  ```

### 依存関係管理

- **外部依存の最小化**：必要最小限のライブラリ使用
- **テストダブルの活用**：Selenium・HTTP通信のモック化
- **インターフェース分離**：Protocol による疎結合設計

### 継続的品質改善

- **各機能完成毎のレビュー**：設計・実装・テストの三位一体チェック
- **リファクタリング継続**：コードの可読性・保守性向上
- **ベストプラクティス適用**：moro 既存パターンの踏襲

## 実装時の注意事項

### TDD実践での重要ポイント

1. **テストファースト厳守**：コード実装前に必ずテスト作成
2. **最小実装原則**：テストを通すだけの最小限のコード
3. **リファクタリング安全性**：テストが通った状態でのみリファクタリング
4. **テスト品質**：読みやすく・保守しやすい・意図が明確なテスト

### セキュリティ配慮

- **機密情報の取り扱い**：Cookie・認証情報の安全な管理
- **入力値検証**：全ての外部入力に対する厳密な検証
- **ログ出力制御**：機密情報のマスク処理・適切なログレベル

### パフォーマンス配慮

- **メモリ効率**：大量データ処理時のメモリ使用量最適化
- **ネットワーク効率**：適切なタイムアウト・リトライ設定
- **キャッシュ戦略**：Cookie キャッシュの効果的な活用

この実装計画により、堅牢で保守性の高い EPGStation クライアント機能を TDD で構築します。

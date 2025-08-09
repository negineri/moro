# テスト設計書: create_app_config() 環境変数読み込み機能

**日付**: 2025-07-20
**機能**: create*app_config() 関数に MORO_SETTINGS* 環境変数読み込み機能を追加

## 機能仕様

- **対象関数**: `create_app_config()`
- **環境変数プレフィックス**: `MORO_SETTINGS_`
- **優先順位**: デフォルト値 → 設定ファイル → 環境変数 → options 引数

## テスト項目

### [ ] Happy Path: 基本機能の検証

#### [ ] HP-1: 単一環境変数の読み込み

- **前提条件**: `MORO_SETTINGS_JOBS=8` が設定されている
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: `AppConfig.jobs` が 8 になる

#### [ ] HP-2: 複数環境変数の読み込み

- **前提条件**: `MORO_SETTINGS_JOBS=4`, `MORO_SETTINGS_WORKING_DIR=/tmp` が設定
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: `jobs=4`, `working_dir="/tmp"` になる

#### [ ] HP-3: 文字列型設定値の読み込み

- **前提条件**: `MORO_SETTINGS_USER_DATA_DIR=/custom/data` が設定
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: `user_data_dir="/custom/data"` になる

#### [ ] HP-4: 数値型設定値の読み込み（文字列として）

- **前提条件**: `MORO_SETTINGS_JOBS=32` が設定
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: 辞書には `{"jobs": "32"}` として格納され、Pydantic が `jobs=32` (int 型) に変換

### [ ] Error Cases: エラー処理シナリオ

#### [ ] EC-1: 無効な数値の処理

- **前提条件**: `MORO_SETTINGS_JOBS=invalid` が設定
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: 辞書には `{"jobs": "invalid"}` として格納され、Pydantic ValidationError が発生

#### [ ] EC-2: 存在しないフィールドの処理

- **前提条件**: `MORO_SETTINGS_UNKNOWN_FIELD=value` が設定
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: エラーが発生せず、未知のフィールドは無視される

### [ ] Edge Cases: 境界条件

#### [ ] ED-1: 環境変数が設定されていない場合

- **前提条件**: MORO*SETTINGS* 環境変数が一切設定されていない
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: デフォルト値が使用される

#### [ ] ED-2: 空文字列の環境変数

- **前提条件**: `MORO_SETTINGS_WORKING_DIR=""` が設定
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: 空文字列が設定値として使用される

#### [ ] ED-3: 設定ファイルと環境変数の優先度

- **前提条件**: 設定ファイルに `jobs=16`, 環境変数に `MORO_SETTINGS_JOBS=8`
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: 環境変数が優先され `jobs=8` になる

#### [ ] ED-4: 環境変数と options 引数の優先度

- **前提条件**: 環境変数 `MORO_SETTINGS_JOBS=8`, options `{"jobs": 4}`
- **実行**: `create_app_config(options={"jobs": 4})` を呼び出し
- **期待結果**: options 引数が優先され `jobs=4` になる

### [ ] Integration: コンポーネント間の相互作用

#### [ ] IT-1: load_config_files() との統合

- **前提条件**: 設定ファイルと環境変数の両方が設定されている
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: 正しい優先順位で設定がマージされる

#### [ ] IT-2: AppConfig バリデーションとの統合

- **前提条件**: 環境変数で無効な値が設定されている
- **実行**: `create_app_config()` を呼び出し
- **期待結果**: Pydantic バリデーションが正常に動作する

## 実装要件

- 新しい関数 `load_env_vars()` を作成
- `create_app_config()` 内で環境変数読み込みを統合
- 環境変数値は文字列のまま辞書に格納（型変換は Pydantic に委ねる）
- エラーハンドリング
- 既存テストの互換性維持

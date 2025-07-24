# SeleniumSessionIdProvider テスト設計書

作成日: 2025-07-24
機能名: SeleniumSessionIdProvider - Seleniumベースのsession_id取得Provider

## テスト対象

`SeleniumSessionIdProvider` - SessionIdProviderの具象実装でSeleniumを使用してFantiaにログインしsession_idを取得

## テスト項目

### 1. Happy Path テスト

- [ ] `get_session_id()` - 正常なログインフローでsession_idを取得・返却
- [ ] `get_session_id()` - ユーザーデータディレクトリが指定された場合の動作
- [ ] `get_session_id()` - 既にログイン済みの場合の session_id取得

### 2. Error Cases テスト

- [ ] `get_session_id()` - ログインに失敗した場合にNoneを返す
- [ ] `get_session_id()` - WebDriverの初期化に失敗した場合のエラーハンドリング
- [ ] `get_session_id()` - session_idクッキーが見つからない場合

### 3. Edge Cases テスト

- [ ] `get_session_id()` - ネットワークエラー時の適切な処理
- [ ] `get_session_id()` - WebDriverのタイムアウト処理
- [ ] `get_session_id()` - 同時実行時の動作（複数インスタンス）

### 4. Integration テスト

- [ ] SessionIdProviderインターフェースとの互換性確認
- [ ] FantiaClientとの統合テスト
- [ ] 既存のlogin_fantia関数との動作比較

## 実装方針

1. SessionIdProviderを継承した具象クラス
2. 既存のlogin_fantia関数のロジックを参考に実装
3. Chrome WebDriverを使用したSeleniumベースのログイン
4. ユーザーデータディレクトリのカスタマイズ対応
5. Graceful degradation（エラー時はNoneを返す）

## 設計考慮事項

- **パフォーマンス**: WebDriverの起動は重い処理なので、必要時のみ実行
- **セキュリティ**: session_idの適切な管理
- **並行性**: 複数インスタンスでの同時実行を考慮
- **リソース管理**: WebDriverの適切なクリーンアップ

## 成功条件

- すべてのテストケースが通る
- SessionIdProviderインターフェースに準拠
- 型チェック（mypy）が通る
- リンター（ruff）が通る
- 既存のFantiaClientと正常に統合される

# 自動Session_ID更新機能 テスト設計書

作成日: 2025-07-24
機能名: FantiaClient自動session_id更新機能

## テスト対象

`FantiaClient.get()` メソッドのオーバーライド - session_idが無効な場合の自動更新機能

## テスト項目

### 1. Happy Path テスト

- [ ] `get()` - 有効なsession_idで正常にリクエストが成功する
- [ ] `get()` - session_idが無効な場合、自動更新してリトライが成功する
- [ ] `get()` - SessionIdProviderから新しいsession_idを取得して使用する

### 2. Error Cases テスト

- [ ] `get()` - session_idが無効で、Providerも新しいsession_idを提供できない場合
- [ ] `get()` - SessionIdProviderが設定されていない場合のエラーハンドリング
- [ ] `get()` - リトライ後も401が返される場合の適切なエラー処理

### 3. Edge Cases テスト

- [ ] `get()` - 401以外のHTTPエラー（403, 404等）では自動更新しない
- [ ] `get()` - ネットワークエラーでは自動更新しない
- [ ] `get()` - 最大1回のリトライ制限を守る（無限ループ防止）

### 4. Integration テスト

- [ ] 既存のFantiaClientテストとの後方互換性確認
- [ ] check_login()関数との連携テスト
- [ ] 実際のAPIエンドポイント（/api/v1/me）でのテスト

## 実装方針

1. `get()` メソッドをオーバーライド
2. 401レスポンスの検出ロジック
3. SessionIdProviderから新しいsession_idを取得
4. Cookie更新とリトライ実行
5. リトライ回数制限（最大1回）

## 成功条件

- すべてのテストケースが通る
- 既存テストに影響なし
- 型チェック（mypy）が通る
- リンター（ruff）が通る
- 既存のget()インターフェースを維持

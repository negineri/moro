# SessionIdProvider テスト設計書

作成日: 2025-07-24
機能名: SessionIdProvider

## テスト対象

`SessionIdProvider` - Fantiaのsession_idを動的に提供するプロバイダー

## テスト項目

### 1. Happy Path テスト

- [ ] `get_session_id()` - 有効なsession_idが取得できる場合、文字列を返す
- [ ] `get_session_id()` - 複数回呼び出しても動作する

### 2. Error Cases テスト

- [ ] `get_session_id()` - session_idが取得できない場合、Noneを返す
- [ ] `get_session_id()` - 例外が発生してもNoneを返す（graceful degradation）

### 3. Edge Cases テスト

- [ ] `get_session_id()` - 空文字列の場合はNoneを返す
- [ ] `get_session_id()` - None値の場合はNoneを返す

### 4. Integration テスト

- [ ] FantiaClientとの統合 - Providerから取得したsession_idでHTTPクライアントが動作
- [ ] FantiaClientとの統合 - ProviderがNoneを返した場合の適切な処理

## 実装方針

1. 抽象クラス/プロトコルでインターフェースを定義
2. 具体的な取得方法は後で実装するため、テスト用のモック実装を作成
3. injectorライブラリを使用した依存性注入対応
4. 型安全性を重視（Optional[str]の明示的な使用）

## 成功条件

- すべてのテストケースが通る
- 型チェック（mypy）が通る
- リンター（ruff）が通る
- FantiaClientとの統合が正常に機能する

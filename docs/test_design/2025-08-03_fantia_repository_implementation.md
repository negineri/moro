# テスト設計書: Fantia Repository 具体実装

**作成日**: 2025-08-03
**機能名**: Fantia Repository 具体実装（`FantiaPostRepositoryImpl`, `FantiaCreatorRepositoryImpl`）
**対象ファイル**: `src/moro/modules/fantia/infrastructure.py`

## 概要

Repository interface の具体実装を infrastructure.py に追加する。既存の `parse_post()` と `get_posts_by_user()` 機能を Repository パターンに移行し、依存性注入可能な設計にする。

## 実装設計

### FantiaPostRepositoryImpl

- 既存の `parse_post()` 機能を Repository に移行
- `get_many()` メソッドで並列処理を実装
- FantiaClient への依存を注入方式にする

### FantiaCreatorRepositoryImpl

- 既存の `get_posts_by_user()` 機能を活用
- Creator 名前の取得機能を追加
- HTML スクレイピングによる情報抽出

## テスト項目（TODO 形式）

### FantiaPostRepositoryImpl

#### Happy Path テスト

- [ ] `get(post_id)`: 有効な投稿IDで正常な FantiaPostData を取得できる
- [ ] `get(post_id)`: 既存の `parse_post()` と同等の結果が得られる
- [ ] `get_many([])`: 空のリストで空のリストが返される
- [ ] `get_many([post_id1, post_id2])`: 複数投稿の一括取得ができる
- [ ] `get_many()`: 個別の `get()` 呼び出しより効率的である

#### Error Cases テスト

- [ ] `get(invalid_id)`: 存在しない投稿IDで None が返される
- [ ] `get(blog_post_id)`: ブログ投稿で NotImplementedError が発生する
- [ ] `get()`: ネットワークエラー時に適切な例外が発生する
- [ ] `get()`: 認証エラー（401）時に適切な例外が発生する
- [ ] `get_many([valid_id, invalid_id])`: 一部無効IDがある場合、有効なもののみ返される

#### Edge Cases テスト

- [ ] `get("")`: 空文字列IDで None が返される
- [ ] `get_many([duplicate_id, duplicate_id])`: 重複IDで重複除去される
- [ ] `get_many(large_list)`: 大量ID（100件）で適切に処理される

### FantiaCreatorRepositoryImpl

#### Happy Path テスト

- [ ] `get(creator_id)`: 有効なクリエイターIDで正常な FantiaCreator を取得できる
- [ ] `get(creator_id)`: 投稿一覧が正しく取得される
- [ ] `get(creator_id)`: クリエイター名が正しく取得される
- [ ] `get(creator_id)`: 既存の `get_posts_by_user()` と同等の投稿一覧が得られる

#### Error Cases テスト

- [ ] `get(invalid_id)`: 存在しないクリエイターIDで None が返される
- [ ] `get()`: ネットワークエラー時に適切な例外が発生する
- [ ] `get()`: 認証エラー時に適切な例外が発生する

#### Edge Cases テスト

- [ ] `get("")`: 空文字列IDで None が返される
- [ ] `get(creator_with_no_posts)`: 投稿が存在しないクリエイターで空の投稿リストが返される
- [ ] `get(creator_with_many_posts)`: 大量投稿（1000件以上）を持つクリエイターで正しく処理される

### Integration テスト

#### Repository間の連携テスト

- [ ] CreatorRepository で取得した投稿一覧を PostRepository で取得できる
- [ ] 同じ FantiaClient インスタンスを共有して動作する
- [ ] セッション管理が Repository 間で整合性を保つ

#### 既存実装との互換性テスト

- [ ] `FantiaPostRepositoryImpl.get()` と `parse_post()` の結果が同等
- [ ] `FantiaCreatorRepositoryImpl.get().posts` と `get_posts_by_user()` の結果が同等
- [ ] 既存の FantiaClient 設定がそのまま利用できる

#### 依存性注入テスト

- [ ] FantiaClient の注入が正しく動作する
- [ ] Mock FantiaClient でのテストが可能
- [ ] Repository インスタンスの lifecycle 管理

### Performance テスト

#### 効率性テスト

- [ ] `get_many()` が個別 `get()` より高速である
- [ ] 並列処理が適切に動作する（同時実行数制限）
- [ ] メモリ使用量が適切な範囲内である

#### エラー処理性能テスト

- [ ] タイムアウト処理が適切に動作する
- [ ] リトライ処理が設定に従って動作する
- [ ] 大量エラー時の処理が安定している

## Mock 戦略

### FantiaClient のモック化

- HTTP レスポンスのモック
- 認証状態のモック
- エラー状態のモック

### 段階的テスト実装

1. Mock を使用した単体テスト
2. 実際の API を使用した統合テスト
3. パフォーマンステスト

## 実装順序

1. **Red フェーズ**: Repository 実装が存在しない失敗テスト
2. **Green フェーズ**: 最小限の Repository 実装
3. **Refactor フェーズ**: 既存機能の移行と最適化

## 注意事項

- 既存の `parse_post()` と `get_posts_by_user()` を破壊的に変更
- 後方互換性は考慮しない（リファクタリングが主目的）
- DI コンテナとの統合を前提とした設計
- 既存のエラーハンドリングパターンを継承

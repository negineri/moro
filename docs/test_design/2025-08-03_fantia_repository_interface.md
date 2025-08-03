# テスト設計書: Fantia Repository Interface

**作成日**: 2025-08-03
**機能名**: Fantia Repository Interface（`FantiaPostRepository`, `FantiaCreatorRepository`）
**対象ファイル**: `src/moro/modules/fantia/domain.py`

## 概要

DDD に従い、Fantia モジュールにおけるデータアクセスの責務を分離するため、Repository interface を domain.py に追加する。既存の実装をリファクタリングし、凝縮度の高い設計を実現する。

## テスト項目（TODO 形式）

### FantiaPostRepository Interface

#### Happy Path テスト

- [ ] `get(post_id: str) -> Optional[FantiaPostData]`: 存在する投稿IDで正常なデータを取得できる
- [ ] `get_many(post_ids: list[str]) -> list[FantiaPostData]`: 複数の投稿IDで一括取得できる
- [ ] `get_many()`: 空のリストを渡した場合、空のリストが返される

#### Error Cases テスト

- [ ] `get()`: 存在しない投稿IDでNoneが返される
- [ ] `get()`: 無効な投稿ID（空文字、None）でNoneが返される
- [ ] `get()`: ネットワークエラー時の例外処理
- [ ] `get()`: 認証エラー（401）時の例外処理
- [ ] `get_many()`: 一部存在しない投稿IDが含まれる場合、存在するもののみ返される

#### Edge Cases テスト

- [ ] `get()`: 非常に長い投稿IDでの処理
- [ ] `get_many()`: 大量の投稿ID（100件以上）での処理
- [ ] `get_many()`: 重複した投稿IDが含まれる場合の重複除去
- [ ] `get()`: ブログ投稿（未対応コンテンツ）での適切なエラーハンドリング

### FantiaCreatorRepository Interface

#### Happy Path テスト

- [ ] `get(creator_id: str) -> Optional[FantiaCreator]`: 存在するクリエイターIDで正常なデータを取得できる
- [ ] `get()`: 投稿が存在するクリエイターで投稿ID一覧が取得できる
- [ ] `get()`: 投稿が存在しないクリエイターで空の投稿一覧が返される

#### Error Cases テスト

- [ ] `get()`: 存在しないクリエイターIDでNoneが返される
- [ ] `get()`: 無効なクリエイターID（空文字、None）でNoneが返される
- [ ] `get()`: ネットワークエラー時の例外処理
- [ ] `get()`: 認証エラー時の例外処理

#### Edge Cases テスト

- [ ] `get()`: 大量の投稿を持つクリエイター（1000件以上）での処理
- [ ] `get()`: 非常に長いクリエイターIDでの処理

### Integration テスト

#### Repository間の連携テスト

- [ ] `FantiaCreatorRepository.get()` で取得した投稿ID一覧を `FantiaPostRepository.get_many()` で取得できる
- [ ] Creator の投稿一覧と Post の実際のデータに整合性がある
- [ ] 複数の Repository インスタンスが同じセッションを共有できる

#### 既存実装との互換性テスト

- [ ] 現在の `parse_post()` 関数と同等の結果が得られる
- [ ] 現在の `get_posts_by_user()` 関数と同等の結果が得られる
- [ ] 既存の `FantiaPostData` モデルとの完全な互換性

### Performance テスト

- [ ] `get_many()` のバッチ処理が個別の `get()` 呼び出しより効率的
- [ ] 大量データ処理時のメモリ使用量が適切な範囲内
- [ ] 並行リクエスト処理の安全性

## 新規エンティティ設計

### FantiaCreator

```python
class FantiaCreator(BaseModel):
    id: str
    name: str
    posts: list[str]  # post_id のリスト
```

#### FantiaCreator テスト項目

- [ ] 必須フィールド（id, name, posts）の検証
- [ ] posts フィールドが空リストでも有効
- [ ] Pydantic バリデーションエラーの適切な処理

## Mock 戦略

- HTTPクライアントのモック化
- セッション認証のモック化
- HTML解析結果のモック化
- 段階的なテスト実装（Protocol → Mock実装 → 本実装）

## 実装順序

1. Protocol interface の定義
2. Mock実装による失敗テスト作成
3. 最小限の実装でテスト通過
4. 既存機能との統合テスト
5. パフォーマンステスト

## 注意事項

- 既存の `__init__.py` の実装を破壊的に変更する予定
- 現在の関数群をRepository実装に移行
- 後方互換性は考慮しない（リファクタリングが主目的）

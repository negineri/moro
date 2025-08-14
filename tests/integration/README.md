# Integration Tests - Cross-module boundaries

モジュール境界を跨ぐ統合テスト。最小限の価値あるテストのみ実装。

## 実行方法

```bash
# 統合テスト実行
pytest tests/integration/ -m integration -v

# 外部システム統合のみ
pytest tests/integration/external_systems/ -v
```

## カテゴリ

- `cli_to_modules/`: CLI層からモジュール層への統合
- `external_systems/`: 外部API・システムとの統合
- `infrastructure/`: データベース・ファイルシステム統合

# EPGStation Module Unit Tests - 完全独立実行

EPGStationモジュールの単体テスト。他モジュールへの依存・参照は一切禁止。

## 実行方法

```bash
# 単独実行（他モジュール不要）
pytest tests/unit/modules/epgstation/ -v

# 高速並列実行
pytest tests/unit/modules/epgstation/ -n auto
```

## 構造

- `test_domain.py`: ドメインエンティティ・値オブジェクト
- `test_usecases.py`: アプリケーションサービス・ユースケース
- `test_infrastructure.py`: リポジトリ実装・外部API連携
- `test_config.py`: 設定管理・バリデーション

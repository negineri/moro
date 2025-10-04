# E2E Tests - Full user workflows

完全なユーザーワークフローのエンドツーエンドテスト。実行時間を考慮し最小限に限定。

## 実行方法

```bash
# E2E テスト実行
pytest tests/e2e/ -m e2e -v

# 特定ワークフローのみ
pytest tests/e2e/workflows/test_fantia_download_workflow.py -v
```

## カテゴリ

- `workflows/`: 完全なユーザーワークフロー（CLI → モジュール → 外部システム）
- `scenarios/`: ユーザーシナリオ・エラー回復シナリオ

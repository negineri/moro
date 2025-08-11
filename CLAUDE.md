# CLAUDE.md

## 概要

"moro" - Click を CLI、Injector による DI、Pydantic による設定管理を使用した Python 個人用ツールボックス。

## 開発コマンド

```bash
# 実行
uv run moro

# テスト
uv run pytest --cov=src --cov-report=term-missing

# コード品質チェック
uv run ruff check
uv run mypy
```

## アーキテクチャ

レイヤードアーキテクチャ + 依存性注入によるモジュラー設計。

### 構造

```text
src/moro/
├── cli/          # CLIレイヤー
├── config/       # 設定管理
├── dependencies/ # DI設定
├── modules/      # ドメインモジュール（相互参照禁止、common.pyは例外）
└── scenarios/    # 横断的ユースケース
```

### 拡張パターン

- 新 CLI コマンド: `cli/`に追加後、`cli.py`で登録
- 新機能: モジュールを跨ぐ機能は`scenarios/`に実装する

### モジュール構造

新しいモジュールを `modules/` に追加する際は、以下の標準構造を採用：

```text
modules/{module_name}/
├── __init__.py
├── config.py          # Pydantic による設定管理
├── domain.py          # ドメインモデル・エンティティ
├── infrastructure.py  # 外部システム連携・データアクセス
└── usecases.py        # ビジネスロジック・ユースケース
```

各ファイルの責務：

- `config.py`: Pydantic モデルによる設定定義、`ConfigRepository` への登録
- `domain.py`: ドメインエンティティ、値オブジェクト、ドメインサービス
- `infrastructure.py`: リポジトリ実装、外部 API クライアント、データベースアクセス
- `usecases.py`: アプリケーションサービス、ユースケース実装

## コードスタイル

- 行長 100 文字、Ruff + MyPy 厳格モード
  - テストコードでも Ruff + MyPy 厳格モードに従う
- `tests/*+`のみ日本語コメント可
- 実装を終えたら pytest で確認する

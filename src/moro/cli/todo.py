"""Todo management commands.

Todo 管理コマンド群

教育的ポイント:
- Click による CLI 設計
- Injector による DI パターン
- コマンドラインインターフェースの設計
- エラーハンドリングとユーザビリティ
- CLI からユースケースへの適切な委譲
"""

from logging import getLogger

import click

from moro.cli._utils import AliasedGroup
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector
from moro.modules.todo.usecases import (
    CreateTodoRequest,
    CreateTodoUseCase,
    DeleteTodoUseCase,
    ListTodosUseCase,
    ToggleTodoUseCase,
    UpdateTodoRequest,
    UpdateTodoUseCase,
)

logger = getLogger(__name__)


@click.group(cls=AliasedGroup)
def todo() -> None:
    """Todo 管理コマンド

    新しい開発者向けの教育的サンプルコマンド群。
    レイヤードアーキテクチャと DDD の実践例を学習できます。
    """
    pass


@todo.command()
@click.argument("title")
@click.option("--description", "-d", default="", help="Todo の詳細説明")
@click.option(
    "--priority",
    "-p",
    default="medium",
    type=click.Choice(["high", "medium", "low"], case_sensitive=False),
    help="優先度 (high/medium/low)",
)
def add(title: str, description: str, priority: str) -> None:
    """新しい Todo を追加する

    Args:
        title: Todo のタイトル（必須）
        description: Todo の詳細説明（オプション）
        priority: 優先度（high/medium/low、デフォルト: medium）

    Examples:
        moro todo add "買い物に行く"
        moro todo add "レポート作成" --description "月次レポートを作成する" --priority high
        moro todo add "本を読む" -d "Python の本を読み終える" -p low

    教育的ポイント:
    - Click による引数とオプションの定義
    - 型安全なオプション設定（Choice）
    - ユースケースへの適切な委譲
    - エラーハンドリングの統一
    """
    try:
        # DI コンテナからユースケースを取得
        config = ConfigRepository.create()
        injector = create_injector(config)
        create_usecase = injector.get(CreateTodoUseCase)

        # リクエストオブジェクトの作成
        request = CreateTodoRequest(title=title, description=description, priority=priority.lower())

        # ユースケース実行
        response = create_usecase.execute(request)

        # 成功メッセージの表示
        click.echo(f"✓ Todo を作成しました: {response.title}")
        click.echo(f"  ID: {response.id}")
        click.echo(f"  優先度: {response.priority}")
        if response.description:
            click.echo(f"  説明: {response.description}")

    except ValueError as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        logger.exception("Unexpected error in add command")
        click.echo(f"❌ 予期しないエラーが発生しました: {e}", err=True)
        raise click.Abort() from e


@todo.command("list")
@click.option("--completed", "-c", is_flag=True, help="完了済みの Todo のみ表示")
@click.option("--pending", "-p", is_flag=True, help="未完了の Todo のみ表示")
@click.option("--sort-by-priority", "-s", is_flag=True, help="優先度順でソート")
def list_todos(completed: bool, pending: bool, sort_by_priority: bool) -> None:
    """Todo 一覧を表示する

    Options:
        --completed, -c: 完了済みの Todo のみ表示
        --pending, -p: 未完了の Todo のみ表示
        --sort-by-priority, -s: 優先度順でソート（デフォルト: 作成日時順）

    Examples:
        moro todo list
        moro todo list --completed
        moro todo list --pending --sort-by-priority
        moro todo list -cs

    教育的ポイント:
    - フラグオプションの使用方法
    - 排他的オプションのハンドリング
    - データのフォーマット表示
    - ユーザビリティを考慮した出力設計
    """
    try:
        # 排他的オプションのチェック
        if completed and pending:
            click.echo("❌ --completed と --pending は同時に指定できません", err=True)
            raise click.Abort()

        # DI コンテナからユースケースを取得
        config = ConfigRepository.create()
        injector = create_injector(config)
        list_usecase = injector.get(ListTodosUseCase)

        # フィルタ条件の決定
        completed_only = None
        if completed:
            completed_only = True
        elif pending:
            completed_only = False

        # ユースケース実行
        todos = list_usecase.execute(
            completed_only=completed_only, sort_by_priority=sort_by_priority
        )

        # 結果の表示
        if not todos:
            if completed:
                click.echo("📋 完了済みの Todo はありません")
            elif pending:
                click.echo("📋 未完了の Todo はありません")
            else:
                click.echo("📋 Todo はありません")
            return

        # ヘッダー表示
        filter_text = ""
        if completed:
            filter_text = " (完了済み)"
        elif pending:
            filter_text = " (未完了)"

        sort_text = " - 優先度順" if sort_by_priority else " - 作成日時順"
        click.echo(f"📋 Todo 一覧{filter_text}{sort_text}")
        click.echo("=" * 50)

        # Todo 一覧の表示
        for todo in todos:
            status = "✓" if todo.is_completed else "○"
            priority_indicator = {"high": "🔴", "medium": "🟡", "low": "🟢"}[todo.priority]

            click.echo(f"{status} [{todo.id[:8]}] {priority_indicator} {todo.title}")

            if todo.description:
                click.echo(f"    📝 {todo.description}")

            created_date = todo.created_at.strftime("%Y-%m-%d %H:%M")
            click.echo(f"    📅 作成: {created_date}")

            if todo.is_completed:
                updated_date = todo.updated_at.strftime("%Y-%m-%d %H:%M")
                click.echo(f"    ✅ 完了: {updated_date}")

            click.echo()  # 空行

        # 統計情報
        total = len(todos)
        completed_count = sum(1 for t in todos if t.is_completed)
        pending_count = total - completed_count

        click.echo(f"合計: {total}件 (完了: {completed_count}件, 未完了: {pending_count}件)")

    except Exception as e:
        logger.exception("Unexpected error in list command")
        click.echo(f"❌ 予期しないエラーが発生しました: {e}", err=True)
        raise click.Abort() from e


@todo.command()
@click.argument("todo_id")
@click.option("--title", "-t", help="新しいタイトル")
@click.option("--description", "-d", help="新しい説明")
@click.option(
    "--priority",
    "-p",
    type=click.Choice(["high", "medium", "low"], case_sensitive=False),
    help="新しい優先度",
)
def update(todo_id: str, title: str | None, description: str | None, priority: str | None) -> None:
    """Todo を更新する

    Args:
        todo_id: 更新する Todo の ID
        title: 新しいタイトル
        description: 新しい説明
        priority: 新しい優先度

    Options:
        --title, -t: 新しいタイトル
        --description, -d: 新しい説明
        --priority, -p: 新しい優先度

    Examples:
        moro todo update abc123 --title "新しいタイトル"
        moro todo update abc123 --description "詳細な説明" --priority high
        moro todo update abc123 -t "買い物" -d "スーパーで食材を購入" -p medium

    教育的ポイント:
    - 部分更新の UI 設計
    - Optional パラメータの扱い
    - ID による対象指定
    - エラーメッセージの分かりやすさ
    """
    try:
        # 最低限一つのオプションが指定されているかチェック
        if not any([title, description, priority]):
            click.echo(
                "❌ 更新する項目を指定してください(--title, --description, --priority のいずれか)",
                err=True,
            )
            raise click.Abort()

        # DI コンテナからユースケースを取得
        config = ConfigRepository.create()
        injector = create_injector(config)
        update_usecase = injector.get(UpdateTodoUseCase)

        # リクエストオブジェクトの作成
        request = UpdateTodoRequest(
            todo_id=todo_id,
            title=title,
            description=description,
            priority=priority.lower() if priority else None,
        )

        # ユースケース実行
        response = update_usecase.execute(request)

        # 成功メッセージの表示
        click.echo(f"✓ Todo を更新しました: {response.title}")
        click.echo(f"  ID: {response.id}")
        click.echo(f"  優先度: {response.priority}")
        if response.description:
            click.echo(f"  説明: {response.description}")

    except ValueError as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        logger.exception("Unexpected error in update command")
        click.echo(f"❌ 予期しないエラーが発生しました: {e}", err=True)
        raise click.Abort() from e


@todo.command()
@click.argument("todo_id")
def toggle(todo_id: str) -> None:
    """Todo の完了状態を切り替える

    Args:
        todo_id: 切り替える Todo の ID

    Examples:
        moro todo toggle abc123

    教育的ポイント:
    - 状態切り替えの UI パターン
    - 分かりやすい操作結果の表示
    - シンプルなコマンド設計
    """
    try:
        # DI コンテナからユースケースを取得
        config = ConfigRepository.create()
        injector = create_injector(config)
        toggle_usecase = injector.get(ToggleTodoUseCase)

        # ユースケース実行
        response = toggle_usecase.execute(todo_id)

        # 成功メッセージの表示
        status_text = "完了" if response.is_completed else "未完了"
        status_icon = "✅" if response.is_completed else "○"

        click.echo(f"{status_icon} Todo を{status_text}にしました: {response.title}")
        click.echo(f"  ID: {response.id}")

    except ValueError as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort() from e
    except Exception as e:
        logger.exception("Unexpected error in toggle command")
        click.echo(f"❌ 予期しないエラーが発生しました: {e}", err=True)
        raise click.Abort() from e


@todo.command()
@click.argument("todo_id")
@click.option("--force", "-f", is_flag=True, help="確認なしで削除")
def delete(todo_id: str, force: bool) -> None:
    """Todo を削除する

    Args:
        todo_id: 削除する Todo の ID
        force: 確認なしで削除するかどうか

    Options:
        --force, -f: 確認なしで削除

    Examples:
        moro todo delete abc123
        moro todo delete abc123 --force
        moro todo delete abc123 -f

    教育的ポイント:
    - 削除操作の安全性設計
    - 確認プロンプトの実装
    - --force オプションの活用
    - ユーザーエクスペリエンスの配慮
    """
    try:
        # 確認プロンプト（--force が指定されていない場合）
        if not force:
            if not click.confirm(f"Todo (ID: {todo_id[:8]}...) を削除しますか?"):
                click.echo("削除をキャンセルしました")
                return

        # DI コンテナからユースケースを取得
        config = ConfigRepository.create()
        injector = create_injector(config)
        delete_usecase = injector.get(DeleteTodoUseCase)

        # ユースケース実行
        deleted = delete_usecase.execute(todo_id)

        if deleted:
            click.echo(f"✓ Todo を削除しました (ID: {todo_id[:8]}...)")
        else:
            click.echo(f"❌ 指定された Todo が見つかりません (ID: {todo_id[:8]}...)", err=True)
            raise click.Abort()

    except Exception as e:
        logger.exception("Unexpected error in delete command")
        click.echo(f"❌ 予期しないエラーが発生しました: {e}", err=True)
        raise click.Abort() from e


@todo.command()
@click.option("--force", "-f", is_flag=True, help="確認なしで削除")
def cleanup(force: bool) -> None:
    """完了済みの Todo を一括削除する

    Options:
        --force, -f: 確認なしで削除

    Examples:
        moro todo cleanup
        moro todo cleanup --force
        moro todo cleanup -f

    教育的ポイント:
    - 一括操作の UI 設計
    - 危険な操作への適切な警告
    - 操作結果の定量的表示
    - バッチ処理パターンの実装
    """
    try:
        # 確認プロンプト（--force が指定されていない場合）
        if not force:
            if not click.confirm("完了済みの Todo を全て削除しますか?"):
                click.echo("削除をキャンセルしました")
                return

        # DI コンテナからユースケースを取得
        config = ConfigRepository.create()
        injector = create_injector(config)
        delete_usecase = injector.get(DeleteTodoUseCase)

        # 一括削除実行
        deleted_count = delete_usecase.delete_completed()

        if deleted_count > 0:
            click.echo(f"✓ {deleted_count}件の完了済み Todo を削除しました")
        else:
            click.echo("削除対象の完了済み Todo はありませんでした")

    except Exception as e:
        logger.exception("Unexpected error in cleanup command")
        click.echo(f"❌ 予期しないエラーが発生しました: {e}", err=True)
        raise click.Abort() from e

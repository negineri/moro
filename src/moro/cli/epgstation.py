"""EPGStation 録画管理コマンド"""

import json
from abc import ABC, abstractmethod

import click
from table2ascii import PresetStyle, table2ascii

from moro.cli._utils import AliasedGroup, click_verbose_option, config_logging
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector
from moro.modules.epgstation.domain import RecordingData
from moro.modules.epgstation.usecases import ListRecordingsUseCase


class OutputFormatter(ABC):
    """出力フォーマットの抽象基底クラス"""

    @abstractmethod
    def format(self, recordings: list["RecordingData"]) -> str:
        """録画データを指定形式でフォーマット"""

    @abstractmethod
    def format_empty_message(self) -> str:
        """データが空の場合のメッセージ"""


class TableFormatter(OutputFormatter):
    """テーブル形式フォーマッター（table2ascii使用）"""

    def format(self, recordings: list["RecordingData"]) -> str:
        """録画データをテーブル形式でフォーマット"""
        if not recordings:
            return self.format_empty_message()

        headers = ["録画ID", "タイトル", "開始時刻", "ファイル名", "種別", "サイズ"]
        rows: list[list[str]] = []

        for recording in recordings:
            if not recording.video_files:
                rows.append(
                    [
                        str(recording.id),
                        self._truncate_text(recording.name, 40),
                        recording.formatted_start_time,
                        "N/A",
                        "N/A",
                        "N/A",
                    ]
                )
            else:
                for video_file in recording.video_files:
                    rows.append(
                        [
                            str(recording.id),
                            self._truncate_text(recording.name, 40),
                            recording.formatted_start_time,
                            video_file.filename or video_file.name,
                            video_file.type.upper(),
                            video_file.formatted_size,
                        ]
                    )

        return self._create_table(headers, rows)

    def format_empty_message(self) -> str:
        """空データの場合のメッセージを返却"""
        return "録画データが見つかりませんでした。"

    def _truncate_text(self, text: str, max_length: int) -> str:
        return text[:max_length] + "..." if len(text) > max_length else text

    def _create_table(self, headers: list[str], rows: list[list[str]]) -> str:
        if not rows:
            return "データがありません。"

        return table2ascii(
            header=headers,
            body=rows,
            style=PresetStyle.ascii_box,
        )


class JsonFormatter(OutputFormatter):
    """JSON形式フォーマッター（堅牢性重視）"""

    def format(self, recordings: list["RecordingData"]) -> str:
        """録画データをJSON形式でフォーマット"""
        if not recordings:
            return self.format_empty_message()

        try:
            # Pydantic model_dump_json() を使用してJSONシリアライゼーション
            json_strings = [recording.model_dump_json() for recording in recordings]
            # 個別のJSON文字列を配列として結合
            return "[\n  " + ",\n  ".join(json_strings) + "\n]"
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"JSON serialization failed: {e}")

            fallback_data = []
            for recording in recordings:
                try:
                    fallback_data.append(
                        {
                            "id": recording.id,
                            "name": recording.name,
                            "start_time": recording.formatted_start_time,
                            "duration_minutes": recording.duration_minutes,
                            "error": "詳細情報の取得に失敗",
                        }
                    )
                except Exception:
                    try:
                        recording_id = getattr(recording, "id", "unknown")
                    except Exception:
                        recording_id = "unknown"

                    fallback_data.append(
                        {
                            "error": "データ取得エラー",
                            "id": recording_id,
                        }
                    )

            return json.dumps(fallback_data, ensure_ascii=False, indent=2)

    def format_empty_message(self) -> str:
        """空データの場合のJSONメッセージを返却"""
        return json.dumps(
            {
                "recordings": [],
                "message": "録画データが見つかりませんでした。",
            },
            ensure_ascii=False,
            indent=2,
        )


@click.group(cls=AliasedGroup)
def epgstation() -> None:
    """EPGStation 録画管理コマンド"""
    pass


@epgstation.command(name="list")
@click.option(
    "--limit",
    default=100,
    type=int,
    help="表示する録画数の上限（デフォルト: 100）",
)
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["table", "json"]),
    default="table",
    help="出力形式（デフォルト: table）",
)
@click_verbose_option
def list_recordings(limit: int, format_type: str, verbose: tuple[bool]) -> None:
    """録画一覧を表示"""
    config = ConfigRepository.create()
    config_logging(config, verbose)
    try:
        injector = create_injector(config)
        use_case = injector.get(ListRecordingsUseCase)

        recordings = use_case.execute(limit=limit)

        formatter_map = {
            "table": TableFormatter(),
            "json": JsonFormatter(),
        }
        formatter = formatter_map[format_type]

        result = formatter.format(recordings)
        click.echo(result)

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Command execution failed: {e}")
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    epgstation()

"""EPGStation ユースケース実装"""

import logging

from injector import inject

from moro.modules.epgstation.domain import RecordingData, RecordingRepository

logger = logging.getLogger(__name__)


@inject
class ListRecordingsUseCase:
    """録画一覧取得ユースケース"""

    def __init__(self, recording_repository: "RecordingRepository") -> None:
        """初期化

        Args:
            recording_repository: 録画データリポジトリ
        """
        self._repository = recording_repository

    def execute(self, limit: int = 100) -> str:
        """録画一覧を取得してテーブル形式で返す

        Args:
            limit: 表示する録画数の上限

        Returns:
            テーブル形式の録画一覧文字列
        """
        try:
            recordings = self._repository.get_all(limit=limit)
            return self._format_table(recordings)
        except Exception as e:
            logger.error(f"Failed to get recordings: {e}")
            return f"エラー: 録画一覧の取得に失敗しました ({e})"

    def _format_table(self, recordings: list["RecordingData"]) -> str:
        """録画データをテーブル形式でフォーマット

        Args:
            recordings: 録画データリスト

        Returns:
            テーブル形式の文字列
        """
        if not recordings:
            return "録画データが見つかりませんでした。"

        headers = ["録画ID", "タイトル", "開始時刻", "ファイル名", "種別", "サイズ"]
        rows: list[list[str]] = []

        for recording in recordings:
            if not recording.video_files:
                # ビデオファイルがない場合
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
                # 各ビデオファイルを個別行として表示
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

    def _truncate_text(self, text: str, max_length: int) -> str:
        """テキストを指定文字数で切り詰め

        Args:
            text: 元のテキスト
            max_length: 最大文字数

        Returns:
            切り詰められたテキスト
        """
        return text[:max_length] + "..." if len(text) > max_length else text

    def _create_table(self, headers: list[str], rows: list[list[str]]) -> str:
        """テーブル形式の文字列を作成

        Args:
            headers: ヘッダー行
            rows: データ行のリスト

        Returns:
            テーブル形式の文字列
        """
        if not rows:
            return "データがありません。"

        # 各列の最大幅を計算
        col_widths: list[int] = []
        for i in range(len(headers)):
            width = len(headers[i])
            for row in rows:
                if i < len(row):
                    width = max(width, len(str(row[i])))
            col_widths.append(width + 2)  # パディング

        # ヘッダー行を作成
        header_line = "│".join(h.ljust(w) for h, w in zip(headers, col_widths, strict=False))
        separator_line = "─" * len(header_line)

        # データ行を作成
        data_lines: list[str] = []
        for row in rows:
            padded_row: list[str] = []
            for i in range(len(headers)):
                cell = str(row[i]) if i < len(row) else ""
                padded_row.append(cell.ljust(col_widths[i]))
            data_lines.append("│".join(padded_row))

        # 結果を組み立て
        result = [header_line, separator_line, *data_lines]
        return "\n".join(result)

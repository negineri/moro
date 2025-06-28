"""曲目リストをHTMLから抽出してCSVに変換するモジュール."""

import csv
from pathlib import Path
from typing import NamedTuple

from bs4 import BeautifulSoup, Tag


class Track(NamedTuple):
    """トラック情報を表すナmedタプル."""

    disc: int
    track: int
    title: str
    duration: str
    file_size: str


class TracklistExtractor:
    """HTMLファイルから曲目リストを抽出してCSVに変換するクラス."""

    def __init__(self, html_content: str) -> None:
        """
        初期化メソッド.

        Args:
            html_content: HTMLコンテンツ
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')

    def extract_tracks(self) -> list[Track]:
        """
        HTMLから曲目リストを抽出する.

        Returns:
            曲目リストのリスト
        """
        tracks = []

        # テーブルの行を取得
        table_rows = self.soup.find_all('tr')

        for row in table_rows:
            # Tagオブジェクトであることを確認
            if not isinstance(row, Tag):
                continue

            cells = row.find_all('td')

            # 最低限必要なセルがあるかチェック
            if len(cells) < 6:
                continue

            try:
                # ディスク番号を取得（2番目のセル）
                disc_cell = cells[1]
                if not isinstance(disc_cell, Tag):
                    continue
                if disc_cell.get('align') != 'center':
                    continue

                disc_text = disc_cell.get_text(strip=True)
                if not disc_text.isdigit():
                    continue
                disc = int(disc_text)

                # トラック番号を取得（3番目のセル）
                track_cell = cells[2]
                if not isinstance(track_cell, Tag):
                    continue
                if track_cell.get('align') != 'right':
                    continue

                track_text = track_cell.get_text(strip=True)
                if not track_text.replace('.', '').isdigit():
                    continue
                track = int(track_text.replace('.', ''))

                # 曲名を取得（4番目のセル）
                title_cell = cells[3]
                if not isinstance(title_cell, Tag):
                    continue
                class_attr = title_cell.get('class')
                if class_attr is None or 'clickable-row' not in class_attr:
                    continue

                title_link = title_cell.find('a')
                if not title_link or not isinstance(title_link, Tag):
                    continue
                title = title_link.get_text(strip=True)

                # 長さを取得（5番目のセル）
                duration_cell = cells[4]
                if not isinstance(duration_cell, Tag):
                    continue
                class_attr = duration_cell.get('class')
                if class_attr is None or 'clickable-row' not in class_attr:
                    continue

                duration_link = duration_cell.find('a')
                if not duration_link or not isinstance(duration_link, Tag):
                    continue
                duration = duration_link.get_text(strip=True)

                # ファイルサイズを取得（6番目のセル）
                size_cell = cells[5]
                if not isinstance(size_cell, Tag):
                    continue
                class_attr = size_cell.get('class')
                if class_attr is None or 'clickable-row' not in class_attr:
                    continue

                size_link = size_cell.find('a')
                if not size_link or not isinstance(size_link, Tag):
                    continue
                file_size = size_link.get_text(strip=True)

                # トラック情報を作成
                track_info = Track(
                    disc=disc,
                    track=track,
                    title=title,
                    duration=duration,
                    file_size=file_size
                )
                tracks.append(track_info)

            except (ValueError, AttributeError):
                # 解析に失敗した行はスキップ
                continue

        return tracks

    def save_to_csv(self, tracks: list[Track], output_path: Path) -> None:
        """
        曲目リストをCSVファイルに保存する.

        Args:
            tracks: 曲目リストのリスト
            output_path: 出力ファイルパス
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # ヘッダーを書き込み
            writer.writerow(['Disc', 'Track', 'Title', 'Duration', 'File Size'])

            # データを書き込み
            for track in tracks:
                writer.writerow([
                    track.disc,
                    track.track,
                    track.title,
                    track.duration,
                    track.file_size
                ])


def extract_tracklist_to_csv(html_file_path: Path, csv_file_path: Path) -> int:
    """
    HTMLファイルから曲目リストを抽出してCSVファイルに保存する.

    Args:
        html_file_path: 入力HTMLファイルパス
        csv_file_path: 出力CSVファイルパス

    Returns:
        抽出されたトラック数
    """
    # HTMLファイルを読み込み
    html_content = html_file_path.read_text(encoding='utf-8')

    # 曲目リストを抽出
    extractor = TracklistExtractor(html_content)
    tracks = extractor.extract_tracks()

    # CSVファイルに保存
    extractor.save_to_csv(tracks, csv_file_path)

    return len(tracks)

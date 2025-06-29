"""曲目リストをHTMLから抽出してCSVに変換するモジュール."""

import csv
import random
from pathlib import Path
from time import sleep
from typing import NamedTuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup, Tag


class Track(NamedTuple):
    """トラック情報を表すナmedタプル."""

    disc: int
    track: int
    title: str
    duration: str
    track_url: str


def extract_tracks(html_content: str, netloc: str) -> list[Track]:
    """
    HTMLから曲目リストを抽出する.

    Args:
        html_content: HTMLコンテンツ
        netloc: ドメイン名

    Returns:
        曲目リストのリスト
    """
    soup = BeautifulSoup(html_content, "html.parser")
    tracks: list[Track] = []

    # テーブルの行を取得
    table_rows = soup.find_all("tr")

    for row in table_rows:
        # Tagオブジェクトであることを確認
        if not isinstance(row, Tag):
            continue

        cells = row.find_all("td")

        # 最低限必要なセルがあるかチェック
        if len(cells) < 6:
            continue

        try:
            # ディスク番号を取得（2番目のセル）
            disc_cell = cells[1]
            if not isinstance(disc_cell, Tag):
                continue
            if disc_cell.get("align") != "center":
                continue

            disc_text = disc_cell.get_text(strip=True)
            if not disc_text.isdigit():
                continue
            disc = int(disc_text)

            # トラック番号を取得（3番目のセル）
            track_cell = cells[2]
            if not isinstance(track_cell, Tag):
                continue
            if track_cell.get("align") != "right":
                continue

            track_text = track_cell.get_text(strip=True)
            if not track_text.replace(".", "").isdigit():
                continue
            track = int(track_text.replace(".", ""))

            # 曲名を取得（4番目のセル）
            title_cell = cells[3]
            if not isinstance(title_cell, Tag):
                continue
            class_attr = title_cell.get("class")
            if class_attr is None or "clickable-row" not in class_attr:
                continue

            title_link = title_cell.find("a")
            if not title_link or not isinstance(title_link, Tag):
                continue
            title = title_link.get_text(strip=True)

            # 長さを取得（5番目のセル）
            duration_cell = cells[4]
            if not isinstance(duration_cell, Tag):
                continue
            class_attr = duration_cell.get("class")
            if class_attr is None or "clickable-row" not in class_attr:
                continue

            duration_link = duration_cell.find("a")
            if not duration_link or not isinstance(duration_link, Tag):
                continue
            duration = duration_link.get_text(strip=True)

            # ファイルサイズを取得（7番目のセル）
            size_cell = cells[6]
            if not isinstance(size_cell, Tag):
                continue
            class_attr = size_cell.get("class")
            if class_attr is None or "clickable-row" not in class_attr:
                continue

            size_link = size_cell.find("a")
            if not size_link or not isinstance(size_link, Tag):
                continue
            href = size_link.get("href")
            if not href or not isinstance(href, str):
                continue

            # hrefが相対パスの場合、完全なURLに変換
            if not href.startswith("http"):
                href = f"https://{netloc}{href}"

            # HTTPリクエストでHTMLコンテンツを取得
            sleep(random.uniform(0.5, 1.5))  # noqa: S311
            with httpx.Client(timeout=30.0) as client:
                response = client.get(href)
                response.raise_for_status()
                html_content = response.text

            track_url = extract_track_url(html_content)

            # トラック情報を作成
            track_info = Track(
                disc=disc, track=track, title=title, duration=duration, track_url=track_url
            )
            tracks.append(track_info)

        except (ValueError, AttributeError):
            # 解析に失敗した行はスキップ
            continue

    return tracks


def extract_track_url(content: str) -> str:
    """
    HTMLからトラックのURLを抽出する.

    Args:
        content: HTMLコンテンツ

    Returns:
        完全なトラックURL
    """
    soup = BeautifulSoup(content, "html.parser")
    hrefs = soup.select("a[href]")
    for a in hrefs:
        href = a.get("href")
        if not href or not isinstance(href, str):
            continue
        if not href.endswith(".flac"):
            continue

        # トラックのリンクを見つけたら返す
        return href

    return ""


def save_tracks_to_csv(tracks: list[Track], output_path: Path) -> None:
    """
    曲目リストをCSVファイルに保存する.

    Args:
        tracks: 曲目リストのリスト
        output_path: 出力ファイルパス
    """
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # ヘッダーを書き込み
        writer.writerow(["Disc", "Track", "Title", "Duration", "Track URL"])

        # データを書き込み
        for track in tracks:
            writer.writerow([track.disc, track.track, track.title, track.duration, track.track_url])


def extract_tracklist_from_url_to_csv(url: str, csv_file_path: Path) -> int:
    """
    URLから曲目リストを抽出してCSVファイルに保存する.

    Args:
        url: 曲目リストが含まれるWebページのURL
        csv_file_path: 出力CSVファイルパス

    Returns:
        抽出されたトラック数

    Raises:
        httpx.HTTPError: HTTP通信エラー
        ValueError: 無効なURLまたはHTMLコンテンツ
    """
    try:
        # URLからHTMLコンテンツを取得
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            html_content = response.text

        # ドメイン名を抽出
        netloc = urlparse(url).netloc
        if not netloc:
            raise ValueError("無効なURL: ドメイン名が取得できません")

        # 曲目リストを抽出
        tracks = extract_tracks(html_content, netloc)

        # CSVファイルに保存
        save_tracks_to_csv(tracks, csv_file_path)

        return len(tracks)

    except httpx.HTTPError as e:
        raise httpx.HTTPError(f"URL取得エラー: {e}") from e
    except Exception as e:
        raise ValueError(f"HTML解析エラー: {e}") from e

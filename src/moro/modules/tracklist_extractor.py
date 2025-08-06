"""曲目リストをHTMLから抽出してCSVに変換するモジュール."""

import csv
import random
from collections.abc import Sequence
from pathlib import Path
from time import sleep
from typing import Any, NamedTuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup, Tag
from bs4.element import PageElement


class Track(NamedTuple):
    """トラック情報を表すナmedタプル."""

    disc: int
    track: int
    title: str
    duration: str
    track_url: str


def _extract_disc_number(cells: Sequence[PageElement]) -> int | None:
    """
    テーブル行からディスク番号を抽出する.

    Args:
        cells: テーブルセルのリスト

    Returns:
        ディスク番号、抽出に失敗した場合はNone
    """
    if len(cells) < 2:
        return None

    disc_cell = cells[1]
    if not isinstance(disc_cell, Tag):
        return None
    if disc_cell.get("align") != "center":
        return None

    disc_text = disc_cell.get_text(strip=True)
    if not disc_text.isdigit():
        return None

    return int(disc_text)


def _extract_track_number(cells: Sequence[PageElement]) -> int | None:
    """
    テーブル行からトラック番号を抽出する.

    Args:
        cells: テーブルセルのリスト

    Returns:
        トラック番号、抽出に失敗した場合はNone
    """
    if len(cells) < 3:
        return None

    track_cell = cells[2]
    if not isinstance(track_cell, Tag):
        return None
    if track_cell.get("align") != "right":
        return None

    track_text = track_cell.get_text(strip=True)
    if not track_text.replace(".", "").isdigit():
        return None

    return int(track_text.replace(".", ""))


def _extract_title(cells: Sequence[PageElement]) -> str | None:
    """
    テーブル行から曲名を抽出する.

    Args:
        cells: テーブルセルのリスト

    Returns:
        曲名、抽出に失敗した場合はNone
    """
    if len(cells) < 4:
        return None

    title_cell = cells[3]
    if not isinstance(title_cell, Tag):
        return None
    class_attr = title_cell.get("class")
    if class_attr is None or "clickable-row" not in class_attr:
        return None

    title_link = title_cell.find("a")
    if not title_link or not isinstance(title_link, Tag):
        return None

    return title_link.get_text(strip=True)


def _extract_duration(cells: Sequence[PageElement]) -> str | None:
    """
    テーブル行から曲の長さを抽出する.

    Args:
        cells: テーブルセルのリスト

    Returns:
        曲の長さ、抽出に失敗した場合はNone
    """
    if len(cells) < 5:
        return None

    duration_cell = cells[4]
    if not isinstance(duration_cell, Tag):
        return None
    class_attr = duration_cell.get("class")
    if class_attr is None or "clickable-row" not in class_attr:
        return None

    duration_link = duration_cell.find("a")
    if not duration_link or not isinstance(duration_link, Tag):
        return None

    return duration_link.get_text(strip=True)


def _extract_download_url(cells: Sequence[PageElement], netloc: str) -> str | None:
    """
    テーブル行からダウンロードURLを抽出する.

    Args:
        cells: テーブルセルのリスト
        netloc: ドメイン名

    Returns:
        ダウンロードURL、抽出に失敗した場合はNone
    """
    if len(cells) < 7:
        return None

    size_cell = cells[6]
    if not isinstance(size_cell, Tag):
        return None
    class_attr = size_cell.get("class")
    if class_attr is None or "clickable-row" not in class_attr:
        return None

    size_link = size_cell.find("a")
    if not size_link or not isinstance(size_link, Tag):
        return None
    href = size_link.get("href")
    if not href or not isinstance(href, str):
        return None

    # hrefが相対パスの場合、完全なURLに変換
    if not href.startswith("http"):
        href = f"https://{netloc}{href}"

    return href


def _create_track_from_download_url(
    disc: int, track: int, title: str, duration: str, download_url: str
) -> Track | None:
    """
    ダウンロードURLからトラック情報を作成する.

    Args:
        disc: ディスク番号
        track: トラック番号
        title: 曲名
        duration: 曲の長さ
        download_url: ダウンロードURL

    Returns:
        トラック情報、作成に失敗した場合はNone
    """
    try:
        # HTTPリクエストでHTMLコンテンツを取得
        sleep(random.uniform(0.5, 1.5))  # noqa: S311
        with httpx.Client(timeout=30.0) as client:
            response = client.get(download_url)
            response.raise_for_status()
            html_content = response.text

        track_url = extract_track_url(html_content)

        return Track(disc=disc, track=track, title=title, duration=duration, track_url=track_url)
    except Exception:
        return None


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
        if len(cells) < 7:
            continue

        # 各セルからデータを抽出
        disc = _extract_disc_number(cells)
        track_num = _extract_track_number(cells)
        title = _extract_title(cells)
        duration = _extract_duration(cells)
        download_url = _extract_download_url(cells, netloc)

        # 全ての必要な情報が抽出できた場合のみトラックを作成
        values: list[Any] = [disc, track_num, title, duration, download_url]
        if all(x is not None for x in values):
            # Noneチェック済みなのでキャスト
            track_info = _create_track_from_download_url(
                disc,  # type: ignore
                track_num,  # type: ignore
                title,  # type: ignore
                duration,  # type: ignore
                download_url,  # type: ignore
            )
            if track_info is not None:
                tracks.append(track_info)

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

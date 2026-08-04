"""ディレクトリ一括パック機能のテストモジュール."""

from pathlib import Path
from zipfile import ZipFile

import pytest
from PIL import Image

from moro.modules.common.utils import PackError, pack_directory


def _write_image(path: Path, color: tuple[int, int, int], mode: str = "RGB") -> None:
    """テスト用の画像ファイルを作成する."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fill = color if mode == "RGB" else (*color, 128)
    Image.new(mode, (10, 20), fill).save(path)


@pytest.mark.unit
class TestPackDirectoryZip:
    """zip 出力のテスト."""

    def test_flattens_nested_files_into_sequential_names(self, tmp_path: Path) -> None:
        """全階層のファイルが単一階層の連番として格納される."""
        target = tmp_path / "target"
        (target / "sub" / "deep").mkdir(parents=True)
        (target / "a.txt").write_text("a")
        (target / "sub" / "b.txt").write_text("b")
        (target / "sub" / "deep" / "c.txt").write_text("c")
        output = tmp_path / "out.zip"

        count = pack_directory(target, output)

        assert count == 3
        with ZipFile(output) as archive:
            assert archive.namelist() == ["1.txt", "2.txt", "3.txt"]
            assert archive.read("3.txt") == b"c"

    def test_keeps_original_extension(self, tmp_path: Path) -> None:
        """リネーム後も元の拡張子を保持する."""
        target = tmp_path / "target"
        target.mkdir()
        (target / "cover.png").write_bytes(b"png")
        (target / "note.txt").write_text("note")
        output = tmp_path / "out.zip"

        pack_directory(target, output)

        with ZipFile(output) as archive:
            assert archive.namelist() == ["1.png", "2.txt"]

    def test_numbers_entries_in_natural_order(self, tmp_path: Path) -> None:
        """連番は元ファイルの数値順に割り当てられる."""
        target = tmp_path / "target"
        target.mkdir()
        for name in ("10.txt", "2.txt", "1.txt"):
            (target / name).write_text(name)
        output = tmp_path / "out.zip"

        pack_directory(target, output)

        with ZipFile(output) as archive:
            assert archive.namelist() == ["1.txt", "2.txt", "3.txt"]
            assert [archive.read(name) for name in archive.namelist()] == [
                b"1.txt",
                b"2.txt",
                b"10.txt",
            ]

    def test_zero_pads_to_file_count_width(self, tmp_path: Path) -> None:
        """連番はファイル数の桁数でゼロ埋めされる."""
        target = tmp_path / "target"
        target.mkdir()
        for index in range(1, 11):
            (target / f"{index:02d}.txt").write_text(str(index))
        output = tmp_path / "out.zip"

        pack_directory(target, output)

        with ZipFile(output) as archive:
            assert archive.namelist()[0] == "01.txt"
            assert archive.namelist()[-1] == "10.txt"

    def test_excludes_output_inside_target(self, tmp_path: Path) -> None:
        """出力先が対象ディレクトリ配下でも自身を含めない."""
        target = tmp_path / "target"
        target.mkdir()
        (target / "a.txt").write_text("a")
        output = target / "out.zip"

        count = pack_directory(target, output)

        assert count == 1
        with ZipFile(output) as archive:
            assert archive.namelist() == ["1.txt"]

    def test_creates_missing_output_directory(self, tmp_path: Path) -> None:
        """出力先の親ディレクトリが無ければ作成する."""
        target = tmp_path / "target"
        target.mkdir()
        (target / "a.txt").write_text("a")
        output = tmp_path / "nested" / "out.zip"

        pack_directory(target, output)

        assert output.is_file()


@pytest.mark.unit
class TestPackDirectoryPdf:
    """pdf 出力のテスト."""

    def test_packs_all_images_as_pages(self, tmp_path: Path) -> None:
        """全階層の画像がページとして書き出される."""
        target = tmp_path / "target"
        _write_image(target / "2.png", (0, 255, 0))
        _write_image(target / "10.png", (0, 0, 255))
        _write_image(target / "sub" / "1.jpg", (255, 0, 0))
        output = tmp_path / "out.pdf"

        count = pack_directory(target, output)

        assert count == 3
        content = output.read_bytes()
        assert content.startswith(b"%PDF")
        assert b"/Count 3" in content

    def test_flattens_transparency(self, tmp_path: Path) -> None:
        """アルファ付き画像も RGB ページとして書き出せる."""
        target = tmp_path / "target"
        _write_image(target / "1.png", (255, 0, 0), mode="RGBA")
        output = tmp_path / "out.pdf"

        assert pack_directory(target, output) == 1

    def test_skips_non_image_files(self, tmp_path: Path) -> None:
        """画像以外のファイルはページにせず読み飛ばす."""
        target = tmp_path / "target"
        _write_image(target / "1.png", (255, 0, 0))
        (target / "note.txt").write_text("note")
        output = tmp_path / "out.pdf"

        assert pack_directory(target, output) == 1

    def test_raises_when_no_image_exists(self, tmp_path: Path) -> None:
        """画像が一つも無い場合はエラーになる."""
        target = tmp_path / "target"
        target.mkdir()
        (target / "note.txt").write_text("note")

        with pytest.raises(PackError, match="No image file"):
            pack_directory(target, tmp_path / "out.pdf")


@pytest.mark.unit
class TestPackDirectoryErrors:
    """入力検証のテスト."""

    def test_raises_on_unsupported_extension(self, tmp_path: Path) -> None:
        """Zip と pdf 以外の拡張子は拒否する."""
        target = tmp_path / "target"
        target.mkdir()
        (target / "a.txt").write_text("a")

        with pytest.raises(PackError, match="Unsupported output extension"):
            pack_directory(target, tmp_path / "out.tar")

    def test_raises_when_target_is_empty(self, tmp_path: Path) -> None:
        """対象ディレクトリが空の場合はエラーになる."""
        target = tmp_path / "target"
        (target / "empty").mkdir(parents=True)

        with pytest.raises(PackError, match="No files found"):
            pack_directory(target, tmp_path / "out.zip")

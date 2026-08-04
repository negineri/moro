"""Common utilities for the modules."""

import importlib
import inspect
import pkgutil
import re
import sys
from contextlib import ExitStack
from logging import getLogger
from pathlib import Path
from types import ModuleType
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

from moro.env import APP_NAME
from moro.modules.common.domain import PWScriptBase

_logger = getLogger(__name__)

#: PDF のページとして取り込める画像ファイルの拡張子
PDF_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"})


def generate_number_prefix(total_count: int, current_index: int) -> str:
    """
    Generates a zero-padded sequential prefix based on the total number of URLs.

    Args:
        total_count (int): The total number of URLs.
        current_index (int): The current index being processed (starting from 1).

    Returns:
        str: Zero-padded sequential prefix (e.g., "01_", "001_").

    Raises:
        ValueError: If total_count is less than or equal to 0, or if current_index is less than 1
            or greater than total_count.
    """
    if total_count <= 0:
        raise ValueError("total_count must be greater than 0")

    if current_index <= 0 or current_index > total_count:
        raise ValueError(
            "current_index must be greater than or equal to 1 and less than or equal to total_count"
        )

    # 必要な桁数を計算
    width = len(str(total_count))

    # ゼロ埋めされたプレフィックスを生成
    return f"{current_index:0{width}d}_"


class PWScriptLoadError(Exception):
    """Exception raised when a Playwright script fails to load."""


def iter_pwscript_classes(plugin_dirs: list[Path] | None = None) -> list[type[PWScriptBase]]:
    """
    Iterate over all classes in a module that inherit from PWScriptBase.

    Args:
        plugin_dirs: Additional directories holding user defined modules or packages.
            Every top level module and package in them is inspected.

    Returns:
        list[type]: A list of classes that inherit from PWScriptBase.

    Raises:
        PWScriptLoadError: If a package or one of its submodules cannot be imported.
    """
    modules: list[ModuleType] = []
    package_path = APP_NAME + ".plugins"
    modules.extend(_iter_modules(package_path))
    for plugin_dir in plugin_dirs or []:
        modules.extend(_iter_dir_modules(plugin_dir))

    classes: list[type[PWScriptBase]] = []
    seen: set[type[PWScriptBase]] = set()

    for module in modules:
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, PWScriptBase) or obj is PWScriptBase:
                continue
            if obj in seen:
                continue
            seen.add(obj)
            classes.append(obj)

    return classes


def _iter_dir_modules(plugin_dir: Path) -> list[ModuleType]:
    """
    Import every top level module and package found in a directory.

    The directory is appended to ``sys.path`` so that plugins can use absolute
    imports between their own modules. Installed packages take precedence over
    plugins with the same name.

    Args:
        plugin_dir: The directory to load modules from. Missing directories are skipped.

    Returns:
        list[ModuleType]: The imported modules and their submodules.

    Raises:
        PWScriptLoadError: If a module cannot be imported.
    """
    resolved = plugin_dir.expanduser().resolve()
    if not resolved.is_dir():
        _logger.warning("Plugin directory does not exist: %s", resolved)
        return []

    if str(resolved) not in sys.path:
        sys.path.append(str(resolved))

    modules: list[ModuleType] = []
    for name in _iter_top_level_names(resolved):
        module = _import_module(name)
        module_file = getattr(module, "__file__", None)
        if module_file is not None and resolved not in Path(module_file).parents:
            # 同名のインストール済みモジュールが優先された場合は読み込まない
            _logger.warning(
                "Skipping plugin '%s' in %s: shadowed by %s", name, resolved, module_file
            )
            continue
        modules.extend(_iter_modules(name))

    return modules


def _iter_top_level_names(plugin_dir: Path) -> list[str]:
    """
    Collect importable top level module and package names in a directory.

    Args:
        plugin_dir: The directory to inspect.

    Returns:
        list[str]: Sorted module names, excluding private and dunder entries.
    """
    names = {
        module_info.name
        for module_info in pkgutil.iter_modules([str(plugin_dir)])
        if not module_info.name.startswith("_")
    }
    return sorted(names)


def _iter_modules(package_path: str) -> list[ModuleType]:
    """
    Import a package (or module) and all of its submodules.

    Args:
        package_path: The package path to import. example: "moro.scripts"

    Returns:
        list[ModuleType]: The imported package followed by all of its submodules.

    Raises:
        PWScriptLoadError: If the package or one of its submodules cannot be imported.
    """
    modules = [_import_module(package_path)]

    package_paths = getattr(modules[0], "__path__", None)
    if package_paths is None:  # 単一モジュールの場合はサブモジュールを持たない
        return modules

    def _on_error(name: str) -> None:
        raise PWScriptLoadError(f"Failed to import module '{name}'")

    for module_info in pkgutil.walk_packages(
        package_paths, prefix=f"{package_path}.", onerror=_on_error
    ):
        modules.append(_import_module(module_info.name))

    return modules


def _import_module(name: str) -> ModuleType:
    """
    Import a module and wrap any failure in PWScriptLoadError.

    Args:
        name: The fully qualified module name.

    Returns:
        ModuleType: The imported module.

    Raises:
        PWScriptLoadError: If the module cannot be imported.
    """
    try:
        return importlib.import_module(name)
    except Exception as e:
        raise PWScriptLoadError(f"Failed to import module '{name}'") from e


class PackError(Exception):
    """Exception raised when files cannot be packed into a single file."""


def pack_directory(target: Path, output: Path) -> int:
    """
    Pack every file under a directory into a single archive or document.

    The output format is chosen from the output file extension. ``.zip`` flattens the
    directory structure and renames every entry to a sequential number, ``.pdf`` renders
    each image file as a page.

    Args:
        target: The directory whose files are packed. Nested directories are included.
        output: The destination file. Its suffix must be ``.zip`` or ``.pdf``.

    Returns:
        int: The number of files written into the output.

    Raises:
        PackError: If the extension is unsupported, or no packable file is found.
    """
    suffix = output.suffix.lower()
    if suffix not in {".zip", ".pdf"}:
        raise PackError(f"Unsupported output extension: '{output.suffix}'. Use '.zip' or '.pdf'.")

    target = target.expanduser().resolve()
    output = output.expanduser().resolve()
    files = _collect_files(target, exclude=output)
    if not files:
        raise PackError(f"No files found under '{target}'")

    output.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".zip":
        return _pack_zip(files, target, output)
    return _pack_pdf(files, target, output)


def _collect_files(target: Path, exclude: Path) -> list[Path]:
    """
    Collect every file under a directory in natural sort order.

    Args:
        target: The directory to walk recursively.
        exclude: A file to skip, typically the output file placed inside the target.

    Returns:
        list[Path]: The collected files, sorted by their path relative to the target.
    """
    files = [
        path
        for path in target.rglob("*")
        if path.is_file() and path.resolve() != exclude  # 出力先が対象配下にある場合は除外する
    ]
    return sorted(files, key=lambda path: _natural_key(path.relative_to(target)))


def _natural_key(relative_path: Path) -> list[list[tuple[int, int, str]]]:
    """
    Build a sort key that orders embedded numbers by value instead of by character.

    Args:
        relative_path: The path to build the key from.

    Returns:
        list: A per path component key, comparable with other keys of the same shape.
    """
    return [
        [
            (0, int(chunk), "") if chunk.isdigit() else (1, 0, chunk)
            for chunk in re.split(r"(\d+)", part)
            if chunk
        ]
        for part in relative_path.parts
    ]


def _pack_zip(files: list[Path], target: Path, output: Path) -> int:
    """
    Write files into a flat zip archive, renaming every entry to a sequential number.

    The directory structure is dropped: entries are named ``001.png`` style, numbered in
    the order the files were collected and zero padded to the width of the file count.
    The original extension is kept.

    Args:
        files: The files to archive.
        target: The directory the original file names are relative to, used for logging.
        output: The destination zip file.

    Returns:
        int: The number of archived files.
    """
    images = [file for file in files if file.suffix.lower() in PDF_IMAGE_SUFFIXES]
    for file in files:
        if file not in images:
            _logger.warning("Skipping non image file: %s", file.relative_to(target))
    if not images:
        raise PackError(f"No image file found under '{target}'")
    width = len(str(len(images)))
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for index, file in enumerate(images, start=1):
            arcname = f"{index:0{width}d}{file.suffix}"
            _logger.debug("Adding %s as %s", file.relative_to(target), arcname)
            archive.write(file, arcname=arcname)
    return len(images)


def _pack_pdf(files: list[Path], target: Path, output: Path) -> int:
    """
    Write image files into a single PDF, one page per image.

    Non image files cannot be rendered as a page and are skipped with a warning.

    Args:
        files: The files to render. Only images listed in PDF_IMAGE_SUFFIXES are used.
        target: The directory the file names are relative to, used for logging.
        output: The destination pdf file.

    Returns:
        int: The number of pages written.

    Raises:
        PackError: If no image file is found, or an image cannot be read.
    """
    images = [file for file in files if file.suffix.lower() in PDF_IMAGE_SUFFIXES]
    for file in files:
        if file not in images:
            _logger.warning("Skipping non image file: %s", file.relative_to(target))
    if not images:
        raise PackError(f"No image file found under '{target}'")

    with ExitStack() as stack:
        try:
            pages = [_load_pdf_page(stack, file) for file in images]
        except OSError as e:
            raise PackError(f"Failed to read image: {e}") from e
        pages[0].save(output, "PDF", save_all=True, append_images=pages[1:])
    return len(pages)


def _load_pdf_page(stack: ExitStack, file: Path) -> Image.Image:
    """
    Load an image as an RGB page, flattening transparency onto white.

    Args:
        stack: The exit stack closing the opened images once the PDF is written.
        file: The image file to load.

    Returns:
        Image.Image: The image converted to a PDF friendly RGB page.
    """
    image = stack.enter_context(Image.open(file))
    if image.mode == "RGB":
        return image

    rgba = image.convert("RGBA")
    page = Image.new("RGB", rgba.size, (255, 255, 255))
    page.paste(rgba, mask=rgba.getchannel("A"))
    return stack.enter_context(page)

"""Common utilities for the modules."""

import importlib
import inspect
import pkgutil
import sys
from logging import getLogger
from pathlib import Path
from types import ModuleType

from moro.env import APP_NAME
from moro.modules.common.domain import PWScriptBase

_logger = getLogger(__name__)


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

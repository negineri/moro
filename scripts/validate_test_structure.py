#!/usr/bin/env python3
"""テスト構造バリデーションスクリプト"""

import ast
import sys
from pathlib import Path


def check_module_independence() -> bool:
    """各モジュールテストの独立性チェック"""
    violations = []

    unit_modules_path = Path("tests/unit/modules")
    if not unit_modules_path.exists():
        print("✅ モジュール独立性: tests/unit/modules が存在しないため、チェックスキップ")  # noqa: T201
        return True

    for module_dir in unit_modules_path.iterdir():
        if not module_dir.is_dir():
            continue

        module_name = module_dir.name
        for test_file in module_dir.glob("**/*.py"):
            violations.extend(_check_file_imports(test_file, module_name))

    if violations:
        print("❌ モジュール独立性違反:", file=sys.stderr)  # noqa: T201
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)  # noqa: T201
        return False

    print("✅ モジュール独立性: 適合")  # noqa: T201
    return True


def _check_file_imports(file_path: Path, module_name: str) -> list[str]:
    """ファイルのimport文をチェック"""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except Exception as e:
        return [f"{file_path}: Parse error - {e}"]

    violations = []
    forbidden_patterns = [
        f"moro.modules.{other}"
        for other in ["epgstation", "fantia", "todo"]
        if other != module_name
    ]

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_name = _get_import_name(node)
            for pattern in forbidden_patterns:
                if import_name and import_name.startswith(pattern):
                    violations.append(f"{file_path}: 禁止import - {import_name}")

    return violations


def _get_import_name(node: ast.Import | ast.ImportFrom) -> str:
    """import文から名前を抽出"""
    if isinstance(node, ast.Import):
        return node.names[0].name if node.names else ""
    if isinstance(node, ast.ImportFrom):
        return node.module or ""
    return ""


if __name__ == "__main__":
    success = check_module_independence()
    sys.exit(0 if success else 1)

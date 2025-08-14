#!/usr/bin/env python3
"""test_fantia.pyの価値分析スクリプト"""

import ast
import re
from pathlib import Path
from typing import NamedTuple


class TestAnalysis(NamedTuple):
    """テスト分析結果を格納するデータクラス."""

    name: str
    line_count: int
    mock_count: int
    category: str  # domain, usecase, infrastructure, integration, e2e
    value_score: int  # 1-5 (5=最高価値)
    keep_decision: str  # keep, refactor, delete


def analyze_fantia_tests() -> list[TestAnalysis]:
    """既存テストの詳細分析"""
    test_file = Path("tests/modules/test_fantia.py")
    if not test_file.exists():
        print("❌ test_fantia.py が見つかりません")  # noqa: T201
        return []

    content = test_file.read_text()
    tree = ast.parse(content)

    analyses = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            analysis = _analyze_test_function(node, content)
            analyses.append(analysis)

    return analyses


def _analyze_test_function(node: ast.FunctionDef, content: str) -> TestAnalysis:
    """個別テスト関数の分析"""
    # テスト関数のソース抽出
    lines = content.split("\n")
    start_line = node.lineno - 1
    end_line = _find_function_end(node, lines, start_line)
    test_source = "\n".join(lines[start_line:end_line])

    # Mock使用回数カウント
    mock_count = len(re.findall(r"Mock|mock|patch", test_source))

    # カテゴリ分類
    category = _categorize_test(node.name, test_source)

    # 価値評価
    value_score = _evaluate_test_value(test_source, category, mock_count)

    # 保持判断
    keep_decision = _decide_keep_or_delete(category, value_score, mock_count)

    return TestAnalysis(
        name=node.name,
        line_count=end_line - start_line,
        mock_count=mock_count,
        category=category,
        value_score=value_score,
        keep_decision=keep_decision,
    )


def _find_function_end(node: ast.FunctionDef, lines: list[str], start: int) -> int:
    """関数の終了行を推定"""
    # 次の関数またはクラス定義を探す
    for i in range(start + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith("def ") or line.startswith("class ") or line.startswith("@"):
            return i
    return len(lines)


def _categorize_test(test_name: str, source: str) -> str:
    """テストのカテゴリ分類"""
    # ドメインロジック系
    if any(
        keyword in test_name.lower()
        for keyword in ["validate", "format", "parse", "domain", "entity"]
    ):
        return "domain"

    # インフラ系（HTTP、ファイルI/O）
    if any(keyword in source for keyword in ["httpx", "requests", "pathlib", "open(", "write"]):
        return "infrastructure"

    # 統合テスト系（複数レイヤー）
    if source.count("mock") > 3:
        return "integration"

    # E2E系
    if any(keyword in source for keyword in ["selenium", "webdriver", "click"]):
        return "e2e"

    # ユースケース系（デフォルト）
    return "usecase"


def _evaluate_test_value(source: str, category: str, mock_count: int) -> int:
    """テストの価値評価 (1-5)"""
    score = 3  # ベース

    # カテゴリ別調整
    if category == "domain":
        score += 1  # ドメインロジックは価値が高い
    elif category == "infrastructure":
        score -= 1  # インフラテストは価値が低め

    # Mock数による調整
    if mock_count > 5:
        score -= 1  # 過度なMockは価値を下げる
    elif mock_count == 0:
        score += 1  # Mock無しは価値が高い

    # ソースコード品質による調整
    if len(source) > 500:
        score -= 1  # 巨大テストは価値が低い
    if "TODO" in source or "FIXME" in source:
        score -= 1  # 未完成テスト

    return max(1, min(5, score))


def _decide_keep_or_delete(category: str, value_score: int, mock_count: int) -> str:
    """保持・削除判断"""
    # 高価値テストは保持
    if value_score >= 4:
        return "keep"

    # ドメインテストは基本保持
    if category == "domain" and value_score >= 3:
        return "keep"

    # 過度なMock使用は削除
    if mock_count > 10:
        return "delete"

    # 低価値テストは削除
    if value_score <= 2:
        return "delete"

    # 中程度は要リファクタ
    return "refactor"


def generate_analysis_report(analyses: list[TestAnalysis]) -> str:
    """分析レポート生成"""
    keep_tests = [a for a in analyses if a.keep_decision == "keep"]
    refactor_tests = [a for a in analyses if a.keep_decision == "refactor"]
    delete_tests = [a for a in analyses if a.keep_decision == "delete"]

    total_lines = sum(a.line_count for a in analyses)
    keep_lines = sum(a.line_count for a in keep_tests)

    return f"""# test_fantia.py 分析レポート

## 概要
- 総テスト数: {len(analyses)}
- 総行数: {total_lines}
- 保持対象: {len(keep_tests)} テスト ({keep_lines} 行)
- リファクタ対象: {len(refactor_tests)} テスト
- 削除対象: {len(delete_tests)} テスト

## カテゴリ別分析
{_category_summary(analyses)}

## 削除対象テスト詳細 ({len(delete_tests)} テスト)
{_format_test_list(delete_tests)}

## リファクタ対象テスト詳細 ({len(refactor_tests)} テスト)
{_format_test_list(refactor_tests)}

## 保持対象テスト詳細 ({len(keep_tests)} テスト)
{_format_test_list(keep_tests)}
"""


def _category_summary(analyses: list[TestAnalysis]) -> str:
    """カテゴリ別サマリー"""
    categories = {}
    for analysis in analyses:
        cat = analysis.category
        if cat not in categories:
            categories[cat] = {"count": 0, "lines": 0, "keep": 0, "delete": 0, "refactor": 0}
        categories[cat]["count"] += 1
        categories[cat]["lines"] += analysis.line_count
        categories[cat][analysis.keep_decision] += 1

    summary = ""
    for cat, stats in categories.items():
        summary += f"- {cat}: {stats['count']} テスト, {stats['lines']} 行 "
        summary += (
            f"(保持:{stats['keep']}, リファクタ:{stats['refactor']}, 削除:{stats['delete']})\n"
        )

    return summary


def _format_test_list(tests: list[TestAnalysis]) -> str:
    """テストリストのフォーマット"""
    if not tests:
        return "なし"

    result = ""
    for test in sorted(tests, key=lambda x: x.value_score, reverse=True):
        result += f"- {test.name} ({test.line_count}行, Mock:{test.mock_count}, "
        result += f"価値:{test.value_score}, {test.category})\n"

    return result


if __name__ == "__main__":
    analyses = analyze_fantia_tests()
    report = generate_analysis_report(analyses)

    with Path("fantia_test_analysis.md").open("w") as f:
        f.write(report)

    print("✅ 分析完了: fantia_test_analysis.md")  # noqa: T201
    print(f"総テスト数: {len(analyses)}")  # noqa: T201
    print(f"保持対象: {len([a for a in analyses if a.keep_decision == 'keep'])}")  # noqa: T201
    print(f"削除対象: {len([a for a in analyses if a.keep_decision == 'delete'])}")  # noqa: T201

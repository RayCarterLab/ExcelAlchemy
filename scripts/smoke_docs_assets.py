"""Validate documentation entry points and generated showcase assets."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / 'docs'
ASSET_DIR = ROOT / 'files' / 'example-outputs'
BRANCH_PINNED_LINK_PATTERN = re.compile(
    r'https://github\.com/RayCarterLab/ExcelAlchemy/blob/main/'
    r'|https://raw\.githubusercontent\.com/RayCarterLab/ExcelAlchemy/main/'
)

REQUIRED_DOC_CHECKS: dict[Path, tuple[str, ...]] = {
    ROOT / 'README.md': (
        'Choosing ExcelAlchemy',
        'docs/tool-comparison.md',
    ),
    DOCS_DIR / 'result-objects.md': (
        'ImportResult',
        'CellErrorMap',
        'RowIssueMap',
        'docs/api-response-cookbook.md',
        'display_message',
    ),
    DOCS_DIR / 'integration-roadmap.md': (
        'If You Are Integrating ExcelAlchemy For The First Time',
        'If You Are Building A Backend API',
        'If You Are Building Frontend Error Displays',
    ),
    DOCS_DIR / 'limitations.md': (
        'Formula Cells And Cached Values',
        'server-side',
        'round-trip',
        'Microsoft Excel',
    ),
    DOCS_DIR / 'performance.md': (
        'Common Bottlenecks',
        'WorksheetTable',
        'Operational Guardrails For Backend Services',
        'background job',
    ),
    DOCS_DIR / 'tool-comparison.md': (
        'Summary Table',
        'Plain `openpyxl` Scripting',
        'Excel Automation Tools',
        'Generic Dataframe / Schema Validation Approaches',
    ),
    DOCS_DIR / 'examples-showcase.md': (
        'files/example-outputs/employee-import-workflow.txt',
        'files/example-outputs/create-or-update-import.txt',
        'files/example-outputs/export-workflow.txt',
        'files/example-outputs/fastapi-reference.txt',
    ),
}

REQUIRED_ASSETS = (
    'annotated-schema.txt',
    'employee-import-workflow.txt',
    'create-or-update-import.txt',
    'date-and-range-fields.txt',
    'selection-fields.txt',
    'custom-storage.txt',
    'export-workflow.txt',
    'fastapi-reference.txt',
    'import-failure-api-payload.json',
)


def _assert_doc_contains(path: Path, fragments: tuple[str, ...]) -> None:
    content = path.read_text(encoding='utf-8')
    missing = [fragment for fragment in fragments if fragment not in content]
    if missing:
        raise AssertionError(f'{path.relative_to(ROOT)} is missing expected fragments: {missing}')


def _assert_asset_exists(filename: str) -> None:
    path = ASSET_DIR / filename
    if not path.exists():
        raise AssertionError(f'Missing generated asset: {path.relative_to(ROOT)}')
    if not path.read_text(encoding='utf-8').strip():
        raise AssertionError(f'Generated asset is empty: {path.relative_to(ROOT)}')


def _assert_repo_markdown_links_are_branch_agnostic() -> None:
    markdown_files = [
        ROOT / 'README.md',
        ROOT / 'README_cn.md',
        ROOT / 'MIGRATIONS.md',
        *DOCS_DIR.rglob('*.md'),
        *(ROOT / 'examples').rglob('*.md'),
    ]
    for path in markdown_files:
        content = path.read_text(encoding='utf-8')
        if BRANCH_PINNED_LINK_PATTERN.search(content):
            raise AssertionError(
                f'{path.relative_to(ROOT)} still contains a branch-pinned GitHub link; '
                'prefer relative links so docs work on non-main branches.'
            )


def _assert_pypi_readme_links_target_main() -> None:
    content = (ROOT / 'README-pypi.md').read_text(encoding='utf-8')
    required_fragments = (
        'https://github.com/RayCarterLab/ExcelAlchemy/blob/main/README.md',
        'https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md',
        'https://raw.githubusercontent.com/RayCarterLab/ExcelAlchemy/main/images/portfolio-template-en.png',
    )
    missing = [fragment for fragment in required_fragments if fragment not in content]
    if missing:
        raise AssertionError(f'README-pypi.md is missing expected main-branch links: {missing}')


def main() -> None:
    for path, fragments in REQUIRED_DOC_CHECKS.items():
        _assert_doc_contains(path, fragments)
        print(f'Documentation smoke passed: {path.relative_to(ROOT)}')

    _assert_repo_markdown_links_are_branch_agnostic()
    print('Documentation smoke passed: branch-agnostic Markdown links')

    _assert_pypi_readme_links_target_main()
    print('Documentation smoke passed: README-pypi links target main')

    for filename in REQUIRED_ASSETS:
        _assert_asset_exists(filename)
        print(f'Asset smoke passed: files/example-outputs/{filename}')


if __name__ == '__main__':
    main()

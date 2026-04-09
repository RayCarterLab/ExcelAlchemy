"""Validate documentation entry points and generated showcase assets."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / 'docs'
ASSET_DIR = ROOT / 'files' / 'example-outputs'

REQUIRED_DOC_CHECKS: dict[Path, tuple[str, ...]] = {
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


def main() -> None:
    for path, fragments in REQUIRED_DOC_CHECKS.items():
        _assert_doc_contains(path, fragments)
        print(f'Documentation smoke passed: {path.relative_to(ROOT)}')

    for filename in REQUIRED_ASSETS:
        _assert_asset_exists(filename)
        print(f'Asset smoke passed: files/example-outputs/{filename}')


if __name__ == '__main__':
    main()

"""Verify a stable import-failure API payload snapshot for release smoke."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / 'files' / 'example-outputs' / 'import-failure-api-payload.json'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def _build_snapshot_payload() -> dict[str, object]:
    from scripts.smoke_package import (
        InMemorySmokeStorage,
        SmokeImporter,
        _build_invalid_import_fixture,
        _create_employee,
    )

    from excelalchemy import ExcelAlchemy, ImporterConfig

    storage = InMemorySmokeStorage()
    importer = ExcelAlchemy(
        ImporterConfig.for_create(
            SmokeImporter,
            creator=_create_employee,
            storage=storage,
            locale='en',
        )
    )
    template = importer.download_template_artifact(filename='smoke-template.xlsx')
    _build_invalid_import_fixture(storage, template.as_bytes())
    result = await importer.import_data('smoke-invalid-input.xlsx', 'smoke-invalid-result.xlsx')
    return {
        'result': result.to_api_payload(),
        'cell_errors': importer.cell_error_map.to_api_payload(),
        'row_errors': importer.row_error_map.to_api_payload(),
    }


def _normalize(payload: dict[str, object]) -> dict[str, object]:
    return json.loads(json.dumps(payload, sort_keys=True))


async def main() -> None:
    actual = _normalize(await _build_snapshot_payload())
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding='utf-8'))
    if actual != expected:
        raise AssertionError('Import-failure API payload snapshot does not match the expected release snapshot.')
    print(f'API payload snapshot smoke passed: {SNAPSHOT_PATH.name}')


if __name__ == '__main__':
    asyncio.run(main())

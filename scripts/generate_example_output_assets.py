"""Generate fixed example output assets for README and documentation pages."""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import importlib.util
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / 'examples'
OUTPUT_DIR = ROOT / 'files' / 'example-outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXAMPLE_ASSETS: dict[str, str] = {
    'annotated_schema.py': 'annotated-schema.txt',
    'employee_import_workflow.py': 'employee-import-workflow.txt',
    'create_or_update_import.py': 'create-or-update-import.txt',
    'date_and_range_fields.py': 'date-and-range-fields.txt',
    'selection_fields.py': 'selection-fields.txt',
    'custom_storage.py': 'custom-storage.txt',
    'export_workflow.py': 'export-workflow.txt',
}

MODULE_ASSETS: dict[str, str] = {
    'examples.fastapi_reference.app': 'fastapi-reference.txt',
}


def _load_example_module(module_name: str, filename: str):
    module_path = EXAMPLES_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Could not load example module: {filename}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_example(filename: str) -> str:
    module_name = f'example_asset_{filename.removesuffix(".py").replace("-", "_")}'
    module = _load_example_module(module_name, filename)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()
    return buffer.getvalue().strip()


def _run_module_example(module_name: str) -> str:
    module = importlib.import_module(module_name)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()
    return buffer.getvalue().strip()


async def _build_import_failure_api_payload() -> dict[str, object]:
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


def main() -> None:
    for filename, output_name in EXAMPLE_ASSETS.items():
        output = _run_example(filename)
        output_path = OUTPUT_DIR / output_name
        output_path.write_text(f'{output}\n', encoding='utf-8')
        print(f'Generated example output: {output_path}')

    for module_name, output_name in MODULE_ASSETS.items():
        output = _run_module_example(module_name)
        output_path = OUTPUT_DIR / output_name
        output_path.write_text(f'{output}\n', encoding='utf-8')
        print(f'Generated example output: {output_path}')

    payload = asyncio.run(_build_import_failure_api_payload())
    payload_path = OUTPUT_DIR / 'import-failure-api-payload.json'
    payload_path.write_text(f'{json.dumps(payload, indent=2, sort_keys=True)}\n', encoding='utf-8')
    print(f'Generated example output: {payload_path}')


if __name__ == '__main__':
    main()

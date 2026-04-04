"""Smoke-test representative repository examples."""

from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / 'examples'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_EXAMPLES: dict[str, tuple[str, ...]] = {
    'annotated_schema.py': ('Generated template:', 'employee-template.xlsx'),
    'employee_import_workflow.py': ('Employee import workflow completed', 'Success rows: 1'),
    'create_or_update_import.py': ('Create-or-update import workflow completed', 'Updated rows: 1'),
    'date_and_range_fields.py': ('Generated template:', 'compensation-template.xlsx'),
    'selection_fields.py': ('Generated template:', 'selection-fields-template.xlsx'),
    'custom_storage.py': ('memory://employees.xlsx', 'Uploaded bytes:'),
    'export_workflow.py': ('Export workflow completed', 'Upload URL: memory://employees-export-upload.xlsx'),
}

OPTIONAL_EXAMPLES: dict[str, tuple[tuple[str, bool], tuple[str, ...]]] = {
    'fastapi_upload.py': (('fastapi', True), ('FastAPI upload example completed', '/employee-imports')),
    'minio_storage.py': (('minio', True), ('Built gateway: MinioStorageGateway', 'Uses built-in Minio path: True')),
}

REQUIRED_MODULE_EXAMPLES: dict[str, tuple[str, ...]] = {
    'examples.fastapi_reference.app': ('FastAPI reference project completed', '/employee-imports'),
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
    module_name = f'smoke_example_{filename.removesuffix(".py").replace("-", "_")}'
    module = _load_example_module(module_name, filename)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()
    return buffer.getvalue()


def _dependency_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _run_module_example(module_name: str) -> str:
    module = importlib.import_module(module_name)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()
    return buffer.getvalue()


def _assert_example_output(filename: str, output: str, required_fragments: tuple[str, ...]) -> None:
    missing = [fragment for fragment in required_fragments if fragment not in output]
    if missing:
        raise AssertionError(f'Example {filename} did not produce expected output fragments: {missing}')


def main() -> None:
    for filename, required_fragments in REQUIRED_EXAMPLES.items():
        output = _run_example(filename)
        _assert_example_output(filename, output, required_fragments)
        print(f'Smoke passed: {filename}')

    for filename, ((dependency_name, should_exist), required_fragments) in OPTIONAL_EXAMPLES.items():
        available = _dependency_available(dependency_name)
        if should_exist and not available:
            print(f'Skipped optional example: {filename} ({dependency_name} is not installed)')
            continue
        output = _run_example(filename)
        _assert_example_output(filename, output, required_fragments)
        print(f'Smoke passed: {filename}')

    for module_name, required_fragments in REQUIRED_MODULE_EXAMPLES.items():
        output = _run_module_example(module_name)
        _assert_example_output(module_name, output, required_fragments)
        print(f'Smoke passed: {module_name}')


if __name__ == '__main__':
    main()

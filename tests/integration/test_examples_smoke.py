from __future__ import annotations

import contextlib
import importlib
import importlib.util
import io
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / 'examples'
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_example_module(module_name: str, filename: str):
    module_path = EXAMPLES_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_annotated_schema_example_main_generates_template_output() -> None:
    module = _load_example_module('example_annotated_schema', 'annotated_schema.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'Generated template:' in output
    assert 'employee-template.xlsx' in output


def test_custom_storage_example_main_uploads_to_memory_storage() -> None:
    module = _load_example_module('example_custom_storage', 'custom_storage.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'memory://employees.xlsx' in output
    assert 'Uploaded bytes:' in output


def test_employee_import_workflow_example_main_runs_end_to_end() -> None:
    module = _load_example_module('example_employee_import_workflow', 'employee_import_workflow.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'Employee import workflow completed' in output
    assert 'Success rows: 1' in output
    assert 'Failed rows: 0' in output


def test_create_or_update_import_example_main_runs_end_to_end() -> None:
    module = _load_example_module('example_create_or_update_import', 'create_or_update_import.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'Create-or-update import workflow completed' in output
    assert 'Success rows: 2' in output
    assert 'Failed rows: 0' in output
    assert 'Created rows: 1' in output
    assert 'Updated rows: 1' in output


def test_date_and_range_fields_example_main_generates_template_output() -> None:
    module = _load_example_module('example_date_and_range_fields', 'date_and_range_fields.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'Generated template:' in output
    assert 'compensation-template.xlsx' in output


def test_selection_fields_example_main_generates_template_output() -> None:
    module = _load_example_module('example_selection_fields', 'selection_fields.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'Generated template:' in output
    assert 'selection-fields-template.xlsx' in output


def test_export_workflow_example_main_runs_end_to_end() -> None:
    module = _load_example_module('example_export_workflow', 'export_workflow.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'Export workflow completed' in output
    assert 'Artifact filename: employees-export.xlsx' in output
    assert 'Upload URL: memory://employees-export-upload.xlsx' in output


def test_fastapi_example_source_compiles() -> None:
    source = (EXAMPLES_DIR / 'fastapi_upload.py').read_text(encoding='utf-8')
    compile(source, str(EXAMPLES_DIR / 'fastapi_upload.py'), 'exec')


def test_fastapi_reference_example_sources_compile() -> None:
    package_dir = EXAMPLES_DIR / 'fastapi_reference'
    for filename in ('models.py', 'storage.py', 'services.py', 'app.py'):
        source = (package_dir / filename).read_text(encoding='utf-8')
        compile(source, str(package_dir / filename), 'exec')


@pytest.mark.skipif(importlib.util.find_spec('fastapi') is None, reason='fastapi is not installed')
def test_fastapi_example_main_runs_when_optional_dependency_is_available() -> None:
    module = _load_example_module('example_fastapi_upload_main', 'fastapi_upload.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'FastAPI upload example completed' in output
    assert 'Success rows: 1' in output
    assert '/employee-template.xlsx' in output
    assert '/employee-imports' in output


def test_fastapi_reference_project_main_runs_when_optional_dependency_is_available() -> None:
    module = importlib.import_module('examples.fastapi_reference.app')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'FastAPI reference project completed' in output
    assert 'Success rows: 1' in output
    assert '/employee-template.xlsx' in output
    assert '/employee-imports' in output


@pytest.mark.skipif(importlib.util.find_spec('minio') is None, reason='minio is not installed')
def test_minio_storage_example_main_builds_gateway() -> None:
    module = _load_example_module('example_minio_storage', 'minio_storage.py')

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        module.main()

    output = buffer.getvalue()
    assert 'Built gateway: MinioStorageGateway' in output
    assert 'Uses built-in Minio path: True' in output
    assert 'Gateway type check: True' in output


@pytest.mark.skipif(importlib.util.find_spec('fastapi') is None, reason='fastapi is not installed')
def test_fastapi_example_module_imports_when_optional_dependency_is_available() -> None:
    module = _load_example_module('example_fastapi_upload', 'fastapi_upload.py')
    assert module.app is not None
    assert module.create_app is not None
    assert module.import_employees_from_upload is not None


@pytest.mark.skipif(
    importlib.util.find_spec('fastapi') is None or importlib.util.find_spec('httpx') is None,
    reason='fastapi/httpx is not installed',
)
def test_fastapi_example_endpoints_work_when_optional_dependencies_are_available() -> None:
    from openpyxl import load_workbook

    module = _load_example_module('example_fastapi_upload_client', 'fastapi_upload.py')
    testclient_module = importlib.import_module('fastapi.testclient')
    TestClient = testclient_module.TestClient

    client = TestClient(module.create_app())
    template_response = client.get('/employee-template.xlsx')
    assert template_response.status_code == 200

    workbook = load_workbook(io.BytesIO(template_response.content))
    try:
        worksheet = workbook['Sheet1']
        worksheet['A3'] = 'TaylorChen'
        worksheet['B3'] = '32'
        buffer = io.BytesIO()
        workbook.save(buffer)
        upload_bytes = buffer.getvalue()
    finally:
        workbook.close()

    import_response = client.post(
        '/employee-imports',
        files={
            'file': (
                'employee-import.xlsx',
                upload_bytes,
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        },
    )
    assert import_response.status_code == 200
    payload = import_response.json()
    assert payload['result']['result'] == 'SUCCESS'
    assert payload['created_rows'] == 1
    assert payload['uploaded_artifacts'] == ['employee-import-result.xlsx']


@pytest.mark.skipif(
    importlib.util.find_spec('fastapi') is None or importlib.util.find_spec('httpx') is None,
    reason='fastapi/httpx is not installed',
)
def test_fastapi_reference_project_endpoints_work_when_optional_dependencies_are_available() -> None:
    module = importlib.import_module('examples.fastapi_reference.app')
    testclient_module = importlib.import_module('fastapi.testclient')
    TestClient = testclient_module.TestClient

    client = TestClient(module.create_app())
    template_response = client.get('/employee-template.xlsx')
    assert template_response.status_code == 200

    import_service_module = importlib.import_module('examples.fastapi_reference.services')
    upload_bytes = import_service_module.build_demo_upload(template_response.content)

    import_response = client.post(
        '/employee-imports',
        files={
            'file': (
                'employee-import.xlsx',
                upload_bytes,
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        },
    )
    assert import_response.status_code == 200
    payload = import_response.json()
    assert payload['result']['result'] == 'SUCCESS'
    assert payload['created_rows'] == 1
    assert payload['uploaded_artifacts'] == ['employee-import-result.xlsx']

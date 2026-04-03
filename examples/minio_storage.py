"""Built-in Minio storage example for the current 2.x line."""

from minio import Minio
from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, FieldMeta, ImporterConfig, Number, String
from excelalchemy.core.storage import build_storage_gateway
from excelalchemy.core.storage_minio import MinioStorageGateway


class EmployeeImporter(BaseModel):
    full_name: String = FieldMeta(label='Full name', order=1)
    age: Number = FieldMeta(label='Age', order=2)


def main() -> None:
    minio_client = Minio(
        'localhost:9000',
        access_key='minioadmin',
        secret_key='minioadmin',
        secure=False,
    )
    config = ImporterConfig.for_create(
        EmployeeImporter,
        creator=lambda row, context: row,
        minio=minio_client,
        bucket_name='excel-files',
        locale='en',
    )

    gateway = build_storage_gateway(config)
    alchemy = ExcelAlchemy(config)
    template = alchemy.download_template_artifact(filename='employee-template.xlsx')

    print(f'Built gateway: {type(gateway).__name__}')
    print(f'Uses built-in Minio path: {config.storage_options.uses_legacy_minio_path}')
    print(f'Template bytes: {len(template.as_bytes())}')
    print(f'Gateway type check: {isinstance(gateway, MinioStorageGateway)}')


if __name__ == '__main__':
    main()

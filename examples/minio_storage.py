"""Explicit Minio storage example."""

from typing import Annotated

from minio import Minio
from pydantic import BaseModel

from excelalchemy import ExcelAlchemy, ExcelColumn, ImporterConfig
from excelalchemy.storage.gateway import build_storage_gateway
from excelalchemy.storage.minio import MinioStorageGateway


class EmployeeImporter(BaseModel):
    full_name: Annotated[str, ExcelColumn(label='Full name', order=1)]
    age: Annotated[float, ExcelColumn(label='Age', order=2)]


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
        storage=MinioStorageGateway(minio_client, bucket_name='excel-files'),
        locale='en',
    )

    gateway = build_storage_gateway(config)
    alchemy = ExcelAlchemy(config)
    template = alchemy.download_template_artifact(filename='employee-template.xlsx')

    print(f'Built gateway: {type(gateway).__name__}')
    print(f'Uses explicit storage path: {config.storage_options.has_storage}')
    print(f'Template bytes: {len(template.as_bytes())}')
    print(f'Gateway type check: {isinstance(gateway, MinioStorageGateway)}')


if __name__ == '__main__':
    main()

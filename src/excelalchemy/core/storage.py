"""Storage adapters used by ExcelAlchemy to read and upload workbooks."""

from os import PathLike
from typing import BinaryIO, cast

import pandas
from pandas import DataFrame

from excelalchemy.exc import ConfigError
from excelalchemy.types.alchemy import ExporterConfig, ImporterConfig
from excelalchemy.types.identity import UrlStr
from excelalchemy.util.file import read_file_from_minio_object, remove_excel_prefix, upload_file_from_minio_object


class MinioStorageGateway:
    """Small gateway around the Minio-backed workbook IO helpers."""

    def __init__(self, config: ImporterConfig | ExporterConfig):
        self.config = config

    def read_excel_dataframe(self, input_excel_name: str, *, skiprows: int, sheet_name: str) -> DataFrame:
        """Read one Excel object from Minio into a DataFrame."""
        if self.config.minio is None:
            raise ConfigError('未配置 minio')

        file_object = read_file_from_minio_object(
            self.config.minio,
            self.config.bucket_name,
            input_excel_name,
        )

        try:
            return pandas.read_excel(
                cast(PathLike[str], file_object),
                sheet_name=sheet_name,
                skiprows=skiprows,
                header=None,
                dtype=str,
                engine='openpyxl',
            )
        finally:
            cast(BinaryIO, file_object).close()

    def upload_excel(self, output_name: str, content_with_prefix: str) -> UrlStr:
        """Upload one rendered workbook and return its signed URL."""
        if self.config.minio is None:
            raise ConfigError('未配置 minio')
        url = upload_file_from_minio_object(
            self.config.minio,
            self.config.bucket_name,
            output_name,
            remove_excel_prefix(content_with_prefix),
            self.config.url_expires,
        )
        return UrlStr(url)

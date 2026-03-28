from typing import Any, cast
from unittest import IsolatedAsyncioTestCase

from minio import Minio
from pydantic import BaseModel

from excelalchemy import ColumnIndex, ExcelAlchemy, ImporterConfig, RowIndex
from tests.support.mock_minio import local_minio


class BaseTestCase(IsolatedAsyncioTestCase):
    minio = local_minio
    first_data_row: RowIndex = RowIndex(0)
    first_data_col: ColumnIndex = ColumnIndex(2)

    @staticmethod
    async def fake_creator(data: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
        return data

    def build_alchemy(
        self,
        importer: type[BaseModel],
    ) -> ExcelAlchemy:
        return ExcelAlchemy(
            ImporterConfig(
                importer,
                creator=self.fake_creator,
                minio=cast(Minio, self.minio),
            ),
        )

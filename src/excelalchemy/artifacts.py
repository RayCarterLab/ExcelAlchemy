"""Structured workbook payloads for download and integration workflows."""

from __future__ import annotations

import base64
from dataclasses import dataclass, replace

from excelalchemy._internal.identity import DataUrlStr
from excelalchemy.util.file import EXCEL_MEDIA_TYPE, add_excel_prefix, remove_excel_prefix


@dataclass(slots=True, frozen=True)
class ExcelArtifact:
    """Structured Excel payload that can be consumed as bytes, base64, or a data URL."""

    content: bytes
    filename: str
    media_type: str = EXCEL_MEDIA_TYPE

    @classmethod
    def from_data_url(cls, data_url: str, *, filename: str, media_type: str = EXCEL_MEDIA_TYPE) -> 'ExcelArtifact':
        return cls(
            content=base64.b64decode(remove_excel_prefix(data_url)),
            filename=filename,
            media_type=media_type,
        )

    def with_filename(self, filename: str) -> 'ExcelArtifact':
        return replace(self, filename=filename)

    def as_bytes(self) -> bytes:
        return self.content

    def as_base64(self) -> str:
        return base64.b64encode(self.content).decode('ascii')

    def as_data_url(self) -> DataUrlStr:
        return DataUrlStr(add_excel_prefix(self.as_base64()))


from abc import ABC, abstractmethod
from collections.abc import Sequence

from pydantic import BaseModel

from excelalchemy._primitives.identity import DataUrlStr, UrlStr
from excelalchemy._primitives.payloads import ExportRowPayload
from excelalchemy.artifacts import ExcelArtifact
from excelalchemy.results import ImportResult


class ABCExcelAlchemy[
    ContextT,
    ImporterCreateModelT: BaseModel,
    ImporterUpdateModelT: BaseModel,
    CreateModelT: BaseModel,
    UpdateModelT: BaseModel,
    ExporterModelT: BaseModel,
](ABC):
    @abstractmethod
    def download_template(self, sample_data: list[ExportRowPayload] | None = None) -> DataUrlStr:
        """Render an import template and return it as a data URL."""

    @abstractmethod
    def download_template_artifact(
        self,
        sample_data: list[ExportRowPayload] | None = None,
        *,
        filename: str = 'template.xlsx',
    ) -> ExcelArtifact:
        """Render an import template and return a structured Excel artifact."""

    @abstractmethod
    async def import_data(self, input_excel_name: str, output_excel_name: str) -> ImportResult:
        """Import workbook data and return a structured result."""

    @abstractmethod
    def export(self, data: list[ExportRowPayload], keys: Sequence[str] | None = None) -> DataUrlStr:
        """Export rows and return the workbook as a data URL."""

    @abstractmethod
    def export_artifact(
        self,
        data: list[ExportRowPayload],
        keys: Sequence[str] | None = None,
        *,
        filename: str = 'export.xlsx',
    ) -> ExcelArtifact:
        """Export rows and return a structured Excel artifact."""

    @abstractmethod
    def export_upload(self, output_name: str, data: list[ExportRowPayload], keys: Sequence[str] | None = None) -> UrlStr:
        """Export rows and upload the workbook through the configured storage backend."""

    @abstractmethod
    def add_context(self, context: ContextT) -> None:
        """Attach runtime context used by importer callbacks."""

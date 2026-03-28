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
        """下载导入模版，返回 Data URL，字段顺序与定义的导出模型一致。"""

    @abstractmethod
    def download_template_artifact(
        self,
        sample_data: list[ExportRowPayload] | None = None,
        *,
        filename: str = 'template.xlsx',
    ) -> ExcelArtifact:
        """下载导入模板，返回结构化 Excel 产物。"""

    @abstractmethod
    async def import_data(self, input_excel_name: str, output_excel_name: str) -> ImportResult:
        """导入数据"""

    @abstractmethod
    def export(self, data: list[ExportRowPayload], keys: Sequence[str] | None = None) -> DataUrlStr:
        """导出数据，返回 Data URL 形式的 Excel 文件，字段顺序与定义的导出模型一致。"""

    @abstractmethod
    def export_artifact(
        self,
        data: list[ExportRowPayload],
        keys: Sequence[str] | None = None,
        *,
        filename: str = 'export.xlsx',
    ) -> ExcelArtifact:
        """导出数据，返回结构化 Excel 产物。"""

    @abstractmethod
    def export_upload(self, output_name: str, data: list[ExportRowPayload], keys: Sequence[str] | None = None) -> UrlStr:
        """导出数据, 自动将文件上传到配置的存储后端，字段顺序与定义的导出模型一致"""

    @abstractmethod
    def add_context(self, context: ContextT):
        """添加上下文"""

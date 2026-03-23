"""用于表示用户实际输入 Excel 的表头"""

from pydantic import BaseModel
from pydantic.fields import Field

from excelalchemy.const import UNIQUE_HEADER_CONNECTOR
from excelalchemy.types.identity import Label, UniqueLabel


class ExcelHeader(BaseModel):
    """用于表示用户输入的 Excel 表头信息"""

    label: Label = Field(description='Excel 的列名')
    parent_label: Label = Field(description='Excel 的父列名, 如果没有父列名, parent_label 等于 label')
    offset: int = Field(default=0, description='合并表头·子单元格所属父单元格的偏移量')

    @property
    def unique_label(self) -> UniqueLabel:
        """返回唯一标签"""
        label = (
            f'{self.parent_label}{UNIQUE_HEADER_CONNECTOR}{self.label}'
            if self.parent_label != self.label
            else self.label
        )
        return UniqueLabel(label)

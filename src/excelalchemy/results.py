"""导入 Excel 的结果"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from excelalchemy._internal.identity import Label
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import display_message as dmsg
from excelalchemy.i18n.messages import message as msg


class ValidateRowResult(str, Enum):
    """导入结果"""

    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'

    def __str__(self):
        if self is ValidateRowResult.SUCCESS:
            return dmsg(MessageKey.VALIDATE_ROW_SUCCESS)
        return dmsg(MessageKey.VALIDATE_ROW_FAIL)


class ValidateHeaderResult(BaseModel):
    """校验表头结果"""

    missing_required: list[Label] = Field(description='缺失的必填表头')
    missing_primary: list[Label] = Field(description='缺失的关键列')
    unrecognized: list[Label] = Field(description='无法识别的表头')
    duplicated: list[Label] = Field(description='重复的表头')
    is_valid: bool = Field(default=True, description='是否校验通过')

    @property
    def is_required_missing(self) -> bool:
        """是否缺失必填表头"""
        return bool(self.missing_required)


class ValidateResult(str, Enum):
    """导入结果类型"""

    HEADER_INVALID = 'HEADER_INVALID'  # 表头无效
    DATA_INVALID = 'DATA_INVALID'  # 数据无效
    SUCCESS = 'SUCCESS'  # 成功


class ImportResult(BaseModel):
    """导入数据结果"""

    model_config = ConfigDict(extra='allow')

    result: ValidateResult = Field(description='导入结果')

    is_required_missing: bool = Field(default=False, description='是否缺失必填表头')
    missing_required: list[Label] = Field(default_factory=list, description='缺失的必填表头')
    missing_primary: list[Label] = Field(default_factory=list, description='缺失的关键列')
    unrecognized: list[Label] = Field(default_factory=list, description='无法识别的表头')
    duplicated: list[Label] = Field(default_factory=list, description='重复的表头')

    url: str | None = Field(default=None, description='导入结果文件的下载链接, 失败时有值')
    success_count: int = Field(default=0, description='导入成功的数据条数')
    fail_count: int = Field(default=0, description='导入失败的数据条数')

    @classmethod
    def from_validate_header_result(cls, result: ValidateHeaderResult) -> 'ImportResult':
        """从校验表头结果构造导入结果"""
        if result.is_valid:
            raise RuntimeError(msg(MessageKey.IMPORT_RESULT_ONLY_FOR_INVALID_HEADER_VALIDATION))
        return cls(
            result=ValidateResult.HEADER_INVALID,
            is_required_missing=result.is_required_missing,
            missing_primary=result.missing_primary,
            unrecognized=result.unrecognized,
            duplicated=result.duplicated,
            missing_required=result.missing_required,
        )

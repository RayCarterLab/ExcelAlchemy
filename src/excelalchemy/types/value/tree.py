import logging
from typing import Any

from excelalchemy.types.field import FieldMetaInfo
from excelalchemy.types.value.multi_checkbox import MultiCheckbox
from excelalchemy.types.value.radio import Radio


class SingleTreeNode(Radio):
    __name__ = '树形单选'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        return '\n'.join(
            [
                field_meta.comment_required,
                f'提示：{field_meta.hint or "需按照组织架构树填写组织完整路径，如“XX公司/一级部门/二级部门”，多选时，选项之间用“、”连接"}',
            ]
        )

    @classmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @classmethod
    def deserialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        try:
            return field_meta.options_id_map[value.strip()].name
        except KeyError:
            logging.warning('无法找到树结点 %s 的选项, 返回原值', value)

        return value if value is not None else ''


class MultiTreeNode(MultiCheckbox):
    __name__ = '树形多选'

    @classmethod
    def comment(cls, field_meta: FieldMetaInfo) -> str:
        required = '必填' if field_meta.required else '非必填'
        extra_hint = (
            field_meta.hint
            or '请输入完整路径（包含根节点），层级之间用“/”连接，如“一级/二级/选项1”；多选时，选项之间用“，”连接'
        )
        return f"""必填性：{required} \n提示：{extra_hint}"""

    @classmethod
    def serialize(cls, value: Any, field_meta: FieldMetaInfo) -> Any:
        return super().serialize(value, field_meta)

    @classmethod
    def __validate__(cls, value: Any, field_meta: FieldMetaInfo) -> list[str]:
        return super().__validate__(value, field_meta)

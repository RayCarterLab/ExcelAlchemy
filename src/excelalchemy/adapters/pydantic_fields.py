"""Pydantic field adapters for workbook field declarations."""

from pydantic.fields import FieldInfo

from excelalchemy.errors import ProgrammaticError
from excelalchemy.messages import MessageKey
from excelalchemy.messages import message as msg
from excelalchemy.workbook_fields import FieldMetaInfo


def extract_declared_field_metadata(field_info: FieldInfo) -> FieldMetaInfo:
    metadata = _resolve_declared_field_metadata(field_info)
    return _overlay_pydantic_field_constraints(metadata.clone(), field_info)


def _resolve_declared_field_metadata(field_info: FieldInfo) -> FieldMetaInfo:
    from excelalchemy.columns import ExcelColumnSpec

    for item in field_info.metadata:
        if isinstance(item, ExcelColumnSpec):
            return item.to_field_metadata()

    if isinstance(field_info.default, (FieldMetaInfo, ExcelColumnSpec)):
        raise ProgrammaticError(
            'Annotated fields must place ExcelColumn(...) inside Annotated metadata; '
            'use `field: Annotated[T, Field(...), ExcelColumn(...)]`'
        )

    raise ProgrammaticError(msg(MessageKey.FIELD_DEFINITIONS_MUST_USE_EXCELCOLUMN))


def _overlay_pydantic_field_constraints(metadata: FieldMetaInfo, field_info: FieldInfo) -> FieldMetaInfo:
    for item in field_info.metadata:
        if isinstance(item, FieldMetaInfo):
            continue

        ge = getattr(item, 'ge', None)
        if ge is not None:
            metadata.importer_ge = ge

        le = getattr(item, 'le', None)
        if le is not None:
            metadata.importer_le = le

        max_digits = getattr(item, 'max_digits', None)
        if max_digits is not None:
            metadata.importer_max_digits = max_digits

        decimal_places = getattr(item, 'decimal_places', None)
        if decimal_places is not None:
            metadata.importer_decimal_places = decimal_places

        min_length = getattr(item, 'min_length', None)
        if min_length is not None:
            metadata.importer_min_length = min_length
            metadata.importer_min_items = min_length

        max_length = getattr(item, 'max_length', None)
        if max_length is not None:
            metadata.importer_max_length = max_length
            metadata.importer_max_items = max_length

        unique_items = getattr(item, 'unique_items', None)
        if unique_items is not None:
            metadata.importer_unique_items = unique_items

    return metadata


__all__ = ['extract_declared_field_metadata']

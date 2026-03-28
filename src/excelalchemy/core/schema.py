"""Schema layout helpers used by the ExcelAlchemy facade."""

import itertools
from collections import defaultdict
from decimal import Decimal
from itertools import chain
from typing import Iterable, cast

from pydantic import BaseModel

from excelalchemy._internal.constants import DEFAULT_FIELD_META_ORDER
from excelalchemy._internal.identity import Key, Label, UniqueKey, UniqueLabel
from excelalchemy.exceptions import ConfigError, ExcelCellError, ExcelRowError
from excelalchemy.helper.pydantic import extract_pydantic_model
from excelalchemy.i18n.messages import MessageKey
from excelalchemy.i18n.messages import message as msg
from excelalchemy.metadata import FieldMetaInfo


class ExcelSchemaLayout:
    """Capture the flattened Excel-facing layout derived from one model."""

    def __init__(self, field_metas: list[FieldMetaInfo]):
        self.field_metas = field_metas
        self._check_field_meta_order(field_metas)
        if not field_metas:
            raise ConfigError(msg(MessageKey.NO_FIELD_METADATA_EXTRACTED))

        self.ordered_field_meta = self._sort_field_meta(field_metas)
        self.unique_label_to_field_meta: dict[UniqueLabel, FieldMetaInfo] = {}
        self.parent_label_to_field_metas: dict[Label, list[FieldMetaInfo]] = {}
        self.parent_key_to_field_metas: dict[Key, list[FieldMetaInfo]] = {}
        self.unique_key_to_field_meta: dict[UniqueKey, FieldMetaInfo] = {}
        self._build_indexes()

    @classmethod
    def from_model(cls, model: type[BaseModel]) -> 'ExcelSchemaLayout':
        """Build a layout from a model and validate its field ordering contract."""
        field_metas = extract_pydantic_model(model)
        if not field_metas:
            raise ConfigError(msg(MessageKey.NO_FIELD_METADATA_EXTRACTED_FROM_MODEL, model_name=model.__name__))
        return cls(field_metas)

    def _build_indexes(self) -> None:
        for field_meta in self.ordered_field_meta:
            if field_meta.parent_label is None:
                raise ConfigError(msg(MessageKey.PARENT_LABEL_EMPTY_RUNTIME))
            if field_meta.parent_key is None:
                raise ConfigError(msg(MessageKey.PARENT_KEY_EMPTY_RUNTIME))

            self.parent_label_to_field_metas.setdefault(field_meta.parent_label, []).append(field_meta)
            self.parent_key_to_field_metas.setdefault(field_meta.parent_key, []).append(field_meta)
            self.unique_key_to_field_meta[field_meta.unique_key] = field_meta
            self.unique_label_to_field_meta[field_meta.unique_label] = field_meta

    @staticmethod
    def _check_field_meta_order(field_metas: list[FieldMetaInfo]) -> None:
        order_to_field_meta: dict[int, set[Label]] = defaultdict(set)
        for field_meta in field_metas:
            assert field_meta.parent_label is not None
            order_to_field_meta[field_meta.order].add(field_meta.parent_label)
        duplicate_order = [v for k, v in order_to_field_meta.items() if len(v) > 1 and k != DEFAULT_FIELD_META_ORDER]
        if duplicate_order:
            raise ConfigError(
                msg(
                    MessageKey.DUPLICATE_FIELD_ORDER_DEFINITIONS,
                    duplicate_order=list(itertools.chain.from_iterable(duplicate_order)),
                )
            )

    @classmethod
    def _sort_field_meta(cls, field_metas: list[FieldMetaInfo]) -> list[FieldMetaInfo]:
        orders: dict[Label, int] = {}
        for idx, field_meta in enumerate(field_metas):
            assert field_meta.parent_label is not None
            if field_meta.order == DEFAULT_FIELD_META_ORDER:
                orders[field_meta.parent_label] = idx
            else:
                orders[field_meta.parent_label] = field_meta.order

        return sorted(
            field_metas,
            key=lambda x: (
                orders.get(cast(Label, x.parent_label), Decimal('Infinity')),
                x.offset,
            ),
        )

    def has_merged_header(self, selected_keys: list[UniqueKey]) -> bool:
        """Return whether the selected keys need a two-row merged header."""
        return any(
            self.unique_key_to_field_meta[key].label != self.unique_key_to_field_meta[key].parent_label
            for key in selected_keys
        )

    def get_output_parent_excel_headers(self, selected_keys: list[UniqueKey] | None = None) -> list[UniqueLabel]:
        """Return the flattened header row used as worksheet table columns."""
        if not selected_keys:
            return [field_meta.unique_label for field_meta in self.ordered_field_meta]
        return [self.unique_key_to_field_meta[key].unique_label for key in selected_keys]

    def get_output_child_excel_headers(self, selected_keys: list[UniqueKey] | None = None) -> list[Label]:
        """Return the child labels used in the second header row for merged exports."""
        if not selected_keys:
            return [field_meta.label for field_meta in self.ordered_field_meta]
        return [self.unique_key_to_field_meta[key].label for key in selected_keys]

    def select_output_excel_keys(self, keys: list[Key] | None = None) -> list[UniqueKey]:
        """Expand parent keys into concrete flattened keys while preserving layout order."""
        if not keys:
            return [field_meta.unique_key for field_meta in self.ordered_field_meta]

        selected_field_meta: list[FieldMetaInfo] = []
        for key in keys:
            if key in self.unique_key_to_field_meta:
                selected_field_meta.append(self.unique_key_to_field_meta[UniqueKey(key)])
            elif key in self.parent_key_to_field_metas:
                selected_field_meta.extend(self.parent_key_to_field_metas[key])
            else:
                raise ValueError(msg(MessageKey.INVALID_KEY, key=key))

        return [field_meta.unique_key for field_meta in self._sort_field_meta(selected_field_meta)]

    def order_errors(self, errors: list[ExcelRowError | ExcelCellError]) -> Iterable[ExcelCellError | ExcelRowError]:
        """Sort cell errors by schema order and keep row-level errors at the end."""
        unique_label_to_index = {field_meta.unique_label: idx for idx, field_meta in enumerate(self.ordered_field_meta)}
        row_errors: list[ExcelRowError] = []
        cell_errors: list[ExcelCellError] = []
        for error in errors:
            if isinstance(error, ExcelRowError):
                row_errors.append(error)
            else:
                cell_errors.append(error)
        cell_errors.sort(key=lambda error: unique_label_to_index.get(error.unique_label, Decimal('Infinity')))
        return chain(cell_errors, row_errors)

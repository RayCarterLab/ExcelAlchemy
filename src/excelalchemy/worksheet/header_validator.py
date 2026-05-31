"""Worksheet header validation helpers."""

from collections.abc import Container, Sequence

from excelalchemy.config import ImportMode
from excelalchemy.primitives.identity import Label
from excelalchemy.results import ValidateHeaderResult
from excelalchemy.schema import ExcelSchemaLayout
from excelalchemy.worksheet.header import ExcelHeader


class ExcelHeaderValidator:
    """Validate parsed headers against one schema layout."""

    def validate(
        self,
        headers: list[ExcelHeader],
        layout: ExcelSchemaLayout,
        import_mode: ImportMode,
    ) -> ValidateHeaderResult:
        """Return the full header validation result consumed by the facade."""
        required_labels = [field_meta.unique_label for field_meta in layout.ordered_field_meta if field_meta.required]
        primary_labels = [
            field_meta.unique_label for field_meta in layout.ordered_field_meta if field_meta.is_primary_key
        ]
        schema_labels = [field_meta.unique_label for field_meta in layout.ordered_field_meta]
        input_labels = [header.unique_label for header in headers]

        visited: set[Label] = set()
        duplicated: list[Label] = []
        for label in input_labels:
            if label in visited:
                duplicated.append(label)
            else:
                visited.add(label)

        schema_label_set = set(schema_labels)
        input_label_set = set(input_labels)
        unrecognized = [Label(label) for label in self._ordered_difference(input_labels, schema_label_set)]

        missing_primary: list[Label] = []
        if import_mode == ImportMode.UPDATE:
            missing_primary = self._ordered_missing(primary_labels, input_label_set)
        missing_required = self._ordered_missing(required_labels, input_label_set, excluded=set(missing_primary))

        return ValidateHeaderResult(
            unrecognized=unrecognized,
            duplicated=duplicated,
            missing_required=missing_required,
            missing_primary=missing_primary,
            is_valid=not (missing_required or unrecognized or duplicated or missing_primary),
        )

    @staticmethod
    def _ordered_difference[T](values: Sequence[T], allowed: Container[T]) -> list[T]:
        seen: set[T] = set()
        result: list[T] = []
        for value in values:
            if value in allowed or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    @staticmethod
    def _ordered_missing[T](
        expected: Sequence[T],
        actual: Container[T],
        *,
        excluded: Container[T] | None = None,
    ) -> list[T]:
        excluded = excluded or set()
        return [value for value in expected if value not in actual and value not in excluded]


__all__ = ['ExcelHeaderValidator']

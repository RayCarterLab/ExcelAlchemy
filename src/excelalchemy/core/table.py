"""Lightweight worksheet table abstraction used by the core import/export flow."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import cast, overload

type WorksheetValue = object
type WorksheetColumn = object


@dataclass(frozen=True)
class _WorksheetStringAccessor:
    values: list[WorksheetValue]

    def startswith(self, prefix: str) -> list[bool]:
        return [isinstance(value, str) and value.startswith(prefix) for value in self.values]


class WorksheetColumns(list[WorksheetColumn]):
    """List-like column container with the small API surface used by the core layer."""

    def get_loc(self, value: WorksheetColumn) -> int:
        try:
            return self.index(value)
        except ValueError as exc:
            raise KeyError(value) from exc


class WorksheetRow:
    """Row view used by header parsing and row iteration."""

    def __init__(self, index: Iterable[WorksheetColumn], values: list[WorksheetValue]):
        self._index = list(index)
        self._values = values

    @property
    def str(self) -> _WorksheetStringAccessor:
        return _WorksheetStringAccessor(self._values)

    def items(self) -> Iterator[tuple[WorksheetColumn, WorksheetValue]]:
        return iter(zip(self._index, self._values, strict=True))

    def tolist(self) -> list[WorksheetValue]:
        return list(self._values)

    def to_dict(self) -> dict[WorksheetColumn, WorksheetValue]:
        return dict(zip(self._index, self._values, strict=True))

    def __getitem__(self, key: int | WorksheetColumn) -> WorksheetValue:
        if isinstance(key, int):
            return self._values[key]
        return self.to_dict()[key]


class _WorksheetILoc:
    def __init__(self, table: WorksheetTable):
        self._table = table

    @overload
    def __getitem__(self, key: tuple[int, int]) -> WorksheetValue: ...

    @overload
    def __getitem__(self, key: slice) -> WorksheetTable: ...

    @overload
    def __getitem__(self, key: int) -> WorksheetRow: ...

    def __getitem__(self, key: slice | int | tuple[int, int]) -> WorksheetTable | WorksheetRow | WorksheetValue:
        if isinstance(key, tuple):
            row_index, column_index = key
            return self._table.cell_at(row_index, column_index)
        if isinstance(key, slice):
            return self._table.slice_rows(key)
        return self._table.row_at(key)


class WorksheetTable:
    """A minimal 2D table API that mirrors the table features ExcelAlchemy actually uses."""

    def __init__(
        self,
        columns: Iterable[WorksheetColumn] | None = None,
        rows: Iterable[Iterable[WorksheetValue] | Mapping[WorksheetColumn, WorksheetValue]] | None = None,
    ):
        self._columns = WorksheetColumns(list(columns or []))
        self._rows = [self._normalize_row(row) for row in (rows or [])]

    def _normalize_row(
        self,
        row: Iterable[WorksheetValue] | Mapping[WorksheetColumn, WorksheetValue],
    ) -> list[WorksheetValue]:
        if isinstance(row, Mapping):
            if not self._columns:
                self._columns = WorksheetColumns(list(row.keys()))
            row_mapping = cast(Mapping[WorksheetColumn, WorksheetValue], row)
            return [row_mapping.get(column, None) for column in self._columns]

        values = list(row)
        if not self._columns:
            self._columns = WorksheetColumns(list(range(len(values))))

        if len(values) < len(self._columns):
            return values + [None] * (len(self._columns) - len(values))
        if len(values) > len(self._columns):
            return values[: len(self._columns)]
        return values

    @property
    def columns(self) -> WorksheetColumns:
        return self._columns

    @columns.setter
    def columns(self, value: Iterable[WorksheetColumn]) -> None:
        self._columns = WorksheetColumns(list(value))

    @property
    def iloc(self) -> _WorksheetILoc:
        return _WorksheetILoc(self)

    @property
    def shape(self) -> tuple[int, int]:
        return len(self._rows), len(self._columns)

    @property
    def index(self) -> range:
        return range(len(self._rows))

    def head(self, count: int) -> WorksheetTable:
        return WorksheetTable(columns=self.columns, rows=self._rows[:count])

    def row_at(self, row_index: int) -> WorksheetRow:
        return WorksheetRow(self.columns, self._rows[row_index])

    def cell_at(self, row_index: int, column_index: int) -> WorksheetValue:
        return self._rows[row_index][column_index]

    def slice_rows(self, row_slice: slice) -> WorksheetTable:
        return WorksheetTable(columns=self.columns, rows=self._rows[row_slice])

    def reset_index(self, *, drop: bool = False) -> WorksheetTable:
        if not drop:
            raise NotImplementedError('WorksheetTable only supports reset_index(drop=True)')
        return WorksheetTable(columns=self.columns, rows=self._rows)

    def iterrows(self) -> Iterator[tuple[int, WorksheetRow]]:
        for row_index, row in enumerate(self._rows):
            yield row_index, WorksheetRow(self.columns, row)

    def with_prepended_rows(
        self,
        rows: Iterable[Iterable[WorksheetValue] | Mapping[WorksheetColumn, WorksheetValue]],
    ) -> WorksheetTable:
        return WorksheetTable(columns=self.columns, rows=[*rows, *self._rows])

    def insert(self, *, loc: int, column: WorksheetColumn, value: Sequence[WorksheetValue]) -> None:
        self._columns.insert(loc, column)
        for row, cell_value in zip(self._rows, value, strict=True):
            row.insert(loc, cell_value)

    def __len__(self) -> int:
        return len(self._rows)

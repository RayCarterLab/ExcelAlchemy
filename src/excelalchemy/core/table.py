"""Lightweight worksheet table abstraction used by the core import/export flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, overload


@dataclass(frozen=True)
class _WorksheetStringAccessor:
    values: list[Any]

    def startswith(self, prefix: str) -> list[bool]:
        return [isinstance(value, str) and value.startswith(prefix) for value in self.values]


class WorksheetColumns(list[Any]):
    """List-like column container with the small API surface used by the core layer."""

    def get_loc(self, value: Any) -> int:
        try:
            return self.index(value)
        except ValueError as exc:
            raise KeyError(value) from exc


class WorksheetRow:
    """Row view used by header parsing and row iteration."""

    def __init__(self, index: Iterable[Any], values: list[Any]):
        self._index = list(index)
        self._values = values

    @property
    def str(self) -> _WorksheetStringAccessor:
        return _WorksheetStringAccessor(self._values)

    def items(self) -> Iterator[tuple[Any, Any]]:
        return iter(zip(self._index, self._values))

    def tolist(self) -> list[Any]:
        return list(self._values)

    def to_dict(self) -> dict[Any, Any]:
        return dict(zip(self._index, self._values))

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return self._values[key]
        return self.to_dict()[key]


class _WorksheetILoc:
    def __init__(self, table: 'WorksheetTable'):
        self._table = table

    @overload
    def __getitem__(self, key: tuple[int, int]) -> Any: ...

    @overload
    def __getitem__(self, key: slice) -> 'WorksheetTable': ...

    @overload
    def __getitem__(self, key: int) -> WorksheetRow: ...

    def __getitem__(self, key: slice | int | tuple[int, int]) -> 'WorksheetTable | WorksheetRow | Any':
        if isinstance(key, tuple):
            row_index, column_index = key
            return self._table._rows[row_index][column_index]
        if isinstance(key, slice):
            return WorksheetTable(columns=self._table.columns, rows=self._table._rows[key])
        return WorksheetRow(self._table.columns, self._table._rows[key])


class WorksheetTable:
    """A minimal 2D table API that mirrors the table features ExcelAlchemy actually uses."""

    def __init__(self, columns: Iterable[Any] | None = None, rows: Iterable[Iterable[Any]] | None = None):
        self._columns = WorksheetColumns(list(columns or []))
        self._rows = [self._normalize_row(row) for row in (rows or [])]

    def _normalize_row(self, row: Iterable[Any] | dict[Any, Any]) -> list[Any]:
        if isinstance(row, dict):
            if not self._columns:
                self._columns = WorksheetColumns(list(row.keys()))
            return [row.get(column) for column in self._columns]

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
    def columns(self, value: Iterable[Any]) -> None:
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

    def head(self, count: int) -> 'WorksheetTable':
        return WorksheetTable(columns=self.columns, rows=self._rows[:count])

    def reset_index(self, *, drop: bool = False) -> 'WorksheetTable':
        if not drop:
            raise NotImplementedError('WorksheetTable only supports reset_index(drop=True)')
        return WorksheetTable(columns=self.columns, rows=self._rows)

    def iterrows(self) -> Iterator[tuple[int, WorksheetRow]]:
        for row_index, row in enumerate(self._rows):
            yield row_index, WorksheetRow(self.columns, row)

    def with_prepended_rows(self, rows: Iterable[Iterable[Any]]) -> 'WorksheetTable':
        return WorksheetTable(columns=self.columns, rows=[*rows, *self._rows])

    def insert(self, *, loc: int, column: Any, value: list[Any]) -> None:
        self._columns.insert(loc, column)
        for row, cell_value in zip(self._rows, value, strict=True):
            row.insert(loc, cell_value)

    def __len__(self) -> int:
        return len(self._rows)

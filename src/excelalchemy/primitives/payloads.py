"""Typed row payload shapes shared across config and core import/export flows."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping

type FlatRowPayload = dict[str, object]
type NestedRowPayload = dict[str, object]
type AggregatedRowPayload = dict[str, object | NestedRowPayload]
type ModelRowPayload = dict[str, object]
type ExportRowPayload = dict[str, object]
type RowPayloadLike = Mapping[str, object]

type ImportContext[ContextT] = ContextT | None
type DataConverter = Callable[[ModelRowPayload], ModelRowPayload]
type DmlCallback[ContextT] = Callable[[ModelRowPayload, ImportContext[ContextT]], Awaitable[object]]
type ExistenceCheckCallback[ContextT] = Callable[[ModelRowPayload, ImportContext[ContextT]], Awaitable[bool]]

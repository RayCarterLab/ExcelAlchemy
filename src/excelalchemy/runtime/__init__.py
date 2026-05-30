"""Runtime import/export orchestration."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from excelalchemy.runtime.executor import ImportExecutor
    from excelalchemy.runtime.facade import REASON_COLUMN, RESULT_COLUMN, ExcelAlchemy
    from excelalchemy.runtime.facade_protocol import ABCExcelAlchemy
    from excelalchemy.runtime.import_session import ImportSession, ImportSessionPhase, ImportSessionSnapshot
    from excelalchemy.runtime.preflight import ImportPreflight
    from excelalchemy.runtime.rows import ImportIssueTracker, RowAggregator

__all__ = [
    'REASON_COLUMN',
    'RESULT_COLUMN',
    'ABCExcelAlchemy',
    'ExcelAlchemy',
    'ImportExecutor',
    'ImportIssueTracker',
    'ImportPreflight',
    'ImportSession',
    'ImportSessionPhase',
    'ImportSessionSnapshot',
    'RowAggregator',
]


def __getattr__(name: str) -> object:
    if name == 'ABCExcelAlchemy':
        from excelalchemy.runtime.facade_protocol import ABCExcelAlchemy

        return ABCExcelAlchemy
    if name in {'ExcelAlchemy', 'REASON_COLUMN', 'RESULT_COLUMN'}:
        from excelalchemy.runtime.facade import REASON_COLUMN, RESULT_COLUMN, ExcelAlchemy

        return {'ExcelAlchemy': ExcelAlchemy, 'REASON_COLUMN': REASON_COLUMN, 'RESULT_COLUMN': RESULT_COLUMN}[name]
    if name == 'ImportExecutor':
        from excelalchemy.runtime.executor import ImportExecutor

        return ImportExecutor
    if name in {'ImportSession', 'ImportSessionPhase', 'ImportSessionSnapshot'}:
        from excelalchemy.runtime.import_session import ImportSession, ImportSessionPhase, ImportSessionSnapshot

        return {
            'ImportSession': ImportSession,
            'ImportSessionPhase': ImportSessionPhase,
            'ImportSessionSnapshot': ImportSessionSnapshot,
        }[name]
    if name == 'ImportPreflight':
        from excelalchemy.runtime.preflight import ImportPreflight

        return ImportPreflight
    if name in {'ImportIssueTracker', 'RowAggregator'}:
        from excelalchemy.runtime.rows import ImportIssueTracker, RowAggregator

        return {'ImportIssueTracker': ImportIssueTracker, 'RowAggregator': RowAggregator}[name]
    raise AttributeError(name)

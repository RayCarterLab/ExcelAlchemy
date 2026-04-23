"""Lightweight workbook preflight for structural import checks."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from excelalchemy.config import ImporterConfig
from excelalchemy.core.headers import ExcelHeaderParser, ExcelHeaderValidator
from excelalchemy.core.schema import ExcelSchemaLayout
from excelalchemy.core.storage_protocol import ExcelStorage
from excelalchemy.core.table import WorksheetTable
from excelalchemy.exceptions import ConfigError, WorksheetNotFoundError
from excelalchemy.results import (
    ImportPreflightResult,
    ImportPreflightStatus,
)

HEADER_HINT_LINE_COUNT = 1


@dataclass(slots=True)
class ImportPreflight[
    ContextT,
    ImportCreateModelT: BaseModel,
    ImportUpdateModelT: BaseModel,
]:
    """Read-only structural validation for one workbook."""

    config: ImporterConfig[ContextT, ImportCreateModelT, ImportUpdateModelT]
    layout: ExcelSchemaLayout
    storage_gateway: ExcelStorage
    header_parser: ExcelHeaderParser
    header_validator: ExcelHeaderValidator

    def run(self, input_excel_name: str) -> ImportPreflightResult:
        sheet_name = self.config.schema_options.sheet_name

        try:
            worksheet_table = self.storage_gateway.read_excel_table(
                input_excel_name,
                skiprows=HEADER_HINT_LINE_COUNT,
                sheet_name=sheet_name,
            )
        except ConfigError:
            raise
        except WorksheetNotFoundError:
            return ImportPreflightResult(
                status=ImportPreflightStatus.SHEET_MISSING,
                sheet_name=sheet_name,
                sheet_exists=False,
                structural_issue_codes=[],
            )

        return self._validate_loaded_table(worksheet_table, sheet_name=sheet_name)

    def _validate_loaded_table(self, worksheet_table: WorksheetTable, *, sheet_name: str) -> ImportPreflightResult:
        if len(worksheet_table) == 0:
            return ImportPreflightResult(
                status=ImportPreflightStatus.STRUCTURE_INVALID,
                sheet_name=sheet_name,
                sheet_exists=True,
                structural_issue_codes=['header_row_missing'],
            )

        header_table = worksheet_table.head(2)
        has_merged_header = self.header_parser.has_merged_header(header_table)
        if has_merged_header and len(header_table) < 2:
            return ImportPreflightResult(
                status=ImportPreflightStatus.STRUCTURE_INVALID,
                sheet_name=sheet_name,
                sheet_exists=True,
                has_merged_header=True,
                structural_issue_codes=['merged_header_incomplete'],
            )

        try:
            headers = self.header_parser.extract(header_table)
        except Exception:
            return ImportPreflightResult(
                status=ImportPreflightStatus.STRUCTURE_INVALID,
                sheet_name=sheet_name,
                sheet_exists=True,
                has_merged_header=has_merged_header,
                structural_issue_codes=['header_block_unreadable'],
            )

        validate_header = self.header_validator.validate(headers, self.layout, self.config.behavior.import_mode)
        estimated_row_count = max(0, len(worksheet_table) - 1 - int(has_merged_header))
        return ImportPreflightResult.from_validate_header_result(
            validate_header,
            sheet_name=sheet_name,
            sheet_exists=True,
            has_merged_header=has_merged_header,
            estimated_row_count=estimated_row_count,
        )

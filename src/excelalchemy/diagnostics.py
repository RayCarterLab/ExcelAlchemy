"""Named diagnostic loggers and helpers for developer-facing runtime output."""

from __future__ import annotations

import logging

RUNTIME_LOGGER_NAME = 'excelalchemy.runtime'
METADATA_LOGGER_NAME = 'excelalchemy.metadata'

runtime_logger = logging.getLogger(RUNTIME_LOGGER_NAME)
metadata_logger = logging.getLogger(METADATA_LOGGER_NAME)


def log_runtime_context_replacement() -> None:
    runtime_logger.warning(
        'Replacing an existing conversion context; subsequent imports will use the new runtime context.'
    )


def log_runtime_exporter_inference(*, source: str) -> None:
    runtime_logger.info('Inferring exporter_model from %s.', source)


def log_runtime_export_requested_in_import_mode() -> None:
    runtime_logger.info('Export requested while configured in import mode; inferring exporter_model and continuing.')


def log_runtime_ignoring_unrecognized_export_keys(*, unrecognized: set[str], model_keys: list[str]) -> None:
    runtime_logger.warning(
        'Ignoring export keys that are not present in the exporter model. Ignored keys: %s. Exporter model keys: %s.',
        sorted(unrecognized),
        model_keys,
    )


def log_metadata_large_option_set(*, field_label: str, option_count: int) -> None:
    metadata_logger.warning(
        'Field "%s" defines %s options. Options are intended for bounded vocabularies, so review this field if it '
        'represents a large dataset.',
        field_label,
        option_count,
    )


def log_metadata_missing_option_id(*, option_id: str, field_label: str) -> None:
    metadata_logger.warning(
        'Could not resolve option id %s for field "%s"; returning the original workbook value.',
        option_id,
        field_label,
    )

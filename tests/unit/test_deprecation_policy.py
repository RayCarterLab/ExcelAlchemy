import importlib
import sys
import warnings

from excelalchemy import ExcelAlchemyDeprecationWarning


def import_compat_module(module_name: str) -> list[warnings.WarningMessage]:
    compat_prefixes = (
        'excelalchemy.types',
        'excelalchemy.exc',
        'excelalchemy.identity',
        'excelalchemy.header_models',
    )
    compat_modules = [
        loaded_name
        for loaded_name in sys.modules
        if any(loaded_name == prefix or loaded_name.startswith(f'{prefix}.') for prefix in compat_prefixes)
    ]
    for loaded_name in compat_modules:
        sys.modules.pop(loaded_name, None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', ExcelAlchemyDeprecationWarning)
        importlib.import_module(module_name)

    return caught


class TestDeprecationPolicy:
    def test_package_level_compat_namespace_emits_explicit_deprecation_warning(self):
        warnings_seen = import_compat_module('excelalchemy.types')

        assert any(
            isinstance(warning.message, ExcelAlchemyDeprecationWarning)
            and '`excelalchemy.types` is deprecated' in str(warning.message)
            and 'ExcelAlchemy 3.0' in str(warning.message)
            for warning in warnings_seen
        )

    def test_leaf_compat_module_points_to_replacement_import_path(self):
        warnings_seen = import_compat_module('excelalchemy.types.value.string')

        assert any(
            isinstance(warning.message, ExcelAlchemyDeprecationWarning)
            and '`excelalchemy.types.value.string` is deprecated' in str(warning.message)
            and '`excelalchemy.codecs.string`' in str(warning.message)
            for warning in warnings_seen
        )

    def test_legacy_exc_module_points_to_public_exceptions_module(self):
        warnings_seen = import_compat_module('excelalchemy.exc')

        assert any(
            isinstance(warning.message, ExcelAlchemyDeprecationWarning)
            and '`excelalchemy.exc` is deprecated' in str(warning.message)
            and '`excelalchemy.exceptions`' in str(warning.message)
            for warning in warnings_seen
        )

    def test_legacy_identity_module_points_to_package_root(self):
        warnings_seen = import_compat_module('excelalchemy.identity')

        assert any(
            isinstance(warning.message, ExcelAlchemyDeprecationWarning)
            and '`excelalchemy.identity` is deprecated' in str(warning.message)
            and '`the excelalchemy package root`' in str(warning.message)
            for warning in warnings_seen
        )

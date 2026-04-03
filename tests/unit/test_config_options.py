import warnings
from typing import cast

from minio import Minio

from excelalchemy import ExporterConfig, ImporterConfig, ImportMode
from excelalchemy._primitives.deprecation import ExcelAlchemyDeprecationWarning
from excelalchemy.config import _EMITTED_STORAGE_DEPRECATION_WARNINGS
from tests.support import BaseTestCase, InMemoryExcelStorage
from tests.support.contract_models import SimpleContractImporter, creator


class TestConfigOptions(BaseTestCase):
    async def test_importer_config_normalizes_schema_behavior_and_storage_options(self):
        storage = InMemoryExcelStorage()
        config = ImporterConfig(
            SimpleContractImporter,
            creator=creator,
            import_mode=ImportMode.CREATE,
            storage=storage,
            minio=cast(Minio, self.minio),
            locale='en',
            sheet_name='People',
        )

        assert config.schema_options.create_importer_model is SimpleContractImporter
        assert config.schema_options.update_importer_model is None
        assert config.schema_options.locale == 'en'
        assert config.schema_options.sheet_name == 'People'

        assert config.behavior.import_mode == ImportMode.CREATE
        assert config.behavior.creator is creator
        assert config.behavior.context is None

        assert config.storage_options.storage is storage
        assert config.storage_options.minio is self.minio
        assert config.storage_options.has_explicit_storage
        assert config.storage_options.has_legacy_minio

    async def test_importer_helper_constructors_select_expected_modes(self):
        create_config = ImporterConfig.for_create(SimpleContractImporter, creator=creator)
        update_config = ImporterConfig.for_update(SimpleContractImporter, updater=creator)

        assert create_config.import_mode == ImportMode.CREATE
        assert create_config.schema_options.create_importer_model is SimpleContractImporter
        assert update_config.import_mode == ImportMode.UPDATE
        assert update_config.schema_options.update_importer_model is SimpleContractImporter

    async def test_exporter_helper_constructors_support_recommended_storage_path(self):
        storage = InMemoryExcelStorage()
        config = ExporterConfig.for_storage(SimpleContractImporter, storage=storage, locale='en')

        assert config.schema_options.exporter_model is SimpleContractImporter
        assert config.storage_options.storage is storage
        assert config.schema_options.locale == 'en'

    async def test_legacy_minio_path_emits_deprecation_warning(self):
        _EMITTED_STORAGE_DEPRECATION_WARNINGS.clear()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', ExcelAlchemyDeprecationWarning)
            ImporterConfig.for_create(SimpleContractImporter, creator=creator, minio=cast(Minio, self.minio))

        assert any(
            isinstance(warning.message, ExcelAlchemyDeprecationWarning)
            and '`minio`, `bucket_name`, and `url_expires` are deprecated' in str(warning.message)
            for warning in caught
        )

    async def test_exporter_config_normalizes_schema_behavior_and_storage_options(self):
        storage = InMemoryExcelStorage()
        config = ExporterConfig(
            SimpleContractImporter,
            storage=storage,
            locale='en',
            sheet_name='People',
        )

        assert config.schema_options.exporter_model is SimpleContractImporter
        assert config.schema_options.locale == 'en'
        assert config.schema_options.sheet_name == 'People'

        assert config.behavior.data_converter is config.data_converter
        assert config.storage_options.storage is storage
        assert not config.storage_options.has_legacy_minio

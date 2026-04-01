from typing import cast

from minio import Minio

from excelalchemy import ExporterConfig, ImporterConfig, ImportMode
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

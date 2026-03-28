from excelalchemy.util.file import EXCEL_PREFIX, remove_excel_prefix


class TestFileUtils:
    def test_remove_excel_prefix_strips_only_the_exact_prefix(self):
        prefixed_content = f'{EXCEL_PREFIX},data:payload'

        assert remove_excel_prefix(prefixed_content) == 'data:payload'

    def test_remove_excel_prefix_leaves_unprefixed_content_unchanged(self):
        content = 'data:payload'

        assert remove_excel_prefix(content) == content

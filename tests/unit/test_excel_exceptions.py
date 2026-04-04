from excelalchemy import (
    CellErrorMap,
    ConfigError,
    ExcelCellError,
    ExcelRowError,
    Label,
    ProgrammaticError,
    RowIssueMap,
)
from tests.support import BaseTestCase


class TestExcelExceptions(BaseTestCase):
    async def test_excel_cell_errors_compare_equal_when_message_and_label_match(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert exc1 == exc2

        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱1'), message='Enter a valid email address')

        assert exc1 != exc2

    async def test_excel_cell_error_repr_includes_label_and_message(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert (
            repr(exc1)
            == "ExcelCellError(label=Label('邮箱'), parent_label=None, message='Enter a valid email address')"
        )

    async def test_excel_cell_error_str_prefixes_label(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert str(exc1) == '【邮箱】Enter a valid email address'

    async def test_excel_cell_error_requires_non_empty_label(self):
        self.assertRaises(ValueError, ExcelCellError, label=Label(''), message='Enter a valid email address')

    async def test_excel_cell_error_builds_unique_label_from_parent_when_present(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert exc1.unique_label == '邮箱'

        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address', parent_label=Label('父'))
        assert exc1.unique_label == '父·邮箱'

    async def test_excel_cell_error_supports_equality_and_inequality_operations(self):
        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert exc1 == exc2

        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱1'), message='Enter a valid email address')
        assert exc1 != exc2

        exc1 = ExcelCellError(label=Label('邮箱'), parent_label=Label('员工'), message='Enter a valid email address')
        exc2 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        assert exc1 != exc2

        exc1 = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        other = 'other'

        assert exc1 != other
        assert other != exc1

    async def test_excel_row_error_preserves_message_in_string_representations(self):
        exc1 = ExcelRowError(message='Excel row import error')
        assert exc1.message == 'Excel row import error'

        exc1 = ExcelRowError(message='Enter a valid email address')
        assert exc1.message == 'Enter a valid email address'

        exc1 = ExcelRowError(message='Enter a valid email address')
        assert str(exc1) == 'Enter a valid email address'

        exc1 = ExcelRowError(message='Enter a valid email address')
        assert repr(exc1) == "ExcelRowError(message='Enter a valid email address', detail={})"

    async def test_excel_cell_error_to_dict_includes_coordinate_metadata(self):
        exc = ExcelCellError(label=Label('邮箱'), parent_label=Label('员工'), message='Enter a valid email address')

        assert exc.to_dict() == {
            'type': 'ExcelCellError',
            'code': 'ExcelCellError',
            'message': 'Enter a valid email address',
            'display_message': '【邮箱】Enter a valid email address',
            'label': '邮箱',
            'field_label': '邮箱',
            'parent_label': '员工',
            'unique_label': '员工·邮箱',
        }

    async def test_programmatic_and_config_errors_preserve_detail_payloads(self):
        programmatic = ProgrammaticError('Invalid declaration', field='email')
        config = ConfigError('Missing storage backend', backend='minio')

        assert programmatic.to_dict() == {
            'type': 'ProgrammaticError',
            'code': 'ProgrammaticError',
            'message': 'Invalid declaration',
            'display_message': 'Invalid declaration',
            'detail': {'field': 'email'},
        }
        assert config.to_dict() == {
            'type': 'ConfigError',
            'code': 'ConfigError',
            'message': 'Missing storage backend',
            'display_message': 'Missing storage backend',
            'detail': {'backend': 'minio'},
        }
        assert repr(programmatic) == "ProgrammaticError(message='Invalid declaration', detail={'field': 'email'})"
        assert repr(config) == "ConfigError(message='Missing storage backend', detail={'backend': 'minio'})"

    async def test_cell_error_map_supports_coordinate_access_and_flattening(self):
        error_map = CellErrorMap()
        error = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')

        error_map.add(0, 3, error)

        assert error_map.has_errors is True
        assert error_map.error_count == 1
        assert error_map.at(0, 3) == (error,)
        assert error_map.messages_at(0, 3) == ('【邮箱】Enter a valid email address',)
        assert error_map.flatten() == (error,)
        assert error_map.for_row(0) == {3: (error,)}
        assert error_map.to_dict() == {
            0: {
                3: [
                    {
                        'type': 'ExcelCellError',
                        'code': 'ExcelCellError',
                        'message': 'Enter a valid email address',
                        'display_message': '【邮箱】Enter a valid email address',
                        'label': '邮箱',
                        'field_label': '邮箱',
                        'parent_label': None,
                        'unique_label': '邮箱',
                    }
                ]
            }
        }
        assert error_map.to_api_payload() == {
            'error_count': 1,
            'items': [
                {
                    'type': 'ExcelCellError',
                    'code': 'ExcelCellError',
                    'message': 'Enter a valid email address',
                    'display_message': '【邮箱】Enter a valid email address',
                    'label': '邮箱',
                    'field_label': '邮箱',
                    'parent_label': None,
                    'unique_label': '邮箱',
                    'row_index': 0,
                    'row_number_for_humans': 1,
                    'column_index': 3,
                    'column_number_for_humans': 4,
                }
            ],
            'by_row': {
                0: {
                    3: [
                        {
                            'type': 'ExcelCellError',
                            'code': 'ExcelCellError',
                            'message': 'Enter a valid email address',
                            'display_message': '【邮箱】Enter a valid email address',
                            'label': '邮箱',
                            'field_label': '邮箱',
                            'parent_label': None,
                            'unique_label': '邮箱',
                        }
                    ]
                }
            },
            'summary': {
                'by_field': [
                    {
                        'field_label': '邮箱',
                        'parent_label': None,
                        'unique_label': '邮箱',
                        'error_count': 1,
                        'row_indices': [0],
                        'row_numbers_for_humans': [1],
                        'codes': ['ExcelCellError'],
                    }
                ],
                'by_row': [
                    {
                        'row_index': 0,
                        'row_number_for_humans': 1,
                        'error_count': 1,
                        'codes': ['ExcelCellError'],
                        'field_labels': ['邮箱'],
                        'unique_labels': ['邮箱'],
                    }
                ],
                'by_code': [
                    {
                        'code': 'ExcelCellError',
                        'error_count': 1,
                        'row_indices': [0],
                        'row_numbers_for_humans': [1],
                        'unique_labels': ['邮箱'],
                    }
                ],
            },
        }

        field_summary = error_map.summary_by_field()
        assert field_summary[0].to_dict()['unique_label'] == '邮箱'
        assert error_map.summary_by_code()[0].code == 'ExcelCellError'
        assert error_map.summary_by_row()[0].row_number_for_humans == 1

    async def test_row_issue_map_supports_row_access_and_numbered_messages(self):
        issue_map = RowIssueMap()
        cell_error = ExcelCellError(label=Label('邮箱'), message='Enter a valid email address')
        row_error = ExcelRowError(message='Combination invalid')

        issue_map.add(0, cell_error)
        issue_map.add(0, row_error)

        assert issue_map.has_errors is True
        assert issue_map.error_count == 2
        assert issue_map.at(0) == (cell_error, row_error)
        assert issue_map.messages_for_row(0) == ('【邮箱】Enter a valid email address', 'Combination invalid')
        assert issue_map.numbered_messages_for_row(0) == (
            '1、【邮箱】Enter a valid email address',
            '2、Combination invalid',
        )
        assert issue_map.numbered_messages(issue_map.at(0)) == (
            '1、【邮箱】Enter a valid email address',
            '2、Combination invalid',
        )
        assert issue_map.to_dict() == {
            0: [
                {
                    'type': 'ExcelCellError',
                    'code': 'ExcelCellError',
                    'message': 'Enter a valid email address',
                    'display_message': '【邮箱】Enter a valid email address',
                    'label': '邮箱',
                    'field_label': '邮箱',
                    'parent_label': None,
                    'unique_label': '邮箱',
                },
                {
                    'type': 'ExcelRowError',
                    'code': 'ExcelRowError',
                    'message': 'Combination invalid',
                    'display_message': 'Combination invalid',
                },
            ]
        }
        assert issue_map.to_api_payload() == {
            'error_count': 2,
            'items': [
                {
                    'type': 'ExcelCellError',
                    'code': 'ExcelCellError',
                    'message': 'Enter a valid email address',
                    'display_message': '【邮箱】Enter a valid email address',
                    'label': '邮箱',
                    'field_label': '邮箱',
                    'parent_label': None,
                    'unique_label': '邮箱',
                    'row_index': 0,
                    'row_number_for_humans': 1,
                },
                {
                    'type': 'ExcelRowError',
                    'code': 'ExcelRowError',
                    'message': 'Combination invalid',
                    'display_message': 'Combination invalid',
                    'row_index': 0,
                    'row_number_for_humans': 1,
                    'field_label': None,
                    'parent_label': None,
                    'unique_label': None,
                },
            ],
            'by_row': {
                0: [
                    {
                        'type': 'ExcelCellError',
                        'code': 'ExcelCellError',
                        'message': 'Enter a valid email address',
                        'display_message': '【邮箱】Enter a valid email address',
                        'label': '邮箱',
                        'field_label': '邮箱',
                        'parent_label': None,
                        'unique_label': '邮箱',
                    },
                    {
                        'type': 'ExcelRowError',
                        'code': 'ExcelRowError',
                        'message': 'Combination invalid',
                        'display_message': 'Combination invalid',
                    },
                ]
            },
            'summary': {
                'by_row': [
                    {
                        'row_index': 0,
                        'row_number_for_humans': 1,
                        'error_count': 2,
                        'codes': ['ExcelCellError', 'ExcelRowError'],
                        'field_labels': ['邮箱'],
                        'unique_labels': ['邮箱'],
                    }
                ],
                'by_code': [
                    {
                        'code': 'ExcelCellError',
                        'error_count': 1,
                        'row_indices': [0],
                        'row_numbers_for_humans': [1],
                        'unique_labels': ['邮箱'],
                    },
                    {
                        'code': 'ExcelRowError',
                        'error_count': 1,
                        'row_indices': [0],
                        'row_numbers_for_humans': [1],
                        'unique_labels': [],
                    },
                ],
            },
        }
        assert issue_map.summary_by_row()[0].error_count == 2
        assert [summary.code for summary in issue_map.summary_by_code()] == ['ExcelCellError', 'ExcelRowError']

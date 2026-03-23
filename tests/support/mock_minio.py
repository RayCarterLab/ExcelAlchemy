import io
import os
from copy import copy
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas
from excelalchemy.const import HEADER_HINT

from tests.support.registry import FileRegistry


class LocalMockMinio:
    """有合并表头的内容直接使用文件"""

    storage: dict[str, Any] = {}
    bucket_name: str = 'test'

    mock_excel_data: dict[str, Any] = {
        FileRegistry.TEST_HEADER_INVALID_INPUT: [
            {
                '不存在的表头': '是',
            },
        ],
        FileRegistry.TEST_BOOLEAN_INPUT: [
            {
                '是否启用': '是',
            },
        ],
        FileRegistry.TEST_DATE_INPUT: [
            {
                '出生日期': '2021-01-01',
            },
        ],
        FileRegistry.TEST_DATE_INPUT_WRONG_RANGE: [
            {
                '出生日期': '2021-01-32',
            },
        ],
        FileRegistry.TEST_DATE_INPUT_WRONG_FORMAT: [
            {
                '出生日期': '2021-13',
            },
        ],
        FileRegistry.TEST_DATE_RANGE_INPUT: './files/test_date_range_input.xlsx',
        FileRegistry.TEST_DATE_RANGE_MISSING_INPUT_BEFORE: './files/test_date_range_missing_input_before.xlsx',
        FileRegistry.TEST_DATE_RANGE_MISSING_INPUT_AFTER: './files/test_date_range_missing_input_after.xlsx',
        FileRegistry.TEST_EMAIL_WRONG_FORMAT: [
            {
                '邮箱': '123',
            },
        ],
        FileRegistry.TEST_EMAIL_CORRECT_FORMAT: [
            {
                '邮箱': 'excelalchemy@163.com',
            },
        ],
        FileRegistry.TEST_SIMPLE_IMPORT: [
            {
                '年龄': 18,
                '姓名': '张三',
                '地址': '北京市',
                '是否启用': '是',
                '出生日期': '2021-01-01',
                '邮箱': 'noreply@icloud.com',
                '价格': 100.0,
                '爱好': '篮球',
                '公司': '阿里巴巴',
                '经理': '李四',
                '部门': '研发部',
                '电话': '13223658966',
                '单选': '选项1',
                '老板': '马云',
                '领导': '张三',
                '团队': '研发部',
                '网址': 'https://www.baidu.com',
            }
        ],
        FileRegistry.TEST_SIMPLE_IMPORT_WITH_ERROR: [
            {
                '年龄': '18',
                '姓名': 'Denial',
                '地址': '北京市',
                '是否启用': '是',
                '出生日期': '2021-01-32',
                '邮箱': 'not an email',
                '价格': '100.0',
                '爱好': '游泳',
                '公司': '亚马逊',
                '经理': '经理',
                '部门': '研发部门',
                '电话': '123',
                '单选': '选项10',
                '老板': '自己',
                '领导': '自己',
                '团队': '研发部门',
                '网址': 'google',
            }
        ],
        FileRegistry.TEST_IMPORT_WITH_MERGE_HEADER: './files/test_import_with_merge_header.xlsx',
    }

    def __init__(self):
        """generate mock (NamedTemporaryFile) Excel files from mock_excel_data

        automatically add HEADER_HINT to first row
        """
        for filename, data in self.mock_excel_data.items():
            if isinstance(data, str):
                df = pandas.read_excel(Path(__file__).resolve().parent.parent / Path(data.lstrip('./')))
            else:
                df = pandas.DataFrame(data)

            f = NamedTemporaryFile(suffix='.xlsx', delete=False)
            f.close()  # 关键：先关闭，避免 Windows 文件锁问题

            original_header = df.columns
            df.columns = range(len(df.columns))
            header_row = pandas.Series(original_header, index=df.columns)
            df = pandas.concat([header_row.to_frame().T, df], ignore_index=True)

            df.loc[-1] = 0
            df.index = df.index + 1
            df = df.sort_index()
            df.iat[0, 0] = HEADER_HINT

            df.to_excel(f.name, index=False, header=False, engine='openpyxl')

            with open(f.name, 'rb') as rf:
                file_bytes = rf.read()

            data = io.BytesIO(file_bytes)
            length = len(file_bytes)
            self.put_object(self.bucket_name, filename, data, length, f.name)

    def put_object(self, bucket_name: str, filename: str, data: io.BytesIO, length: int, file: Any = None) -> None:
        self.storage[filename] = {
            'bucket_name': bucket_name,
            'filename': filename,
            'data': data,
            'length': length,
            'file': file,
        }

    @classmethod
    def presigned_get_object(cls, bucket_name: str, filename: str, expires: int) -> str:
        return f'{bucket_name}/{filename}'

    def get_object(self, bucket_name: str, filename: str) -> io.BytesIO:
        assert bucket_name is not None
        return copy(self.storage[filename]['data'])  # use copy to avoid close(), so it can be read multiple times

    def __del__(self):
        for filename, data in self.storage.items():
            if isinstance(data['file'], str) and os.path.exists(data['file']):
                os.remove(data['file'])


local_minio = LocalMockMinio()

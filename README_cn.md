# ExcelAlchemy

[English README](README.md) · [快速开始](docs/getting-started.md) · [示例](examples/README.md) · [Public API](docs/public-api.md) · [迁移说明](docs/migrations.md) · [限制说明](docs/limitations.md) · [Changelog](CHANGELOG.md)

仓库指南：[AGENTS.md](AGENTS.md) · [Coding Agent Guide](docs/agent/coding-agent-guide.md) · [Repository Map](docs/repo-map.md)

ExcelAlchemy 是一个基于 Pydantic 模型的 schema-driven Excel 导入/导出库。

它把 Python 类型模型变成 Excel 工作簿契约：

- 从类型模型生成 Excel 模板
- 校验用户上传的工作簿
- 把错误映射回行和单元格
- 生成面向用户的结果工作簿
- 通过 `ExcelStorage` 支持可替换的存储实现

当前稳定版本是 ExcelAlchemy 3.0。3.0 使用普通 Python 类型标注配合显式
`ExcelColumn(...)` 元数据。2.x 的字段工厂、兼容导入、legacy 配置字段和
facade 别名都不再是当前 API。

## 截图

| 模板 | 导入结果 |
| --- | --- |
| ![Excel 模板截图](docs/assets/images/portfolio-template-en.png) | ![Excel 导入结果截图](docs/assets/images/portfolio-import-result-en.png) |

## 安装

```bash
pip install ExcelAlchemy
```

如果需要内置 Minio-compatible 存储支持：

```bash
pip install "ExcelAlchemy[minio]"
```

## 快速示例

```python
from typing import Annotated

from pydantic import BaseModel, Field

from excelalchemy import EmailCodec, ExcelAlchemy, ExcelColumn, ImporterConfig


class EmployeeImport(BaseModel):
    name: Annotated[str, ExcelColumn(label='姓名', order=1)]
    email: Annotated[
        str,
        Field(min_length=8),
        ExcelColumn(
            label='邮箱',
            codec=EmailCodec(),
            order=2,
            hint='使用工作邮箱',
            example_value='alice@company.com',
        ),
    ]


alchemy = ExcelAlchemy(ImporterConfig(EmployeeImport, locale='zh-CN'))
template = alchemy.download_template_artifact(filename='employees-template.xlsx')

excel_bytes = template.as_bytes()
```

Python 类型标注定义数据形状，Pydantic `Field(...)` 定义 Pydantic 校验，
`ExcelColumn(...)` 定义 Excel 表头、顺序、提示、示例值和 codec 行为。

浏览器下载时，优先从后端返回 `template.as_bytes()` 并设置
`Content-Disposition: attachment`，或者在前端构造 `Blob`。不要依赖很长的
顶层 `data:` URL 导航。

## 导入工作流

最短路径可以概括为：

```text
template -> preflight -> import -> remediation -> delivery
```

后端代码中通常是：

```python
from excelalchemy.results import ImportLifecycleEvent, build_frontend_remediation_payload


events: list[ImportLifecycleEvent] = []

preflight = alchemy.preflight_import('employees.xlsx')
if not preflight.is_valid:
    response = {'preflight': preflight.to_api_payload()}
else:
    result = await alchemy.import_data(
        'employees.xlsx',
        'employees-result.xlsx',
        on_event=events.append,
    )
    response = {
        'result': result.to_api_payload(),
        'events': [event.model_dump(mode='json', exclude_none=True) for event in events],
        'cell_errors': alchemy.cell_error_map.to_api_payload(),
        'row_errors': alchemy.row_error_map.to_api_payload(),
        'remediation': build_frontend_remediation_payload(
            result=result,
            cell_error_map=alchemy.cell_error_map,
            row_error_map=alchemy.row_error_map,
        ),
    }
```

更完整的入门说明见 [docs/getting-started.md](docs/getting-started.md)，可运行
示例见 [examples/README.md](examples/README.md)。

## 适合什么场景

ExcelAlchemy 适合后端导入/导出工作流，尤其是 Excel 模板本身就是业务契约的一部分时。

适合：

- 给业务用户发模板并回收 Excel 数据
- 保持 Excel 输入和后端 Pydantic 模型一致
- 在失败结果中指出具体哪一行、哪一格有问题
- 给前端返回可用于重试和修复的结构化 payload
- 接入自定义对象存储或工作簿 IO

不适合：

- 桌面 Excel 自动化
- 宏执行或公式重算
- pandas-first 数据分析
- 字节级完整保留原工作簿
- 实时表格编辑器

工具选择说明见 [docs/tool-comparison.md](docs/tool-comparison.md)。公式、文件保真和
大文件预期见 [docs/limitations.md](docs/limitations.md) 与
[docs/performance.md](docs/performance.md)。

## 下一步

- [快速开始](docs/getting-started.md)：安装、定义 schema、选择工作流。
- [示例](examples/README.md)：导入、导出、存储和 FastAPI 示例。
- [Public API](docs/public-api.md)：当前 3.0 公共模块和已移除的 2.x 名称。
- [Result Objects](docs/result-objects.md)：`ImportResult`、`CellErrorMap`、`RowIssueMap` 和 API payload。
- [API Response Cookbook](docs/api-response-cookbook.md)：后端/前端响应形状。
- [Integration Blueprints](docs/integration-blueprints.md)：同步上传、worker 导入和 remediation loop。
- [迁移说明](docs/migrations.md)：3.0 升级说明和历史升级资料。

## 开发

本仓库使用 `uv`：

```bash
uv sync --extra development
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
```

仓库内 agent 规则见 [AGENTS.md](AGENTS.md)。面向 Codex、Claude Code、Cursor 等
coding agent 的项目入口见 [docs/agent/coding-agent-guide.md](docs/agent/coding-agent-guide.md)。

## 许可证

MIT. See [LICENSE](LICENSE).

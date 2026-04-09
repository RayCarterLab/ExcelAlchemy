# Limitations & Gotchas

This page sets practical expectations for evaluating ExcelAlchemy in backend
systems.

If you want the quickest getting-started path, see
[`docs/getting-started.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/getting-started.md).
If you want the stable public API boundaries, see
[`docs/public-api.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/docs/public-api.md).
If you want runnable reference examples, see
[`examples/README.md`](https://github.com/RayCarterLab/ExcelAlchemy/blob/main/examples/README.md).

## Quick Fit Check

| Scenario | Is ExcelAlchemy a good fit? |
| --- | --- |
| Generate typed import/export templates from Pydantic models | Yes |
| Validate uploaded workbooks on the server and return result workbooks | Yes |
| Run in containers, CI, or Linux services without Microsoft Excel | Yes |
| Automate a locally installed Excel application | No |
| Preserve every workbook feature exactly while editing an existing file | Usually no |

## Formula Cells And Cached Values

ExcelAlchemy reads workbooks through `openpyxl` using workbook cell values.
In the storage implementations and examples in this repository, workbooks are
loaded with `load_workbook(..., data_only=True)`.

In practice, that means:

- ExcelAlchemy reads the stored cached value for a formula cell when one is
  available.
- ExcelAlchemy does not run Microsoft Excel on the server.
- ExcelAlchemy does not recalculate formulas itself.

This matters when a workbook was generated or modified outside Excel and the
cached values are missing or stale. In that case, the server sees the stored
cell values available in the file, not a newly recalculated workbook.

## Server-Side Processing, Not Excel Automation

ExcelAlchemy is designed for server-side file processing:

- generate templates
- read uploaded workbooks
- validate rows and cells
- render result workbooks
- upload or return workbook artifacts

It is not a desktop automation tool. It does not require a local Excel
installation, an Office COM bridge, or an interactive spreadsheet session.

That makes it a good fit for backend APIs, workers, and containerized services.
It is not the right tool when the requirement is “do what the Excel desktop app
would do on this machine.”

## Large Workbook Performance Expectations

ExcelAlchemy is a practical backend workflow library, not a high-scale
spreadsheet computation engine.

Performance depends on factors such as:

- workbook row and column count
- amount of workbook content being loaded and normalized
- validation complexity in your schema and callbacks
- number of failures written back into result workbooks

For large operational imports, plan for batch-style backend processing rather
than instant UI-style responsiveness. If your workflow regularly handles very
large workbooks, test with realistic files early and treat execution time and
memory use as part of integration planning.

## Workbook Fidelity And Round-Trip Limits

ExcelAlchemy reads workbook data for its own import/export workflow and renders
new workbook artifacts for templates, exports, and import results.

That means you should not position it as:

- a byte-for-byte round-trip editor for existing workbooks
- a preservation tool for every workbook feature
- a full-fidelity transformer for complex author-created spreadsheet files

This is especially important when people expect unchanged preservation of
features such as formulas, workbook-specific formatting decisions, charts,
macros, or other Excel-authored details outside the library's typed workflow.

## FAQ

### Will formulas be recalculated on the server?

No. ExcelAlchemy reads workbook values available to `openpyxl`; it does not run
Excel and does not recalculate formulas itself.

### Does this require Microsoft Excel on the host?

No. The repository is built around server-side processing with Python and
`openpyxl`, not local Excel automation.

### Is this a good fit for very large operational uploads?

It can be, but it should be treated as backend batch work. Validate the
performance with realistic files from your own domain before committing to large
upload workflows.

### Will formatting, charts, macros, or other workbook details survive unchanged?

Do not assume that. ExcelAlchemy is designed around typed Excel workflow data
and rendered workbook outputs, not full-fidelity preservation of complex
existing files.

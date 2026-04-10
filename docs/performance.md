# Performance Guide

This page gives practical performance guidance for ExcelAlchemy in backend
services.

It is intentionally operational rather than benchmark-driven. This repository
does not currently publish benchmark numbers, so the guidance here focuses on
how the current architecture behaves and what teams should plan for in
production.

If you want the expectations page for formulas, server-side execution, and
workbook fidelity, see
[`docs/limitations.md`](limitations.md).
If you want the main onboarding path, see
[`docs/getting-started.md`](getting-started.md).

## What Workloads Are Likely Fine

ExcelAlchemy is a good fit for typical backend Excel workflows such as:

- business uploads with moderate row counts and typed validation rules
- admin imports where row-level failures need to be written back into a result
  workbook
- template generation and export workflows for operational reports
- FastAPI or worker-based services that process workbooks as discrete jobs

In the current architecture, these use cases align well with:

- `openpyxl` for workbook IO
- `WorksheetTable` as the in-memory table abstraction
- row-by-row validation and callback execution
- storage-backed upload/download boundaries

## What Workloads Are Risky

The current design becomes riskier when you combine several of these conditions:

- very large workbooks
- wide sheets with many populated columns
- expensive per-row create or update callbacks
- many validation failures that produce large error maps and result workbooks
- memory-sensitive web workers handling multiple uploads at once

These cases are still possible to support, but they should be treated as
capacity-planning and integration problems rather than assumed “just works”
paths.

## Common Bottlenecks

### 1. Workbook Loading And Row Materialization

In the built-in storage path, ExcelAlchemy loads the workbook with
`openpyxl.load_workbook(...)` and then iterates rows into `WorksheetTable`.
That means the import path is not a streaming pipeline; it materializes workbook
content into in-memory Python structures for the rest of the workflow.

Practical consequence:

- larger and wider workbooks increase memory pressure early in the request/job

### 2. Row-By-Row Execution Cost

Import execution is row-oriented. Each row is:

- aggregated into model-shaped payloads
- validated through Pydantic-backed parsing
- passed into the configured `creator`, `updater`, or `is_data_exist` callbacks

Practical consequence:

- your own callback cost can dominate runtime, especially when it performs
  per-row network or database work

### 3. Failure-Heavy Imports

When an import is not fully successful, ExcelAlchemy builds:

- row and cell error maps
- result and reason columns
- a rendered result workbook for download or upload

Practical consequence:

- large invalid workbooks are usually more expensive than similarly sized valid
  workbooks

### 4. Render And Encoding Overhead

Template, export, and result-workbook rendering happens in memory. The writer
builds the workbook in `openpyxl`, saves it to an in-memory buffer, and the
default render path produces a base64 data URL.

Practical consequence:

- large outputs cost memory and CPU for workbook generation and encoding
- long data URLs are a less attractive transport for large workbook payloads

## Recommended Usage Patterns

### Prefer Batch-Oriented Backend Flows

For larger uploads, design the integration like backend job processing, not like
interactive spreadsheet editing.

Good patterns:

- accept upload, store it, and process it in a worker or background task
- return job status separately from the upload request when files are large
- use result workbook URLs or storage-backed artifacts instead of pushing large
  workbook payloads through every synchronous response

### Keep Per-Row Callbacks Cheap

`creator`, `updater`, and `is_data_exist` are on the hot path.

Prefer:

- batched lookups where possible
- cached reference data in the job context
- minimizing repeated remote calls per row

Avoid:

- doing multiple external round trips for every imported row when the workbook
  is large

### Use Realistic Test Files Early

The repository does not define safe thresholds for row counts, file sizes, or
timeouts. The right limits depend on:

- your schema shape
- your callback behavior
- your worker memory budget
- how many uploads run concurrently

Use realistic workbooks from your domain before setting product expectations.

### Prefer Bytes Or Storage Uploads For Larger Outputs

ExcelAlchemy supports structured artifacts and storage-backed upload flows.
For larger exports or result workbooks, prefer:

- `ExcelArtifact.as_bytes()` when you control the HTTP response directly
- storage-backed upload flows when files should be downloaded later

Be cautious about relying on long base64/data-URL style payloads for large
files across service boundaries.

## Anti-Patterns

- Treating very large uploads as normal request/response work with tight API
  timeouts
- Assuming import cost is only about file size while ignoring per-row callback
  work
- Letting many invalid rows accumulate in a synchronous web request without an
  operational timeout plan
- Using ExcelAlchemy as if it were a streaming ETL engine
- Assuming a failure-heavy workbook will cost roughly the same as a fully valid
  workbook

## What To Do When Importing Large Workbooks

When large workbooks are part of the product, start with this approach:

1. Validate upload size before opening the workbook.
2. Route larger files to a background job instead of a synchronous request.
3. Measure memory use and runtime with realistic files.
4. Reduce per-row remote work in your callbacks.
5. Decide whether the result workbook should be returned inline or uploaded to
   storage for later download.
6. Set explicit operational limits based on your service budget, not on assumed
   spreadsheet norms.

## Operational Guardrails For Backend Services

Use guardrails like these in production services:

- set a maximum upload size at the API gateway or application layer
- define request timeouts and a clear threshold for background-job handoff
- validate content type, extension, and workbook presence before deeper
  processing
- log input file size, row count, outcome, and processing time
- limit concurrent large workbook jobs per worker pool
- monitor memory, timeout rates, and failure-heavy import frequency
- store large result workbooks externally instead of keeping them in hot request
  memory longer than necessary

## Backend Service Checklist

- [ ] Maximum upload size is defined
- [ ] Request timeout is defined
- [ ] Large-file threshold for async/background processing is defined
- [ ] Upload validation happens before workbook parsing
- [ ] Per-row callback cost has been tested with realistic data
- [ ] Result workbook delivery path is chosen intentionally
- [ ] Memory and timeout monitoring are in place

## Future Work

This repository would benefit from explicit benchmark coverage in the future,
for example:

- representative import/export benchmark fixtures
- memory-focused regression checks for larger workbooks
- documentation of relative cost between valid and failure-heavy imports

Until that exists, treat performance planning as workload-specific and validate
it with realistic files from your own system.

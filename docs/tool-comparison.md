# Choose the Right Tool

This page helps you decide when ExcelAlchemy is the right fit and when another
category of tool is a better match.

The goal is not to rank tools in the abstract. Different tools solve different
problems. ExcelAlchemy is strongest when the problem is a typed Excel workflow
in a backend service, not just “read a spreadsheet somehow.”

If you want practical constraints first, see
[`docs/limitations.md`](limitations.md).
If you want operational planning guidance for larger workloads, see
[`docs/performance.md`](performance.md).

## Summary Table

| Decision dimension | ExcelAlchemy | Plain `openpyxl` scripting | Excel automation tools | Generic dataframe/schema validation |
| --- | --- | --- | --- | --- |
| Server-side suitability | Strong | Strong | Usually weak | Strong |
| Typed contract modeling | Strong | Manual | Usually weak | Strong for data, weaker for workbook UX |
| Workbook-facing error feedback | Strong | Manual | Possible, but usually custom | Usually weak |
| Frontend/backend integration | Strong | Custom | Usually weak for backend APIs | Strong for APIs, weaker for workbook UX |
| Template generation | Strong | Manual | Possible, but usually custom | Usually weak |
| Operational predictability | Strong for backend workflows | Depends on your script quality | Usually weaker in server environments | Strong for data pipelines |

## ExcelAlchemy vs Plain `openpyxl` Scripting

Use plain `openpyxl` scripting when:

- you need a one-off workbook transformation
- your schema is small and stable
- you are comfortable owning all workbook parsing and validation logic yourself

Use ExcelAlchemy when:

- the workbook is a recurring product surface, not a one-time script
- you want the schema declared in code through typed models
- you want template generation, import validation, and result-workbook feedback
  to stay aligned
- you want row and cell errors mapped back into workbook coordinates

Fair tradeoff:

- `openpyxl` is lower-level and more flexible for ad hoc workbook work
- ExcelAlchemy adds structure so repeated business workflows are easier to keep
  consistent

## ExcelAlchemy vs Excel Automation Tools

Use Excel automation tools when:

- the requirement is to drive a locally installed Excel application
- you need desktop behavior such as live recalculation, macro execution, or
  Office-specific automation
- the workflow depends on Excel itself being present

Use ExcelAlchemy when:

- you need server-side processing in APIs, workers, containers, or Linux
  services
- you need predictable backend behavior without depending on a desktop Excel
  runtime
- the main goal is typed import/export workflow management rather than desktop
  spreadsheet automation

Fair tradeoff:

- automation tools are closer to the Excel desktop product
- ExcelAlchemy is closer to backend application architecture

## ExcelAlchemy vs Generic Dataframe / Schema Validation Approaches

Use dataframe/schema validation approaches when:

- the main problem is tabular data cleaning or ETL
- the workbook is only an input format, not a user-facing workflow contract
- users do not need generated templates or workbook-embedded feedback

Use ExcelAlchemy when:

- the spreadsheet itself is part of the user workflow
- business users need a guided template, workbook-facing comments, and
  result-workbook feedback
- backend and frontend layers need structured import results tied back to
  workbook rows and cells

Fair tradeoff:

- dataframe-oriented stacks are often better for data pipelines and downstream
  transformations
- ExcelAlchemy is better when workbook UX and backend contract shape need to
  move together

## ExcelAlchemy vs A Fully Custom Import Pipeline

Use a custom pipeline when:

- your ingestion format is broader than Excel
- your rules are so domain-specific that a library abstraction adds little value
- you do not want the spreadsheet to be a first-class contract surface

Use ExcelAlchemy when:

- you want a reusable Excel workflow instead of rebuilding the same template,
  validation, and feedback machinery in each service
- your team benefits from a stable public API around workbook imports and
  exports

Fair tradeoff:

- a custom pipeline gives maximum freedom
- ExcelAlchemy gives a narrower but more repeatable workflow shape

## Recommended By Scenario

### Internal admin upload

ExcelAlchemy is usually a strong fit.

Why:

- typed schema definition
- template generation
- workbook-facing validation feedback
- API-friendly result objects for backend/frontend use

### Business user spreadsheet workflow

ExcelAlchemy is usually a strong fit when the spreadsheet is part of the
product workflow and the backend needs to own the contract.

### Excel automation or desktop interaction

ExcelAlchemy is usually not the right fit.

A desktop automation tool is a better match when the requirement is to automate
Excel itself.

### Dataframe-heavy ETL

ExcelAlchemy is often not the first tool to reach for.

If the core problem is bulk tabular processing, joins, transformations, and
pipeline execution rather than workbook UX, a dataframe-oriented stack is often
the better starting point.

## Short Decision Rule

Choose ExcelAlchemy when you need:

- server-side Excel workflow handling
- typed contract modeling
- generated templates
- workbook-facing validation feedback
- structured backend/frontend integration around import results

Choose something else when you mainly need:

- desktop Excel automation
- ad hoc workbook scripting with minimal abstraction
- dataframe-first ETL or analytics
- a fully custom ingestion pipeline without workbook-specific UX requirements

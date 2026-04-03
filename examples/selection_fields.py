"""Example schema that focuses on selection-heavy business forms."""

from pydantic import BaseModel

from excelalchemy import (
    ExcelAlchemy,
    FieldMeta,
    ImporterConfig,
    MultiCheckbox,
    MultiOrganization,
    MultiStaff,
    Option,
    OptionId,
    Radio,
    SingleOrganization,
    SingleStaff,
)

DEPARTMENT_OPTIONS = [
    Option(id=OptionId('finance'), name='Finance'),
    Option(id=OptionId('operations'), name='Operations'),
    Option(id=OptionId('engineering'), name='Engineering'),
]

ORGANIZATION_OPTIONS = [
    Option(id=OptionId('org-finance'), name='Acme/Finance'),
    Option(id=OptionId('org-ops'), name='Acme/Operations'),
]

STAFF_OPTIONS = [
    Option(id=OptionId('staff-taylor'), name='TaylorChen'),
    Option(id=OptionId('staff-avery'), name='AveryStone'),
]


class ApprovalFormImporter(BaseModel):
    request_type: Radio = FieldMeta(label='Request type', order=1, options=DEPARTMENT_OPTIONS)
    impacted_teams: MultiCheckbox = FieldMeta(label='Impacted teams', order=2, options=DEPARTMENT_OPTIONS)
    owner_org: SingleOrganization = FieldMeta(label='Owner organization', order=3, options=ORGANIZATION_OPTIONS)
    partner_orgs: MultiOrganization = FieldMeta(label='Partner organizations', order=4, options=ORGANIZATION_OPTIONS)
    owner: SingleStaff = FieldMeta(label='Owner', order=5, options=STAFF_OPTIONS)
    reviewers: MultiStaff = FieldMeta(label='Reviewers', order=6, options=STAFF_OPTIONS)


def main() -> None:
    alchemy = ExcelAlchemy(ImporterConfig.for_create(ApprovalFormImporter, locale='en'))
    template = alchemy.download_template_artifact(filename='selection-fields-template.xlsx')
    print(f'Generated template: {template.filename} ({len(template.as_bytes())} bytes)')
    print('Fields: Request type, Impacted teams, Owner organization, Partner organizations, Owner, Reviewers')


if __name__ == '__main__':
    main()

"""Example schema that focuses on selection-heavy business forms."""

from typing import Annotated

from pydantic import BaseModel

from excelalchemy import (
    ExcelAlchemy,
    ExcelColumn,
    ImporterConfig,
    MultiChoiceCodec,
    Option,
    OptionId,
    SingleChoiceCodec,
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
    request_type: Annotated[
        str, ExcelColumn(codec=SingleChoiceCodec(), label='Request type', order=1, options=DEPARTMENT_OPTIONS)
    ]
    impacted_teams: Annotated[
        list[str], ExcelColumn(codec=MultiChoiceCodec(), label='Impacted teams', order=2, options=DEPARTMENT_OPTIONS)
    ]
    owner_org: Annotated[
        str,
        ExcelColumn(
            codec=SingleChoiceCodec(
                entity_name='organization',
                hint="Enter the full organization path, for example 'Acme/Finance'.",
                include_options_in_comment=False,
                include_mode_in_comment=False,
            ),
            label='Owner organization',
            order=3,
            options=ORGANIZATION_OPTIONS,
        ),
    ]
    partner_orgs: Annotated[
        list[str],
        ExcelColumn(
            codec=MultiChoiceCodec(
                entity_name_plural='organizations',
                hint="Enter full organization paths. Use ',' to separate multiple selections.",
                include_options_in_comment=False,
                include_mode_in_comment=False,
                separator=',',
            ),
            label='Partner organizations',
            order=4,
            options=ORGANIZATION_OPTIONS,
        ),
    ]
    owner: Annotated[
        str,
        ExcelColumn(
            codec=SingleChoiceCodec(
                entity_name='staff member',
                hint='Enter the staff display name and identifier.',
                include_options_in_comment=False,
                include_mode_in_comment=False,
            ),
            label='Owner',
            order=5,
            options=STAFF_OPTIONS,
        ),
    ]
    reviewers: Annotated[
        list[str],
        ExcelColumn(
            codec=MultiChoiceCodec(
                entity_name_plural='staff members',
                hint="Enter staff display names and identifiers. Use ',' to separate multiple selections.",
                include_options_in_comment=False,
                include_mode_in_comment=False,
                separator=',',
            ),
            label='Reviewers',
            order=6,
            options=STAFF_OPTIONS,
        ),
    ]


def main() -> None:
    alchemy = ExcelAlchemy(ImporterConfig.for_create(ApprovalFormImporter, locale='en'))
    template = alchemy.download_template_artifact(filename='selection-fields-template.xlsx')
    print(f'Generated template: {template.filename} ({len(template.as_bytes())} bytes)')
    print('Fields: Request type, Impacted teams, Owner organization, Partner organizations, Owner, Reviewers')


if __name__ == '__main__':
    main()

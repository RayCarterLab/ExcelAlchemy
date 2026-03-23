from __future__ import annotations

import nox

DEFAULT_PYTHONS = ['3.10', '3.11', '3.12']
PACKAGE_INSTALL = ['-e', '.[development]']

nox.options.sessions = ['lint', 'typecheck', 'tests']


def install_project(session: nox.Session) -> None:
    session.install(*PACKAGE_INSTALL)


@nox.session(python='3.10')
def lint(session: nox.Session) -> None:
    install_project(session)
    session.run('pylint', 'excelalchemy')


@nox.session(python='3.10')
def typecheck(session: nox.Session) -> None:
    install_project(session)
    session.run('mypy', 'excelalchemy', 'tests')


@nox.session(python=DEFAULT_PYTHONS)
def tests(session: nox.Session) -> None:
    install_project(session)
    session.run(
        'pytest',
        '--cov=excelalchemy',
        '--cov-report=term-missing:skip-covered',
        '--cov-report=xml',
        'tests',
        *session.posargs,
    )

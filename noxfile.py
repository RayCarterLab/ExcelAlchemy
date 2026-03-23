from __future__ import annotations

import nox

DEFAULT_PYTHONS = ['3.10', '3.11', '3.12']
PACKAGE_INSTALL = ['-e', '.[development]']

nox.options.sessions = ['ruff', 'pyright', 'tests']


def install_project(session: nox.Session) -> None:
    session.install(*PACKAGE_INSTALL)


@nox.session(python='3.10')
def ruff(session: nox.Session) -> None:
    install_project(session)
    session.run('ruff', 'format', '--check', '.')
    session.run('ruff', 'check', '.')


@nox.session(python='3.10')
def pyright(session: nox.Session) -> None:
    install_project(session)
    session.run('pyright')


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


@nox.session(python='3.10')
def build(session: nox.Session) -> None:
    session.install('build')
    session.run('python', '-m', 'build')

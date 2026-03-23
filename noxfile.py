from __future__ import annotations

import nox

DEFAULT_PYTHONS = ['3.12', '3.13', '3.14']
MAIN_PYTHON = '3.14'
PACKAGE_INSTALL = ['-e', '.[development]']

nox.options.sessions = ['ruff', 'pyright', 'tests']
nox.options.error_on_missing_interpreters = False


def install_project(session: nox.Session) -> None:
    session.install(*PACKAGE_INSTALL)


@nox.session(python=MAIN_PYTHON)
def ruff(session: nox.Session) -> None:
    install_project(session)
    session.run('ruff', 'format', '--check', '.')
    session.run('ruff', 'check', '.')


@nox.session(python=MAIN_PYTHON)
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
        '--cov-report=xml:coverage.xml',
        '--junitxml=pytest.xml',
        'tests',
        *session.posargs,
    )


@nox.session(python=MAIN_PYTHON)
def build(session: nox.Session) -> None:
    session.install('build')
    session.run('python', '-m', 'build')

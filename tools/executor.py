"""Controlled execution boundary for deterministic repository tools."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from tools.repo_tools import RepoTool, get_repo_tools

ToolResult = dict[str, bool | str]


def execute_tool(name: str, args: dict[str, Any] | None = None) -> ToolResult:
    """Execute a registered repository tool and return a structured result."""

    payload = args or {}
    tool = _tool_registry().get(name)
    if tool is None:
        return _result(False, '', f'Unknown tool: {name}')

    try:
        repo_root = _repo_root(payload)
        timeout_seconds = _timeout_seconds(tool, payload)
        extra_args = _extra_args(tool, payload)
    except TypeError as exc:
        return _result(False, '', str(exc))
    if isinstance(extra_args, str):
        return _result(False, '', extra_args)
    if not tool.command:
        return _execute_python_tool(tool, payload, repo_root, timeout_seconds)

    try:
        completed = subprocess.run(
            (*tool.command, *extra_args),
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        return _result(False, '', f'Command not found for tool {name}: {exc.filename}')
    except subprocess.TimeoutExpired as exc:
        return _result(False, exc.stdout or '', f'Tool {name} timed out after {timeout_seconds}s: {exc.stderr or ""}')
    except OSError as exc:
        return _result(False, '', f'Tool {name} failed to start: {exc}')

    return _result(
        completed.returncode == 0,
        completed.stdout,
        completed.stderr if completed.returncode else '',
    )


def _tool_registry() -> dict[str, RepoTool]:
    return {tool.name: tool for tool in get_repo_tools()}


def _repo_root(args: dict[str, Any]) -> Path:
    value = args.get('repo_root')
    if value is None:
        return Path.cwd().resolve()
    if not isinstance(value, str):
        raise TypeError('Tool argument "repo_root" must be a string when provided.')
    return Path(value).resolve()


def _timeout_seconds(tool: RepoTool, args: dict[str, Any]) -> int:
    value = args.get('timeout_seconds', tool.timeout_seconds)
    if not isinstance(value, int) or value <= 0:
        raise TypeError('Tool argument "timeout_seconds" must be a positive integer.')
    return min(value, tool.timeout_seconds)


def _extra_args(tool: RepoTool, args: dict[str, Any]) -> tuple[str, ...] | str:
    value = args.get('extra_args', ())
    if value in (None, (), []):
        return ()
    if not tool.allow_extra_args:
        return f'Tool {tool.name} does not accept extra_args.'
    if not isinstance(value, list | tuple) or not all(isinstance(item, str) for item in value):
        return 'Tool argument "extra_args" must be a list of strings.'
    return tuple(value)


def _execute_python_tool(tool: RepoTool, args: dict[str, Any], repo_root: Path, timeout_seconds: int) -> ToolResult:
    if tool.name == 'read_file':
        return _read_file(args, repo_root)
    if tool.name == 'search_code':
        return _search_code(args, repo_root, timeout_seconds)
    if tool.name == 'apply_patch':
        return _apply_patch(args, repo_root, timeout_seconds)
    return _result(False, '', f'Tool {tool.name} is registered without an executor.')


def _read_file(args: dict[str, Any], repo_root: Path) -> ToolResult:
    path_result = _safe_repo_path(args, repo_root)
    if isinstance(path_result, str):
        return _result(False, '', path_result)

    max_chars = args.get('max_chars', 20000)
    if not isinstance(max_chars, int) or max_chars <= 0:
        return _result(False, '', 'Tool argument "max_chars" must be a positive integer.')
    if not path_result.is_file():
        return _result(False, '', f'File not found: {path_result.relative_to(repo_root)}')

    try:
        text = path_result.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        return _result(False, '', f'File is not valid UTF-8: {exc}')
    except OSError as exc:
        return _result(False, '', f'Unable to read file: {exc}')

    return _result(True, text[:max_chars], '')


def _search_code(args: dict[str, Any], repo_root: Path, timeout_seconds: int) -> ToolResult:
    pattern = args.get('pattern')
    if not isinstance(pattern, str) or not pattern:
        return _result(False, '', 'Tool argument "pattern" must be a non-empty string.')

    raw_paths = args.get('paths', ['.'])
    if not isinstance(raw_paths, list) or not all(isinstance(path, str) for path in raw_paths):
        return _result(False, '', 'Tool argument "paths" must be a list of strings.')

    safe_paths: list[str] = []
    for raw_path in raw_paths:
        path_result = _safe_repo_path({'path': raw_path}, repo_root)
        if isinstance(path_result, str):
            return _result(False, '', path_result)
        safe_paths.append(str(path_result.relative_to(repo_root)))

    max_chars = args.get('max_chars', 20000)
    if not isinstance(max_chars, int) or max_chars <= 0:
        return _result(False, '', 'Tool argument "max_chars" must be a positive integer.')

    try:
        completed = subprocess.run(
            ('rg', '--line-number', '--no-heading', pattern, *safe_paths),
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return _result(False, '', 'Command not found for tool search_code: rg')
    except subprocess.TimeoutExpired as exc:
        return _result(False, exc.stdout or '', f'Tool search_code timed out: {exc.stderr or ""}')

    if completed.returncode not in {0, 1}:
        return _result(False, completed.stdout[:max_chars], completed.stderr)
    return _result(True, completed.stdout[:max_chars], '')


def _apply_patch(args: dict[str, Any], repo_root: Path, timeout_seconds: int) -> ToolResult:
    patch = args.get('patch')
    if not isinstance(patch, str) or not patch.strip():
        return _result(False, '', 'Tool argument "patch" must be a non-empty string.')

    try:
        completed = subprocess.run(
            ('git', 'apply', '--whitespace=nowarn', '-'),
            cwd=repo_root,
            input=patch,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return _result(False, '', 'Command not found for tool apply_patch: git')
    except subprocess.TimeoutExpired as exc:
        return _result(False, exc.stdout or '', f'Tool apply_patch timed out: {exc.stderr or ""}')

    return _result(completed.returncode == 0, completed.stdout, completed.stderr if completed.returncode else '')


def _safe_repo_path(args: dict[str, Any], repo_root: Path) -> Path | str:
    value = args.get('path')
    if not isinstance(value, str) or not value:
        return 'Tool argument "path" must be a non-empty string.'
    path = (repo_root / value).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError:
        return f'Path escapes repository root: {value}'
    return path


def _result(success: bool, output: str, error: str) -> ToolResult:
    return {
        'success': success,
        'output': output,
        'error': error,
    }

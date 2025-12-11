from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from thesis_generator.config import load_settings
from thesis_generator.security import SecretManager


class SandboxUnavailableError(RuntimeError):
    """Raised when the e2b sandbox SDK is not installed."""


class ExecutionFailed(RuntimeError):
    """Raised when code execution fails inside the sandbox."""


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    files: dict[str, bytes]
    results: list[Any]


def _load_sandbox_class() -> Any:
    try:
        from e2b_code_interpreter import Sandbox
    except Exception as exc:  # pragma: no cover - import checked via tests
        raise SandboxUnavailableError(
            "e2b_code_interpreter is not installed. Add `e2b-code-interpreter` to dependencies."
        ) from exc

    return Sandbox


def _resolve_api_key(provided: str | None, *, secret_manager: SecretManager | None = None) -> str | None:
    if provided:
        return provided

    try:
        settings = load_settings(secret_manager=secret_manager)
    except RuntimeError:
        return None

    return getattr(settings, "e2b_api_key", None)


def _create_sandbox(*, api_key: str | None, timeout: float | None) -> Any:
    sandbox_cls = _load_sandbox_class()

    kwargs: dict[str, Any] = {
        "timeout": int(timeout) if timeout is not None else None,
        "allow_internet_access": False,
        "network": {"deny_out": ["0.0.0.0/0"]},
    }
    if api_key:
        kwargs["api_key"] = api_key

    return sandbox_cls.create(**kwargs)


def _validate_code_safety(code: str) -> None:
    lowered = code.lower()
    banned_markers = ["requests.get", "http://", "https://", "socket.", "subprocess"]
    if any(marker in lowered for marker in banned_markers):
        raise ExecutionFailed("Network and process access are blocked inside the sandbox.")


def _snapshot_files(filesystem: Any) -> set[str]:
    try:
        entries = filesystem.list("/", depth=5)
    except Exception:
        return set()

    paths: set[str] = set()
    for entry in entries or []:
        entry_type = getattr(entry, "type", None)
        path = getattr(entry, "path", None) or getattr(entry, "name", None)
        if entry_type == "file" and path:
            paths.add(path)
    return paths


def _upload_files(filesystem: Any, files: Mapping[str, bytes]) -> set[str]:
    uploaded: set[str] = set()
    for name, content in files.items():
        safe_name = name.lstrip("/")
        path = f"/home/user/{safe_name}"
        filesystem.write(path, content)
        uploaded.add(path)
    return uploaded


def _collect_new_files(filesystem: Any, baseline: set[str], exclude: set[str]) -> dict[str, bytes]:
    try:
        entries = filesystem.list("/", depth=10)
    except Exception:
        return {}

    new_files: dict[str, bytes] = {}
    for entry in entries or []:
        if getattr(entry, "type", None) != "file":
            continue

        path = getattr(entry, "path", None) or getattr(entry, "name", None)
        if not path or path in baseline or path in exclude:
            continue

        try:
            content = filesystem.read(path, format="bytes")
        except TypeError:
            content = filesystem.read(path)

        if isinstance(content, str):
            content = content.encode()
        new_files[path] = bytes(content)

    return new_files


def _ensure_success(execution: Any) -> None:
    if getattr(execution, "error", None):
        message = getattr(execution.error, "message", None) or str(execution.error)
        raise ExecutionFailed(f"Execution failed: {message}")


def execute_python(
    code: str,
    *,
    files: Mapping[str, bytes] | None = None,
    timeout: float = 30.0,
    api_key: str | None = None,
    secret_manager: SecretManager | None = None,
) -> ExecutionResult:
    """Execute Python code inside an e2b sandbox with network egress disabled."""

    _validate_code_safety(code)
    sandbox = _create_sandbox(api_key=_resolve_api_key(api_key, secret_manager=secret_manager), timeout=timeout)
    with sandbox:
        baseline = _snapshot_files(sandbox.files)
        uploaded: set[str] = set()

        if files:
            uploaded = _upload_files(sandbox.files, files)

        try:
            execution = sandbox.run_code(code, timeout=timeout)
        except TimeoutError as exc:
            raise TimeoutError("Sandbox execution timed out") from exc
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise ExecutionFailed("Sandbox execution failed") from exc

        _ensure_success(execution)

        logs = getattr(execution, "logs", None)
        stdout_lines = getattr(logs, "stdout", []) if logs else []
        stderr_lines = getattr(logs, "stderr", []) if logs else []

        files_out = _collect_new_files(sandbox.files, baseline, uploaded)

        return ExecutionResult(
            stdout="\n".join(stdout_lines),
            stderr="\n".join(stderr_lines),
            files=files_out,
            results=getattr(execution, "results", []),
        )


__all__ = ["ExecutionResult", "ExecutionFailed", "SandboxUnavailableError", "execute_python"]

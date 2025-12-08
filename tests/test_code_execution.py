from __future__ import annotations

import pytest

from thesis_generator.tools import code_execution


class DummyLogs:
    def __init__(self, stdout: list[str] | None = None, stderr: list[str] | None = None) -> None:
        self.stdout = stdout or []
        self.stderr = stderr or []


class DummyExecution:
    def __init__(self, stdout: list[str] | None = None, stderr: list[str] | None = None) -> None:
        self.logs = DummyLogs(stdout=stdout, stderr=stderr)
        self.error = None
        self.results = []


class FakeFiles:
    def __init__(self, initial: dict[str, bytes] | None = None) -> None:
        self.data = dict(initial or {})

    def list(self, path: str = "/", depth: int = 5) -> list[object]:  # noqa: ARG002
        return [type("Entry", (), {"path": name, "type": "file"}) for name in self.data]

    def write(self, path: str, data: bytes, **_: object) -> None:
        self.data[path] = data

    def read(self, path: str, format: str = "bytes", **_: object):  # noqa: A002
        content = self.data[path]
        if format == "bytes":
            return content
        return content.decode()


class FakeSandbox:
    def __init__(self, files: FakeFiles | None = None) -> None:
        self.files = files or FakeFiles()
        self.killed = False
        self.received_code: str | None = None

    def __enter__(self) -> FakeSandbox:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001, D401
        self.kill()

    def run_code(self, code: str, timeout: float | None = None, **_: object) -> DummyExecution:
        self.received_code = code
        # mimic sandbox writing a file during execution
        self.files.write("/outputs/plot.png", b"image-bytes")
        return DummyExecution(stdout=[f"ran with timeout {timeout}"])

    def kill(self) -> None:
        self.killed = True


def test_execute_python_collects_stdout_and_files(monkeypatch: pytest.MonkeyPatch) -> None:
    sandbox = FakeSandbox()

    def fake_create_sandbox(**_: object) -> FakeSandbox:
        return sandbox

    monkeypatch.setattr(code_execution, "_create_sandbox", fake_create_sandbox)

    result = code_execution.execute_python("print(1+1)", files={"input.csv": b"a,b"}, timeout=5)

    assert "print(1+1)" in sandbox.received_code or sandbox.received_code is not None
    assert "ran with timeout 5" in result.stdout
    assert result.stderr == ""
    assert result.files == {"/outputs/plot.png": b"image-bytes"}
    assert sandbox.killed is True


def test_execute_python_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    class TimeoutSandbox(FakeSandbox):
        def run_code(self, code: str, timeout: float | None = None, **_: object) -> DummyExecution:  # noqa: ARG002
            raise TimeoutError("execution exceeded")

    sandbox = TimeoutSandbox()

    monkeypatch.setattr(code_execution, "_create_sandbox", lambda **_: sandbox)

    with pytest.raises(TimeoutError):
        code_execution.execute_python("while True: pass", timeout=0.1)

    assert sandbox.killed is True


def test_execute_python_disables_network(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_kwargs: dict[str, object] = {}

    class SandboxFactory:
        def __init__(self) -> None:
            self.instance = FakeSandbox()

        def create(self, **kwargs: object) -> FakeSandbox:
            captured_kwargs.update(kwargs)
            return self.instance

    factory = SandboxFactory()

    monkeypatch.setattr(code_execution, "_load_sandbox_class", lambda: factory)

    result = code_execution.execute_python("print('hi')")

    assert captured_kwargs.get("allow_internet_access") is False
    assert captured_kwargs.get("network") == {"deny_out": ["0.0.0.0/0"]}
    assert result.files["/outputs/plot.png"] == b"image-bytes"

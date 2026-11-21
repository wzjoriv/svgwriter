from __future__ import annotations

import ast
import importlib
from functools import cache
from pathlib import Path
from types import ModuleType

import pytest

PACKAGE = Path(__file__).resolve().parent.parent / "svgwriter"
SHARED = "svgwriter._internal"


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(PACKAGE.parent).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


@cache
def _is_package(name: str) -> bool:
    return PACKAGE.parent.joinpath(*name.split("."), "__init__.py").is_file()


MODULES = {_module_name(path): path for path in sorted(PACKAGE.rglob("*.py"))}


def _private(part: str) -> bool:
    return part.startswith("_") and not (part.startswith("__") and part.endswith("__"))


def _violates(importer: str, target: str) -> bool:
    parts = target.split(".")
    if parts[0] != "svgwriter":
        return False
    for index in range(1, len(parts)):
        if not _private(parts[index]):
            continue
        prefix = ".".join(parts[: index + 1])
        if prefix == SHARED or prefix.startswith(SHARED + "."):
            continue
        holder = ".".join(parts[:index])
        owner = holder if _is_package(holder) else holder.rpartition(".")[0]
        if importer != owner and not importer.startswith(owner + "."):
            return True
    return False


def _targets(importer: str, tree: ast.Module) -> list[tuple[int, str]]:
    package = importer if _is_package(importer) else importer.rpartition(".")[0]
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")[: len(package.split(".")) - node.level + 1]
                source = ".".join(base + ([node.module] if node.module else []))
            else:
                source = node.module or ""
            found.extend((node.lineno, f"{source}.{alias.name}") for alias in node.names if alias.name != "*")
    return found


def _violations() -> list[str]:
    report: list[str] = []
    for importer, path in MODULES.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for line, target in _targets(importer, tree):
            if _violates(importer, target):
                report.append(f"{path.relative_to(PACKAGE.parent).as_posix()}:{line} -> {target}")
    return report


def test_private_modules_stay_inside_their_package() -> None:
    violations = _violations()
    assert not violations, "private imports across package boundaries:\n" + "\n".join(violations)


def test_internal_imports_no_public_package_at_load() -> None:
    report = []
    for importer, path in MODULES.items():
        if not importer.startswith(SHARED):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        body = ast.Module(body=[node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))], type_ignores=[])
        for line, target in _targets(importer, body):
            if target.startswith("svgwriter.") and not target.startswith(SHARED + "."):
                report.append(f"{path.relative_to(PACKAGE.parent).as_posix()}:{line} -> {target}")
    assert not report, "svgwriter._internal imports public packages at load time:\n" + "\n".join(report)


def test_rule_examples() -> None:
    assert _violates("svgwriter.export._flatten", "svgwriter.ops._renderable.Renderable")
    assert not _violates("svgwriter.export._flatten", "svgwriter._internal._drawable.Drawable")
    assert not _violates("svgwriter.ops.render", "svgwriter.ops._fonts.load")
    assert _violates("svgwriter.export._flatten", "svgwriter.ops.render._view")
    assert not _violates("svgwriter.ops.text", "svgwriter.ops.render._view")


PUBLIC_MODULES = sorted(name for name in MODULES if not any(_private(part) for part in name.split(".")))


@pytest.mark.parametrize("name", PUBLIC_MODULES)
def test_all_names_exist(name: str) -> None:
    module = importlib.import_module(name)
    for exported in getattr(module, "__all__", ()):
        assert hasattr(module, exported), f"{name}.__all__ lists missing {exported!r}"
        value = getattr(module, exported)
        if isinstance(value, ModuleType):
            owner, _, leaf = value.__name__.rpartition(".")
            assert leaf == exported and (owner == name or owner.startswith(f"{name}.")), f"{name}.{exported} is {value.__name__}"

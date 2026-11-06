"""Keeps the structure honest, so it can't quietly decay. See CONTRIBUTING.md."""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "shophelper"

# Each folder may import only these. Imports inside functions count too.
ALLOWED = {
    "core": set(),
    "shop": {"core"},
    "accounts": {"core", "shop"},
    "rag": {"core"},
    "agent": {"core", "shop", "accounts", "rag"},
    "mcp": {"core", "shop", "accounts", "agent"},
    "api": {"core", "shop", "accounts", "rag", "agent", "mcp"},
}
LIVE_DOCS = ["README.md", "CLAUDE.md", "docs/**/*.md", "specs/*.md"]
PROJECT_PATH = re.compile(r"(?:src/shophelper|web/src)/[\w./-]+\.\w+")


def folders_imported_by(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        names = []
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module, *(f"{node.module}.{a.name}" for a in node.names)]
        elif isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        for name in names:
            parts = name.split(".")
            if parts[0] == "shophelper" and len(parts) > 1 and parts[1] in ALLOWED:
                found.add(parts[1])
    return found


def forbidden_imports(package: Path) -> list[str]:
    problems = []
    for folder, allowed in ALLOWED.items():
        for path in (package / folder).rglob("*.py"):
            for imported in folders_imported_by(path) - allowed - {folder}:
                problems.append(f"{path.relative_to(package)} imports {imported}")
    return problems


def missing_paths(root: Path, patterns: list[str]) -> list[str]:
    problems = []
    for pattern in patterns:
        for doc in root.glob(pattern):
            for mention in PROJECT_PATH.findall(doc.read_text(encoding="utf-8")):
                if "*" not in mention and not (root / mention.rstrip(".")).exists():
                    problems.append(f"{doc.relative_to(root)} mentions {mention}")
    return problems


def test_imports_point_one_way():
    assert forbidden_imports(PACKAGE) == []


def test_the_import_rule_catches_a_forbidden_import(tmp_path):
    (tmp_path / "core").mkdir()
    (tmp_path / "core" / "bad.py").write_text("def f():\n    from shophelper.api import app\n")
    assert forbidden_imports(tmp_path) == [f"{Path('core/bad.py')} imports api"]


def test_paths_in_live_docs_exist():
    assert missing_paths(ROOT, LIVE_DOCS) == []


def test_the_path_check_catches_a_missing_file(tmp_path):
    (tmp_path / "README.md").write_text("See src/shophelper/gone.py and web/src/gone.tsx.")
    assert len(missing_paths(tmp_path, ["README.md"])) == 2


@pytest.mark.parametrize("pattern", LIVE_DOCS)
def test_the_doc_patterns_find_something(pattern):
    assert list(ROOT.glob(pattern))  # a typo here would make the path check pass by seeing nothing

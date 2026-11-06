"""Every lesson keeps the promises the course makes. See specs/features/022-learning-website/spec.md."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LEARN = ROOT / "docs" / "learn"
WORDS_PER_MINUTE = 200
MAX_MINUTES = 15
REQUIRED = ["What you'll learn", "The simple explanation", "An example"]
SHOPHELPER = ("How ShopHelper does it", "Not in ShopHelper")
ORDER = [*REQUIRED, *SHOPHELPER, "In the market", "Try it", "Interview questions", "Check yourself"]


def split_front(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}, text
    pairs = (line.split(":", 1) for line in match.group(1).splitlines())
    return {key.strip(): value.strip() for key, value in pairs}, text[match.end():]


def sections(body: str) -> dict[str, str]:
    parts = re.split(r"^## (.+)$", strip_code(body, keep=True), flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def strip_code(body: str, keep: bool = False) -> str:
    """Headings inside a code fence aren't headings."""
    out, fenced = [], False
    for line in body.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            if keep:
                out.append(line)
            continue
        if keep and fenced:
            out.append(" " + line)
        elif not fenced:
            out.append(line)
    return "\n".join(out)


def minutes(body: str) -> float:
    return len(strip_code(body).split()) / WORDS_PER_MINUTE


def format_problems(text: str) -> list[str]:
    """What's wrong with a finished lesson. Carried-over chapters are restyled in their own slice."""
    front, body = split_front(text)
    found = sections(body)
    names = list(found)
    problems = [f"no {part}" for part in REQUIRED if part not in found]
    if not any(part in found for part in SHOPHELPER):
        problems.append("no ShopHelper section")
    known = [name for name in names if name in ORDER]
    if known != sorted(known, key=ORDER.index):
        problems.append("parts out of order")
    if not front.get("title"):
        problems.append("no title")
    if minutes(body) > MAX_MINUTES:
        problems.append("over 15 minutes")

    questions = re.split(r"^### ", found.get("Interview questions", ""), flags=re.MULTILINE)[1:]
    if len(questions) < 2:
        problems.append("under 2 interview questions")
    for question in questions:
        if "**Strong answer:**" not in question or "**Follow-up:**" not in question:
            problems.append("an interview question lacks an answer or follow-up")

    checks = re.split(r"^### ", found.get("Check yourself", ""), flags=re.MULTILINE)[1:]
    if len(checks) < 2:
        problems.append("under 2 check questions")
    for check in checks:
        options = re.findall(r"^- \[([ x])\] (.+)$", check, flags=re.MULTILINE)
        if sum(mark == "x" for mark, _ in options) != 1 or len(options) < 2:
            problems.append("a check question needs one right answer")
        if not all(" — " in text for _, text in options):
            problems.append("a check answer gives no feedback")

    market = found.get("In the market")
    if market is not None:
        if not re.search(r"Checked on \d{4}-\d{2}-\d{2}", market):
            problems.append("market section has no date")
        if not re.search(r"\]\(https?://", market):
            problems.append("market section has no source")
    return problems


def snippet_problems(text: str, root: Path) -> list[str]:
    problems = []
    fences = re.findall(r"^```\w* file=(\S+)\n(.*?)^```", text, flags=re.MULTILINE | re.DOTALL)
    for name, code in fences:
        source = root / name
        if not source.exists():
            problems.append(f"{name} doesn't exist")
            continue
        lines = {line.strip() for line in source.read_text(encoding="utf-8").splitlines()}
        for line in code.splitlines():
            if line.strip() and line.strip() != "..." and line.strip() not in lines:
                problems.append(f"{name} no longer has: {line.strip()}")
    return problems


def link_problems(path: Path) -> list[str]:
    problems = []
    body = strip_code(path.read_text(encoding="utf-8"))
    for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", body):
        if not target.startswith(("http://", "https://", "mailto:")) and not (path.parent / target).exists():
            problems.append(f"{path.relative_to(ROOT)} links to {target}")
    return problems


def course() -> dict:
    return json.loads((LEARN / "course.json").read_text(encoding="utf-8"))


def lessons() -> list[Path]:
    stages = course()["stages"]
    return [LEARN / stage["id"] / f"{lesson}.md" for stage in stages for lesson in stage["lessons"]]


GOOD = """---
title: A lesson
checked: 2026-11-06
---

## What you'll learn
Things.

## The simple explanation
Words.

## An example
More words.

## Not in ShopHelper
Not built.

## In the market
Checked on 2026-11-06. [Source](https://example.com).

## Interview questions

### First?
**Strong answer:** Yes.
**Follow-up:** Why?

### Second?
**Strong answer:** No.
**Follow-up:** Why not?

## Check yourself

### One?
- [x] Right — because.
- [ ] Wrong — because not.

### Two?
- [ ] Wrong — because not.
- [x] Right — because.
"""


def test_a_good_lesson_passes():
    assert format_problems(GOOD) == []


@pytest.mark.parametrize(("old", "new", "problem"), [
    ("## An example", "## Another thing", "no An example"),
    ("## Not in ShopHelper", "## Something else", "no ShopHelper section"),
    ("title: A lesson", "name: A lesson", "no title"),
    ("Checked on 2026-11-06.", "Checked lately.", "market section has no date"),
    ("[Source](https://example.com)", "Source", "market section has no source"),
    ("**Follow-up:** Why?", "", "an interview question lacks an answer or follow-up"),
    ("### Second?\n**Strong answer:** No.\n**Follow-up:** Why not?\n", "", "under 2 interview questions"),
    ("- [x] Right — because.\n- [ ] Wrong — because not.\n\n### Two?",
     "- [ ] Right — because.\n- [ ] Wrong — because not.\n\n### Two?",
     "a check question needs one right answer"),
    ("- [ ] Wrong — because not.\n\n### Two?", "- [ ] Wrong\n\n### Two?", "a check answer gives no feedback"),
    ("Words.", "word " * 3100, "over 15 minutes"),
])
def test_each_rule_catches_a_broken_lesson(old, new, problem):
    assert old in GOOD
    assert problem in format_problems(GOOD.replace(old, new))


def test_parts_must_stay_in_order():
    moved = GOOD.replace("## An example\nMore words.\n\n", "") + "\n## An example\nMore words.\n"
    assert "parts out of order" in format_problems(moved)


def test_a_heading_inside_code_is_not_a_part():
    found = sections("## The simple explanation\n```\n## An example\n```\n")
    assert "## An example" in found["The simple explanation"]


def test_a_snippet_must_match_its_file(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\ny = 2\n")
    assert snippet_problems("```python file=a.py\nx = 1\n...\ny = 2\n```\n", tmp_path) == []
    assert snippet_problems("```python file=a.py\nz = 3\n```\n", tmp_path) == ["a.py no longer has: z = 3"]
    assert snippet_problems("```python file=gone.py\nx\n```\n", tmp_path) == ["gone.py doesn't exist"]


def test_the_course_has_all_13_stages():
    assert len(course()["stages"]) == 13


def test_every_listed_lesson_exists():
    assert [str(path) for path in lessons() if not path.exists()] == []


def test_finished_lessons_keep_the_format():
    for path in lessons():
        text = path.read_text(encoding="utf-8")
        if split_front(text)[0].get("carried") != "true":
            assert format_problems(text) == [], path.name


def test_every_lesson_has_a_title():
    for path in lessons():
        assert split_front(path.read_text(encoding="utf-8"))[0].get("title"), path.name


def test_code_examples_still_match_the_project():
    for path in lessons():
        assert snippet_problems(path.read_text(encoding="utf-8"), ROOT) == [], path.name


def test_every_link_works():
    docs = [*(ROOT / "docs").rglob("*.md"), ROOT / "README.md"]
    assert [problem for doc in docs for problem in link_problems(doc)] == []

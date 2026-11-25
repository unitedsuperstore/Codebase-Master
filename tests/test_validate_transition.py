from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_transition import load_health_checks, validate_transition_docs  # noqa: E402


VALID_MAP = """# Map
## Project at a glance
A project.
## Architecture
A module.
## Repository structure
- `src/app.py`
## Important flows
Request to response.
## Data and integrations
No external data.
## Development and operations
Run `python -m unittest`.
## Tests and known gaps
Tests exist.
## Risks and limitations
No known risks.
## Inspection notes
Reviewed source and tests.
"""
VALID_HANDOFF = """# Handoff
## Goal
Continue the requested feature.
## Current state
Verified state is recorded.
## Working tree and constraints
Preserve current changes.
## Recommended next steps
1. Run relevant tests.
## Commands and checks
| Command | Result |
|---|---|
## Handoff prompt
Continue only the requested task.
"""


class TransitionValidationTests(unittest.TestCase):
    def test_no_transition_docs_is_a_warning_not_a_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            errors, warnings = validate_transition_docs(Path(temporary))
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)

    def test_requires_both_map_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "CODEBASE_MAP.md").write_text(VALID_MAP, encoding="utf-8")
            errors, _ = validate_transition_docs(root)
        self.assertTrue(any("requires both documents" in error for error in errors))

    def test_accepts_complete_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "CODEBASE_MAP.md").write_text(VALID_MAP, encoding="utf-8")
            (root / "AI_HANDOFF.md").write_text(VALID_HANDOFF, encoding="utf-8")
            errors, warnings = validate_transition_docs(root)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_finds_missing_sections_and_unresolved_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "CODEBASE_MAP.md").write_text("# Map\n## Architecture\n[date]\n", encoding="utf-8")
            (root / "AI_HANDOFF.md").write_text(VALID_HANDOFF, encoding="utf-8")
            errors, _ = validate_transition_docs(root)
        self.assertTrue(any("missing section" in error for error in errors))
        self.assertTrue(any("unresolved template placeholder" in error for error in errors))

    def test_detects_custom_architecture_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            architecture_map = VALID_MAP.replace("A module.", "A module with [runtime boundary].")
            (root / "CODEBASE_MAP.md").write_text(architecture_map, encoding="utf-8")
            (root / "AI_HANDOFF.md").write_text(VALID_HANDOFF, encoding="utf-8")
            errors, _ = validate_transition_docs(root)
        self.assertTrue(any("unresolved template placeholder" in error for error in errors))

    def test_does_not_treat_markdown_link_labels_as_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("print('ok')\n", encoding="utf-8")
            architecture_map = VALID_MAP.replace("A module.", "A module; see [application entry](src/app.py).")
            (root / "CODEBASE_MAP.md").write_text(architecture_map, encoding="utf-8")
            (root / "AI_HANDOFF.md").write_text(VALID_HANDOFF, encoding="utf-8")
            errors, _ = validate_transition_docs(root)
        self.assertEqual(errors, [])

    def test_does_not_treat_mermaid_labels_as_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            architecture_map = VALID_MAP + "\n```mermaid\nflowchart LR\n    User[Python caller] --> Store[TaskStore]\n```\n"
            (root / "CODEBASE_MAP.md").write_text(architecture_map, encoding="utf-8")
            (root / "AI_HANDOFF.md").write_text(VALID_HANDOFF, encoding="utf-8")
            errors, _ = validate_transition_docs(root)
        self.assertEqual(errors, [])

    def test_finds_broken_local_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "CODEBASE_MAP.md").write_text(VALID_MAP + "\n[missing](docs/not-here.md)\n", encoding="utf-8")
            (root / "AI_HANDOFF.md").write_text(VALID_HANDOFF, encoding="utf-8")
            errors, _ = validate_transition_docs(root)
        self.assertTrue(any("broken local link" in error for error in errors))

    def test_loads_argument_array_health_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "checks.json"
            path.write_text(json.dumps({"checks": [{"name": "unit", "command": ["python3", "-m", "unittest"], "timeout_seconds": 60}]}), encoding="utf-8")
            checks, errors, warnings = load_health_checks(path)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(checks[0]["name"], "unit")

    def test_rejects_shell_string_health_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "checks.json"
            path.write_text(json.dumps({"checks": [{"name": "unsafe", "command": "pytest"}]}), encoding="utf-8")
            checks, errors, _ = load_health_checks(path)
        self.assertEqual(checks, [])
        self.assertTrue(any("array of non-empty strings" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Validate Codebase-Master transition documents and configured project checks."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

MAP_SECTIONS = (
    "Project at a glance",
    "Architecture",
    "Repository structure",
    "Important flows",
    "Data and integrations",
    "Development and operations",
    "Tests and known gaps",
    "Risks and limitations",
    "Inspection notes",
)
HANDOFF_SECTIONS = (
    "Goal",
    "Current state",
    "Working tree and constraints",
    "Recommended next steps",
    "Commands and checks",
    "Handoff prompt",
)
PLACEHOLDER_PATTERNS = (
    r"\[TODO\b",
    r"\[date\]",
    r"\[name,\s*branch,\s*short commit\]",
    r"\[paths and flows inspected",
    r"\[Describe major components",
    r"\[entry point\]",
    r"\[modules/services\]",
    r"\[data or result\]",
    r"\[environment variable names",
    r"\[Security, reliability",
    r"\[What was inspected",
    r"\[What the project is intended",
    r"\[Current git status",
    r"\[Smallest safe, high-value next action",
    r"\[passed / failed / not run\]",
    r"\[specific next step\]",
)
PLACEHOLDER_RE = re.compile("|".join(PLACEHOLDER_PATTERNS), re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def _check_document(
    root: Path, relative_path: str, required_sections: tuple[str, ...]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return [f"Document path escapes repository root: {relative_path}"], errors

    if not path.is_file():
        return [f"Missing required transition document: {relative_path}"], errors

    text = path.read_text(encoding="utf-8")
    headings = {heading.strip().casefold() for heading in HEADING_RE.findall(text)}
    for section in required_sections:
        if section.casefold() not in headings:
            errors.append(f"{relative_path}: missing section '## {section}'")

    match = PLACEHOLDER_RE.search(text)
    if match:
        errors.append(
            f"{relative_path}: unresolved template placeholder near {match.group(0)!r}"
        )

    for target in LINK_RE.findall(text):
        target = target.strip().split()[0].strip("<>") if target.strip() else ""
        if not target or target.startswith(("https://", "http://", "mailto:", "#")):
            continue
        local_target = target.split("#", 1)[0].split("?", 1)[0]
        if not local_target:
            continue
        linked_path = (path.parent / local_target).resolve()
        try:
            linked_path.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{relative_path}: link escapes repository: {target}")
            continue
        if not linked_path.exists():
            errors.append(f"{relative_path}: broken local link: {target}")

    return errors, []


def validate_transition_docs(
    root: Path, map_path: str = "CODEBASE_MAP.md", handoff_path: str = "AI_HANDOFF.md"
) -> tuple[list[str], list[str]]:
    """Validate both transition documents, warning if neither has been created yet."""
    map_exists = (root / map_path).is_file()
    handoff_exists = (root / handoff_path).is_file()
    if not map_exists and not handoff_exists:
        return [], [
            f"No {map_path} or {handoff_path} found; transition-document checks were skipped."
        ]
    if map_exists != handoff_exists:
        missing = handoff_path if map_exists else map_path
        return [f"Transition requires both documents; missing {missing}"], []

    map_errors, _ = _check_document(root, map_path, MAP_SECTIONS)
    handoff_errors, _ = _check_document(root, handoff_path, HANDOFF_SECTIONS)
    return map_errors + handoff_errors, []


def load_health_checks(config_path: Path) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Load argument-array checks from JSON; never interpret commands through a shell."""
    if not config_path.is_file():
        return [], [], [f"No health-check configuration found at {config_path}; no project checks configured."]
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"Could not read health-check configuration: {exc}"], []

    if not isinstance(data, dict) or not isinstance(data.get("checks"), list):
        return [], ["Health-check configuration must be a JSON object with a 'checks' array."], []

    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, item in enumerate(data["checks"]):
        label = f"checks[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object.")
            continue
        name = item.get("name")
        command = item.get("command")
        timeout = item.get("timeout_seconds", 300)
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label}.name must be a non-empty string.")
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(part, str) or not part for part in command)
        ):
            errors.append(f"{label}.command must be a non-empty array of non-empty strings.")
        if not isinstance(timeout, int) or timeout < 1 or timeout > 900:
            errors.append(f"{label}.timeout_seconds must be an integer from 1 to 900.")
        if isinstance(name, str) and name.strip() and isinstance(command, list) and command and all(
            isinstance(part, str) and part for part in command
        ) and isinstance(timeout, int) and 1 <= timeout <= 900:
            checks.append({"name": name, "command": command, "timeout_seconds": timeout})

    if not checks and not errors:
        return [], [], ["No project health checks are configured; only document validation can run."]
    return checks, errors, []


def run_health_checks(root: Path, config_path: Path) -> tuple[list[str], list[str]]:
    checks, errors, warnings = load_health_checks(config_path)
    for warning in warnings:
        print(f"::warning::{warning}")
    for error in errors:
        print(f"::error::{error}")
    if errors:
        return errors, warnings

    failures: list[str] = []
    for check in checks:
        command = check["command"]
        print(f"Running configured health check: {check['name']} — {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                cwd=root,
                timeout=check["timeout_seconds"],
                check=False,
            )
        except FileNotFoundError as exc:
            failures.append(f"{check['name']}: executable not found: {exc.filename}")
        except subprocess.TimeoutExpired:
            failures.append(f"{check['name']}: timed out after {check['timeout_seconds']} seconds")
        else:
            if result.returncode != 0:
                failures.append(f"{check['name']}: exited with status {result.returncode}")
    for failure in failures:
        print(f"::error::{failure}")
    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--map", dest="map_path", default="CODEBASE_MAP.md")
    parser.add_argument("--handoff", dest="handoff_path", default="AI_HANDOFF.md")
    parser.add_argument(
        "--checks-config", type=Path, default=Path(".github/codebase-master-checks.json")
    )
    parser.add_argument(
        "--run-health-checks",
        action="store_true",
        help="Run the reviewed argument-array commands in the health-check JSON file.",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    config_path = args.checks_config
    if not config_path.is_absolute():
        config_path = root / config_path

    errors, warnings = validate_transition_docs(root, args.map_path, args.handoff_path)
    for warning in warnings:
        print(f"::warning::{warning}")
    for error in errors:
        print(f"::error::{error}")

    if args.run_health_checks:
        check_errors, check_warnings = run_health_checks(root, config_path)
        errors.extend(check_errors)
        warnings.extend(check_warnings)

    if errors:
        print(f"Transition validation failed with {len(errors)} error(s).")
        return 1
    print("Transition validation passed. Semantic architecture accuracy still requires agent review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

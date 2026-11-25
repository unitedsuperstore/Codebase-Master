---
name: codebase-transition-kit
description: Turn an existing software repository into a safe, reusable AI-agent transition setup. Use when asked to scaffold Codebase-Master handoff documents, a GitHub Actions transition gate, Claude Code prompt/config guidance, documentation, or optional GitHub publication.
---

# Codebase Transition Kit

Scaffold a portable agent-handoff setup in an existing software repository. Use the bundled templates and validator to add architecture-map and handoff guidance, transition-triggered CI checks, and a Claude Code prompt template. Keep all changes reviewable, project-specific, and safe.

## Workflow

### 1. Confirm scope and inspect the repository

1. Identify the repository root, branch, Git status, untracked files, current diffs, existing README/docs, project instructions, GitHub workflows, and Claude Code instructions.
2. Preserve all user changes. Do not reset, clean, stash, overwrite, or delete existing files. Merge into existing workflow/configuration only after reviewing its triggers, permissions, and behavior.
3. Confirm the requested outputs. A sensible default is to add or refresh `CODEBASE_MAP.md`, `AI_HANDOFF.md`, a transition-check workflow, a Claude Code prompt template, and concise README/playbook guidance.
4. Ask only when a consequential decision cannot be inferred safely, such as replacing an existing workflow, making a repository public, or running a project command with side effects.

### 2. Add transition documents

Use `templates/CODEBASE_MAP.template.md` and `templates/AI_HANDOFF.template.md` to create project-root documents when the user asks for a handoff. For a multi-component system or important runtime, deployment, data, security, or operational boundaries, use `templates/SOFTWARE_ARCHITECTURE_MAP.template.md` as the `CODEBASE_MAP.md` source; it retains the headings required by the validator. Inspect the code and current Git state; do not fill the templates from assumptions alone. Record coverage and limitations. Keep environment-variable names only, never secret values. If documents already exist, update minimally or ask before replacing.

### 3. Add the optional GitHub Actions transition gate

Copy and adapt:

- `templates/codebase-transition.yml` → `.github/workflows/codebase-transition.yml`
- `scripts/validate_transition.py` → `scripts/validate_transition.py`
- `templates/codebase-master-checks.json` → `.github/codebase-master-checks.json`

The workflow is intended to run on changes to `CODEBASE_MAP.md`, `AI_HANDOFF.md`, templates, and on manual dispatch. The validator checks the expected sections, unresolved template placeholders, and relative local links. It runs health commands only from the JSON `checks` list, where each command is an argument array (not a shell string).

Review and configure every project-specific command before enabling it. Existing dependencies and test setup may require a project-specific workflow. Never add secrets to this workflow; use least-privilege `contents: read`. Do not use `pull_request_target` to run untrusted pull-request code. A green workflow confirms only the checks it ran and document structure; it does not create or semantically verify an architecture map. Report an empty health-check list as “health checks not configured,” not as passed.

On failure, the bundled workflow emits an Actions error annotation and writes a summary with a direct run link. GitHub inbox/email delivery follows each user's notification settings; do not configure an external webhook or email without a supplied destination and authorization.

### 4. Add Claude Code guidance

Use `templates/CLAUDE_CODE_PROMPT.template.md` as a one-time handoff prompt or adapt it into project guidance. Explain that the incoming agent must inspect Git state, read project instructions, verify map/handoff claims, preserve local changes, and perform only the current user request. Do not overwrite an existing `CLAUDE.md`; merge only when requested. Describe the file as a prompt/configuration template, not a native system prompt format unless the target tool explicitly supports that format.

### 5. Document and test the setup

Update the repository README and transition playbook with:

- What files to add and why.
- Trigger behavior and exact checks performed.
- How to configure health commands and run the validator locally.
- What the workflow cannot verify and when an agent must inspect manually.
- How to pass the Claude Code prompt and handoff documents to the receiving agent.

Run `python3 -m unittest discover -s tests -v` if tests are bundled, run the validator against a representative temporary fixture, check JSON/YAML syntax and Markdown local links, inspect staged diffs, and record checks accurately. Simulate receiving-agent verification by independently checking the sample handoff's working-tree state and rerunning relevant tests. Do not claim an action has run on GitHub unless a workflow run is observed.

### 6. Publish only when requested

If the user asks to publish, use the session's authorized GitHub integration and the `github-workflow` skill when available. Check repository ownership and visibility, inspect the exact staged file set and diff, and preserve local changes. Create repositories as private by default; make one public only on explicit request. Commit/push only when authorized, then verify the remote branch and files. Never expose access tokens.

## Bundled resources

- `templates/CODEBASE_MAP.template.md` and `templates/AI_HANDOFF.template.md`: project handoff artifacts.
- `templates/SOFTWARE_ARCHITECTURE_MAP.template.md`: expanded software architecture map for multi-component systems and critical runtime/data boundaries.
- `templates/codebase-transition.yml`: workflow to validate transition documents and run configured health checks, with a GitHub-native failure annotation and run summary.
- `templates/codebase-master-checks.json`: project-check configuration example; adapt it to real commands.
- `templates/CLAUDE_CODE_PROMPT.template.md`: Claude Code receiving-agent prompt/config template.
- `scripts/validate_transition.py`: dependency-free structural and link validator plus safe argument-array command runner.

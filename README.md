# Codebase-Master

A portable, agent-neutral skill for understanding an existing software repository and handing it safely from one AI coding agent to another. It is especially useful when a project moves from Codex to Claude Code, but the same process works with any agent that can inspect files and run project commands.

- **Repository:** [unitedsuperstore/Codebase-Master](https://github.com/unitedsuperstore/Codebase-Master)
- **Primary instructions:** [`SKILL.md`](./SKILL.md)
- **Transition playbook:** [`docs/agent-transition-playbook.md`](./docs/agent-transition-playbook.md)

## What the skill does

Codebase-Master guides an AI agent to establish the real state of a project before it continues work. It inventories the repository, reads project instructions and configuration, traces key architecture and workflows, checks current Git changes, and distinguishes verified facts from assumptions and unknowns. It emphasizes preserving developer work and avoiding unsafe or unsupported claims.

When preparing a handoff, the agent adapts the included templates to create two Markdown documents in the **target software project**:

- **`CODEBASE_MAP.md`** — durable architecture and repository context: key packages and files, data flows, integrations, development commands, tests, risks, and inspection limits.
- **`AI_HANDOFF.md`** — time-sensitive continuation context: verified completed/in-progress work, blockers, current Git state, next steps, check results, and a ready-to-paste prompt for the next agent.

These files describe the project being handed off; they are not generated in this skill repository by default.

## Quick start

1. Give the agent access to the target project and its existing Git working tree. Do not replace or re-clone over a working directory that may contain local changes.
2. Make this repository's `SKILL.md`, templates, and playbook available. Install/register the skill using the receiving agent's documented method, or provide the Markdown files as context and ask the agent to follow them.
3. Ask the outgoing agent to map and prepare the handoff. For example:

   > Use Codebase-Master to map this repository and prepare a handoff for another AI coding agent. Inspect the current Git state first, preserve all work, verify important claims from code and tests, and create `CODEBASE_MAP.md` and `AI_HANDOFF.md` in the repository root. Do not start unrelated implementation.

4. Review the generated documents, especially Git state, unresolved questions, commands not run, and inspection limits.
5. Give the receiving agent the same project state, both handoff documents, applicable project instructions, and the current user request. Ask it to verify the relevant facts before editing.

See the [agent transition playbook](./docs/agent-transition-playbook.md) for the outgoing-to-incoming workflow and copy-ready prompts.

A handoff can happen at any point. “More than halfway complete” may be a reminder to consider a transition, but it is not a reliable completion measure. Use acceptance criteria when a progress estimate matters.

## Optional GitHub Actions transition gate

This repository includes a read-only workflow at [`.github/workflows/codebase-transition.yml`](./.github/workflows/codebase-transition.yml). It runs on manual dispatch and on push/pull-request changes to the transition documents or validator configuration. For another project, copy the workflow, [`scripts/validate_transition.py`](./scripts/validate_transition.py), and the configuration template to the target repository, then review and customize them before enabling the checks.

The validator checks that both transition documents are present together, required headings are included, template placeholders have been replaced, and relative Markdown links resolve. The workflow then runs the argument-array commands listed in [`.github/codebase-master-checks.json`](./.github/codebase-master-checks.json). Configure the target project’s commands in that JSON file, for example:

```json
{
  "checks": [
    {
      "name": "Unit tests",
      "command": ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
      "timeout_seconds": 300
    }
  ]
}
```

Use commands that are appropriate for the target project and available in its CI environment. The runner executes argument arrays without a shell. Review commands before adding them: tests execute repository code, so keep GitHub Actions permissions minimal and do not expose secrets to untrusted pull requests. The included workflow uses `contents: read` and no API/LLM credentials.

Run locally with:

```bash
python3 scripts/validate_transition.py --run-health-checks --checks-config .github/codebase-master-checks.json
python3 -m unittest discover -s tests -v
```

If neither handoff document exists, the validator warns and skips document validation; once either one exists, it requires both. If no project health checks are configured, it reports that health checks were not run. The action does **not** generate a map or prove its architecture claims are semantically accurate. The receiving agent must still compare the map with current code and tests.

## Claude Code prompt template

[`templates/CLAUDE_CODE_PROMPT.template.md`](./templates/CLAUDE_CODE_PROMPT.template.md) is a copy-ready prompt/configuration template for Claude Code as the receiving agent. It asks Claude to inspect the working tree, read project instructions and handoff files, verify relevant claims, preserve changes, and implement only the current request. Use it as supplied context or adapt it into project guidance; do not overwrite an existing `CLAUDE.md` without permission.

## Reusable setup skill

[`skills/codebase-transition-kit/SKILL.md`](./skills/codebase-transition-kit/SKILL.md) packages the setup process itself. Use it when you want an agent to scaffold these documents, the transition workflow, project-specific health checks, Claude Code guidance, and supporting README/playbook content in another repository.

## Safety and evidence principles

- Preserve uncommitted work. Inspect `git status` and diffs before editing; never reset, clean, stash, or overwrite project work during an audit.
- Read applicable `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, `README`, and contribution instructions while still following higher-priority safety requirements.
- Never copy credential values, tokens, private keys, or sensitive customer data into handoff artifacts. Record environment-variable names only.
- Run only relevant, safe checks that the available environment supports. Record exact commands and outcomes; distinguish “not run” from “passed.”
- Label claims as verified, inferred, or unknown. File names, TODOs, and previous agent statements are clues, not proof.
- Be accurate about coverage. Inventorying all tracked paths is not the same as reading every line of a large repository.
- Keep `CODEBASE_MAP.md` relatively durable and `AI_HANDOFF.md` concise and time-sensitive.

## Repository contents

| Path | Purpose |
|---|---|
| [`SKILL.md`](./SKILL.md) | Core Codebase-Master workflow and safety instructions |
| [`templates/CODEBASE_MAP.template.md`](./templates/CODEBASE_MAP.template.md) | Starting structure for a project architecture map |
| [`templates/AI_HANDOFF.template.md`](./templates/AI_HANDOFF.template.md) | Starting structure for an agent-to-agent handoff |
| [`templates/CLAUDE_CODE_PROMPT.template.md`](./templates/CLAUDE_CODE_PROMPT.template.md) | Claude Code receiving-agent prompt template |
| [`templates/workflows/codebase-transition.yml`](./templates/workflows/codebase-transition.yml) | Reusable Actions workflow template |
| [`templates/codebase-master-checks.json`](./templates/codebase-master-checks.json) | Example project-health-check configuration |
| [`scripts/validate_transition.py`](./scripts/validate_transition.py) | Dependency-free document and configured-check validator |
| [`.github/workflows/codebase-transition.yml`](./.github/workflows/codebase-transition.yml) | Workflow for this repository and future handoff updates |
| [`docs/agent-transition-playbook.md`](./docs/agent-transition-playbook.md) | Detailed outgoing/receiving-agent transition guidance |
| [`skills/codebase-transition-kit/`](./skills/codebase-transition-kit/) | Reusable setup skill and bundled resources |

## Limitations

Codebase-Master cannot infer undocumented product intent, prove unrun checks pass, or guarantee a line-by-line review of a large repository. Structural CI checks cannot establish whether an architecture map is semantically correct. The receiving agent should verify time-sensitive facts, inspect current working-tree state, and ask the user when evidence conflicts or a decision is unknown.

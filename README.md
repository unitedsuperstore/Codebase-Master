# Codebase-Master

A portable, agent-neutral skill for understanding an existing software repository and handing it safely from one AI coding agent to another. It is especially useful when a project has been developed in Codex and work is moving to Claude Code, but the same process works with any agent that can inspect files and run project commands.

- **Repository:** [unitedsuperstore/Codebase-Master](https://github.com/unitedsuperstore/Codebase-Master)
- **Primary instructions:** [`SKILL.md`](./SKILL.md)
- **Transition playbook:** [`docs/agent-transition-playbook.md`](./docs/agent-transition-playbook.md)

## What the skill does

Codebase-Master guides an AI agent to establish the real state of a project before it continues work. It inventories the repository, reads project instructions and configuration, traces key architecture and workflows, checks current Git changes, and distinguishes verified facts from assumptions and unknowns. It emphasizes preserving the developer's work and avoiding unsafe or unsupported claims.

When asked to prepare a handoff, the skill uses the included templates to create two portable Markdown documents in the project being reviewed:

- **`CODEBASE_MAP.md`** — durable architecture and repository context: key packages and files, data flows, integrations, development commands, tests, risks, and inspection limits.
- **`AI_HANDOFF.md`** — time-sensitive continuation context: what is done or in progress, blockers, current Git state, next steps, check results, and a ready-to-paste prompt for the next agent.

These are generated in the **target software project**, not in this skill repository. The templates are [`templates/CODEBASE_MAP.template.md`](./templates/CODEBASE_MAP.template.md) and [`templates/AI_HANDOFF.template.md`](./templates/AI_HANDOFF.template.md).

## Use it for

- Moving a partially completed project from Codex to Claude Code, or between any other coding agents.
- Onboarding an agent to a repository it has not seen before.
- Creating or refreshing an evidence-based architecture map and AI handoff.
- Auditing project structure, implementation status, tests, risks, and unknowns before making changes.

A handoff is useful at any point in a project. “More than halfway complete” can be a practical reminder to transition, but it is not a reliable completion measure. Do not ask an agent to invent a progress percentage; use an acceptance checklist if a percentage matters.

## Quick start

1. Give the agent access to the **target project repository** and its existing Git working tree. Do not replace or re-clone over a working directory that may contain local changes.
2. Make the instructions and templates in this repository available to the agent. In an agent that supports reusable skills, install or register `SKILL.md` according to that product's documented method. Otherwise, provide `SKILL.md` and this README as context and ask the agent to follow them. The Markdown workflow is tool-neutral; installation mechanics vary by agent.
3. Ask for the desired mode. For example:

   > Use Codebase-Master to map this repository and prepare a handoff for another AI coding agent. Inspect the current Git state first, preserve all work, verify important claims from the code, and create `CODEBASE_MAP.md` and `AI_HANDOFF.md` in the repository root. Do not start unrelated implementation.

4. Review the two resulting documents, especially the current Git state, unresolved questions, commands not run, and inspection limits.
5. Give the receiving agent access to the **same project state** and both handoff documents. Ask it to re-check current files and status before making changes; the handoff is context, not proof.

See the [agent transition playbook](./docs/agent-transition-playbook.md) for the full outgoing-to-incoming workflow and copy-ready prompts.

## Operating modes

- **Audit only:** report findings without changing the project.
- **Map and hand off:** create or update the two project-specific handoff documents after checking whether they already exist and preserving existing content.
- **Continue implementation:** establish the relevant project state first, then make only the changes the user requested.

A request to prepare a handoff is not permission to implement unrelated features, discard edits, install dependencies, run production operations, or change deployment state.

## Safety and evidence principles

- Preserve uncommitted work. Inspect `git status` and diffs before editing; never reset, clean, stash, or overwrite project work during an audit.
- Read applicable project guidance such as `AGENTS.md`, `CLAUDE.md`, `CODEX.md`, and contribution instructions, while still following higher-priority safety requirements.
- Never copy credential values, tokens, private keys, or sensitive customer data into the map or handoff. Variable names may be recorded without their values.
- Run only relevant, safe checks that the available environment supports. Record exact commands and results; distinguish “not run” from “passed.”
- Label claims **verified**, **inferred**, or **unknown**. File names, TODOs, and previous agent statements are clues, not proof.
- Be accurate about coverage. Inventorying all tracked paths is not the same as reading every line of a large repository.
- Keep the architecture map relatively durable and the handoff concise and time-sensitive.

## Repository contents

| Path | Purpose |
|---|---|
| [`SKILL.md`](./SKILL.md) | Core workflow and safety instructions for the AI agent |
| [`templates/CODEBASE_MAP.template.md`](./templates/CODEBASE_MAP.template.md) | Starting structure for a project architecture map |
| [`templates/AI_HANDOFF.template.md`](./templates/AI_HANDOFF.template.md) | Starting structure for an agent-to-agent handoff |
| [`docs/agent-transition-playbook.md`](./docs/agent-transition-playbook.md) | Detailed guidance for outgoing and receiving agents |

## Limitations

Codebase-Master cannot infer project intent that is not documented or supplied by the user, prove that unrun checks pass, or guarantee a complete line-by-line review of a large repository. The receiving agent should verify time-sensitive facts, inspect the current working tree, and ask the user when evidence conflicts or an important decision is unknown.

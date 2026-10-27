# Coding agent prompts

Choose the agent you use, copy its prompt, and run it from a clone of this repository.

- [Codex](#codex)
- [Claude Code](#claude-code)
- [Hermes Agent](#hermes-agent)
- [Other coding agents](#other-coding-agents)

## Codex

```text
Work in this repository as a maintenance coding agent. Before changing anything, read AGENTS.md, README.md, config.yaml, and the relevant file under .agents/skills/. Run `uv run python automation/harness.py status`, then inspect the source, validator, and regression tests for the behavior involved in my request. Preserve the export contract (`id`, `messages`, `tools`), tool and parameter names, group-level split isolation, explicit human acceptance, and financial safety rules. Make the smallest complete change, update every affected source/test/documentation path, and finish by running the closing checks listed in AGENTS.md. Report the files changed and the checks you actually ran.

Task: <describe the change>
```

## Claude Code

```text
Treat AGENTS.md as the repository contract. Read it together with README.md and config.yaml before editing, then load the relevant skill under .agents/skills/. Run `uv run python automation/harness.py status` and trace the requested behavior through its candidate builder, validator, storage/export path, and regression test. Do not invent a new behavior when one of the existing 16 applies. Preserve the three-field export schema, exact tool contracts, group-level split isolation, human acceptance boundary, and financial safety invariants. Implement the smallest complete change and run every closing check in AGENTS.md. Report only observed results.

Task: <describe the change>
```

## Hermes Agent

```text
Start by reading AGENTS.md, README.md, config.yaml, and the relevant .agents/skills/*/SKILL.md file. Run `uv run python automation/harness.py status` before editing. For the requested task, inspect the current implementation and tests together; follow existing patterns instead of creating a parallel pipeline. Keep exported records limited to `id`, `messages`, and `tools`; never translate tool or parameter identifiers; preserve group-level split isolation, explicit human review, and the financial safety rules. Complete all affected code, tests, and docs, then run the closing checks from AGENTS.md and report their real output.

Task: <describe the change>
```

## Other coding agents

```text
Read and follow AGENTS.md before making changes. Also read README.md, config.yaml, and the task-relevant skill under .agents/skills/. Run the repository status command, trace the requested behavior across generation, validation, review, export, and tests, and preserve every invariant in AGENTS.md. Make one complete minimal change, run the documented closing checks, and report only verified results.

Task: <describe the change>
```

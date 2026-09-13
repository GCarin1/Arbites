# AGENTS.md — Arbites

Operational source of truth for AI coding agents working in this
repository. Follows the open AGENTS.md standard.

## What this repo is

Arbites — Plataforma Local de Gestão e Rastreabilidade de Testes

This repository uses the Doctrina framework for spec-driven, AGENTS.md
native multi-agent development. The full framework artifacts live under
`.doctrina/`.

## Working from intent (you drive; the human stays passive)

You — the AI agent — run the Doctrina commands. The human gives a brief
prompt and approves; do not make them run the CLI or hand-author artifacts.

- **Bootstrap.** If `.doctrina/intake.md` is `Status: pending`, the specs
  are not written yet: run `doctrina intake` and execute the printed
  playbook in one pass (fill `product.md`, derive capabilities, one EARS
  spec each, `doctrina clarify --all` + `doctrina validate`, then flip the
  intake to `Status: converted`). After conversion the specs are the only
  source of truth — never edit `intake.md` to change requirements.
- **Day-to-day.** Turn any request into a change with `doctrina work
  "<prompt>"` and follow the printed playbook (spec delta → tasks →
  implement → analyze → apply → archive → validate). Unsure what to do
  next? Run `doctrina next`. Need to read? Run `doctrina context`. Ask the
  human only on genuine ambiguity.

<!-- doctrina:surface:begin — CLI-owned block, generated from the installed command catalog. Refreshed by `doctrina upgrade --write`; edits inside are overwritten. -->
## Doctrina command surface (generated — reach for these, don't hand-author)

Every command, with the moment you reach for it. The CLI scaffolds from
canonical templates and syncs `index.json`. Flags: `doctrina <cmd> --help`.
**Bootstrap**
- `doctrina init` — scaffold AGENTS.md and .doctrina/. *When:* starting a project that has no AGENTS.md yet.
- `doctrina intake` — store the intent and print the bootstrap playbook. *When:* you have a full project description and no specs yet.
- `doctrina adapter list|add|remove` — install/remove agent adapters (additive). *When:* adding or removing an agent's pointer files.
**Orient**
- `doctrina prime (session start)` — gates, open work and next steps in one read (--rules for the full standing rules). *When:* at the START of every session.
- `doctrina context [<cap>] --for "<task>" --concat` — the read pack, assembled to fit a token budget. *When:* before working on any task, to load the right files.
- `doctrina show` — point-read a single artifact by reference. *When:* you need one requirement, criterion, or ADR, not a file.
- `doctrina search` — search the artifact tree, grouped by category. *When:* you do not know which artifact mentions a term.
- `doctrina status` — index, coverage, trace, and artifact counts. *When:* you need the health of the tree at a glance.
- `doctrina next` — the recommended next workflow action. *When:* you finished something and do not know what follows.
- `doctrina why` — provenance: intent, proof, ADRs, and history. *When:* you need to justify or trace a capability's existence.
- `doctrina handoff (before compaction/handover)` — a resume note: open work, task state, next command. *When:* BEFORE compaction or handing over to another session.
**Change**
- `doctrina triage` — classify the lane (product/runtime/chore) and check the declared runtime surface. *When:* a request arrives — BEFORE scaffolding, especially if it smells like an incident.
- `doctrina work "<prompt>" (--capability · --chore · --from-diff · --quiet)` — scaffold a change and print the playbook to execute. *When:* a request arrives that changes behaviour (triage says PRODUCT).
- `doctrina spec new|list|set` — create, list, and edit capability specs. *When:* a capability needs creating or its headers advancing.
- `doctrina change new|apply|archive|check|tick|abandon` — new / apply / archive / check (--verbose) / tick / abandon. *When:* driving a change through its lifecycle by hand.
- `doctrina contract new|list|check` — own and verify the integration surface. *When:* the change touches ports, env vars, or public endpoints.
- `doctrina decision new|accept|land|supersede|list|scope` — record, accept, land, scope, and supersede ADRs. *When:* the change decides something a later session must not relitigate.
- `doctrina skill new|list|sync|suggest` — capture on-demand procedural memory. *When:* a lesson is worth not relearning.
- `doctrina intent add|list` — append and list product intent anchors. *When:* new product intent appears after the intake.
**Gate**
- `doctrina analyze` — structural pre-flight on a change folder. *When:* before applying a change.
- `doctrina clarify --all (--lang pt|en)` — smell-test Markdown for ambiguity. *When:* before applying, or before opening a PR.
- `doctrina validate (--fix)` — schema, structure, EARS, and index drift. *When:* after any artifact edit, and before considering work done.
- `doctrina coverage --strict` — acceptance criteria against cited evidence. *When:* before claiming a capability is proven.
- `doctrina trace --strict` — intent provenance across the tree. *When:* checking that product intent still maps to capabilities.
- `doctrina review` — conformance of your changes vs specs/ADRs/contracts. *When:* before handing work back, to self-review it.
- `doctrina verify` — the project's declared typecheck/test/build checks. *When:* the real build gate must run.
- `doctrina close <id...>` — the whole closing sequence in one attested pass. *When:* a change is implemented and ready to finish.
- `doctrina doctor` — aggregate diagnostic with per-finding remedies. *When:* something looks wrong and you do not know which gate to ask.
**Maintain** (triggers: `doctrina <command> --help`) — `doctrina templates list|check|update` · `doctrina hooks install` · `doctrina index rebuild` · `doctrina watch` · `doctrina metrics` · `doctrina report` · `doctrina completion` · `doctrina upgrade --write` · `doctrina ci --emit github`
<!-- doctrina:surface:end -->

<!-- doctrina:changed:begin — CLI-owned. Regenerated by `doctrina upgrade --write`. -->
## What changed in 0.16.0

- A reference or path that does not resolve now answers exit 2 (USAGE) everywhere — `clarify`, `show`, `why`, `analyze`, `context`, `change check`, `spec set`, `decision accept|scope`. Correct the invocation; retrying it unchanged never succeeds.
- The `--json` envelope names the OPERATION in `command` and carries arguments in `args` — branch on those two, not on a joined string. An undeclared flag now answers with `{ok: false, exit_code: 2}` instead of an empty stdout.
- `analyze` executes a MODIFIED delta's `ops` block, so `analyze`, `change apply` and `close` all refuse the same unappliable block. Fix the ops before closing; a delta with no ops block is still a legitimate manual merge.
- `validate` refuses more: an active spec declaring no acceptance criteria, an empty artifact, a scaffold section left unwritten, a reference that resolves to nothing. Write the criteria before flipping a spec to `active`.
- `change new <id>` requires the `NNNN-slug` shape (lowercase letters, digits, hyphens) and writes nothing otherwise — `doctrina work "<prompt>"` derives one for you.
<!-- doctrina:changed:end -->

## Stack and tooling

- Runtime: Python 3.12+ (FastAPI + Pydantic v2, uvicorn) · Node (React 18 + Vite + TypeScript)
- Package manager: pip/venv (backend) · npm (frontend)
- Test runner: pytest (backend)
- Índice: SQLite (stdlib) · Watcher: watchdog · Parsers: python-frontmatter, markdown-it-py, gherkin

## Commands

```
python -m pytest backend/tests -q     # test (backend)
npm --prefix frontend run build       # build (frontend)
doctrina verify                       # gate executável (roda os dois)
```

## Repository structure

<!-- Outline the top-level directories an agent needs to know about. -->

## Conventions and boundaries

- Specs in `.doctrina/specs/<capability>/spec.md` are the current truth.
- ADRs in `.doctrina/decisions/` are immutable; supersede instead of edit.
- Active change proposals live in `.doctrina/changes/<id>/`.
- Archived changes in `.doctrina/changes/archive/` are out of the default
  read path; consult only when explicitly debugging history.

## Artifact invariants (verbatim — `doctrina validate` enforces these)

Scaffold artifacts with the CLI (`doctrina decision new`, `doctrina work`),
which writes from the canonical templates. Do NOT hand-author these files
from memory. If you must write one by hand, match these exactly:

- **Metadata headers come in two forms — do not mix them up:**
  - ADRs, change proposals, and the intake use **list items**:
    `- **Status:** accepted`, `- **Date:** 2026-06-13`.
  - Specs use **bare bold** (no leading `- `):
    `**Status:** active`, `**Version:** 0.1.0`.
  Match the template for the artifact you are writing.
- **ADR filename** must be `NNNN-slug.md` — four digits, e.g.
  `0001-jwt-algorithm.md`. `ADR-001-...md` or `1-...md` is invisible to
  `doctrina decision accept`, the index, and the orphan check.
- **Change folder** at `.doctrina/changes/<id>/` must contain a file named
  exactly `proposal.md` (not `change.md`, not `README.md`). `tasks.md` and
  `design.md` are optional siblings.
- **Spec** lives at `.doctrina/specs/<capability>/spec.md` and its
  `**Version:**` header must equal the `version` recorded for it in
  `.doctrina/index.json`.
- **Every artifact on disk** must be registered in `.doctrina/index.json`,
  and every path in `index.json` must exist on disk. Update the index in
  the same change that adds or moves a file.

Always finish by running `doctrina validate` and resolving every `error:`
before considering work done.

## How to read context efficiently

`doctrina context [<capability>] --concat` assembles the read pack in one
call, in order: this `AGENTS.md` → `.doctrina/product.md` → the capability
spec → open `.doctrina/changes/<id>/` → `.doctrina/decisions/` filtered to
`Status: accepted`. Run it for ANY task, not only `doctrina work`; it skips
`changes/archive/` (history — read only when debugging it).

On demand only: if the task matches a skill in `.doctrina/skills/`, read its
`description:` / `when:` frontmatter; load the full body when the trigger fires.

Keep this file under 150 lines. Density beats prose. Use exact commands.

## Definition of done

A change is done when:
- All tasks in the change's `tasks.md` are checked.
- Deltas have been merged into affected spec files.
- The change folder has been moved to `.doctrina/changes/archive/`.
- Any architectural decisions are recorded as ADRs with `Status: accepted`.
- `.doctrina/index.json` has been updated.

## What never goes in this file

Tutorials, project history, secrets, generated content, session notes.

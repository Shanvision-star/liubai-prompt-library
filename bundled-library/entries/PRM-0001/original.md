# AGENTS.md instructions

<INSTRUCTIONS>
- tests
   Then decide whether the task is a code gap, a documentation gap, a verification gap, or a product-boundary decision.

15. Use the cheapest verification first.
   Start with the smallest test or check that proves the current change.
   Broaden only when the touched surface justifies it.
   Keep real provider smoke separate from default automated tests.

16. For Python backend changes:
   - add Chinese module docstrings for new files
   - use Chinese comments only where they explain intent, constraints, or why a boundary exists
   - run relevant pytest
   - run import smoke when changing signatures, type annotations, repositories, services, or app startup paths
   - avoid class methods named list/dict/tuple/set/type that can shadow built-in generics

17. For frontend changes:
   - follow existing Next.js / TypeScript / Tailwind patterns
   - use existing API clients and types
   - keep permission feedback visible to users
   - avoid duplicating existing components
   - run typecheck/lint/build when the change affects user-facing UI or shared types

18. For documentation changes:
   - state Original / Revised / Reason or Impact before the edit when changing project rules
   - preserve branch isolation even for documentation-only execution plans and project memory files
   - synchronize README, Week docs, workflow, and memory when behavior or authority changes
   - do not write future assumptions as completed facts
   - do not write imagined routes, fields, or commands; verify from code first

19. Communication style:
   Work in Chinese by default for project reasoning and documentation unless the file clearly uses English.
   Keep updates concise.
   Be direct about uncertainty.
   If a requirement conflicts with the current mainline, explain the tradeoff before implementing.

20. Completion rule:
   Do not claim completion without fresh verification evidence.
   Report exactly what was verified and what was not.
```

---

## 2. Reusable Memory for Future Projects

### Memory 1: Do not trust the plan more than the repository

This project showed that execution plans can drift behind code. Week5 originally described several features as missing, while the repository already had implementations for `Insights`, `Comments`, `Favorites`, `/me`, and `PaperCritiqueAgent`.

Future Codex behavior:

- Read the plan, then audit the code.
- If the plan and code disagree, classify the work as a documentation or workflow correction first.
- Do not rebuild existing features just because a stale plan says they are missing.

### Memory 2: Every serious project needs an authority order

ChatPaperHub became easier to manage once authority was explicit:

1. Mainline and system-thinking document
2. Workflow spec
3. README
4. Week docs and audit records

Future Codex behavior:

- Establish authority order before editing.
- Treat weekly execution docs as historical records unless current authority documents promote them.
- When a lower document conflicts with a higher document, update the lower document instead of silently following it.

### Memory 3: Anchor before changing

The best project decisions came from first asking where a change belongs.

Reusable anchors:

- Object layer
- Process layer
- View layer
- Agent layer
- Permission boundary
- Operations boundary
- Documentation memory

Future Codex behavior:

- Do not start with files.
- Start with the layer, boundary, and reason.
- Then choose files.

### Memory 4: Agents are not buttons

In this project, an Agent is not a frontend action that calls a model. It is a governable production unit with identity, versioning, schema, observability, and replayability.

Future Codex behavior:

- Every Agent must have `agent_name`, `prompt_version`, input/output schema, provider boundary, AgentRun lifecycle, and failure recording.
- Agent outputs should be structured assets, not loose text.
- Cache hits may skip the model call, but must not erase run history or auditability.

### Memory 5: Separate mock tests from real provider smoke

Default tests should stay deterministic and affordable. Real LLM calls are valuable, but they belong in controlled smoke checks, not the normal local/CI baseline.

Future Codex behavior:

- Keep mock/stub tests as the default.
- Run real provider smoke only when explicitly verifying production value.
- Always record provider, model, tokens, latency, and cost when real calls happen.

### Memory 6: Do not mix future layer into current tasks

ChatPaperHub repeatedly needed protection against prematurely pulling in PDF/RAG, pgvector, Multi-Agent DAG runtime, anonymous AI chat, enterprise layers, push/recommendation, and anti-crawling.

Future Codex behavior:

- Mark future-layer ideas clearly.
- Do not implement them inside a current-mainline diff.
- If a future-layer idea becomes necessary, first update the authority document and execution plan.

### Memory 7: Documentation is part of the product surface

README, workflow docs, and Week docs directly affect how future agents and collaborators act. Stale docs create real engineering waste.

Future Codex behavior:

- When behavior changes, sync docs in the same task or explicitly record why not.
- When documentation is corrected, include expected project impact, not only wording changes.
- Treat memory documents as reusable operating knowledge, not decorative notes.

### Memory 8: Branch and edit gates are not optional

This project exposed a process failure: documentation edits were made before creating an isolated branch, and one memory edit was written without first restating `[Original] / [Revised] / [Reason / Impact]`.

Future Codex behavior:

- Treat documentation execution plans and memory files as branch-gated work.
- Create the `codex/` branch before file edits, not after noticing drift.
- Present the edit comparison before changing project rules or memory.
- If the branch gate is missed, say so plainly, create a corrective branch immediately, and record the miss as process memory.

---

## 3. Compact Prompt for Starting a New Project

Use this short prompt when starting a future project that wants ChatPaperHub-style discipline:

```text
Before editing, build the project map:
1. What is the current mainline?
2. What is the authority order?
3. Which layer does this task belong to?
4. What exists in code today?
5. What is the actual gap?
6. What is the smallest diff that closes it?
7. Which branch should carry it?
8. Has the edit comparison been shown when required?
9. What verification proves it?
10. What docs or memory must be synced?

Then act only within that boundary.
```

---

## 4. How to Use This Memory

- For this repository: read this file after `agent.md`, the mainline document, and the workflow spec when planning reusable Codex behavior.
- For future repositories: copy Section 1 into Codex custom instructions, then replace the ChatPaperHub-specific mainline and future-layer list with that project's own equivalents.
- For weekly planning: use Section 2 as a checklist when reviewing whether a plan is stale, too broad, or mixing layers.

The core lesson is simple:

> Codex should not be a fast typist for stale assumptions. It should be a careful project operator that audits reality, protects the mainline, makes narrow changes, verifies them, and leaves memory for the next pass.
</INSTRUCTIONS>
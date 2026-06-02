---
name: postgresql-fetch-webpage-expert
description: 'PostgreSQL expert workflow using official docs and fetch_webpage. Use when designing schema, writing SQL, tuning performance, handling locks, debugging errors, planning backup/restore, replication, security, and operations with docs-backed guidance.'
argument-hint: 'Describe goal, PostgreSQL version, environment, schema/query context, and constraints (latency, throughput, HA, security)'
user-invocable: true
disable-model-invocation: false
---

# PostgreSQL + fetch_webpage Expert

Use this skill for production-grade PostgreSQL engineering with a docs-first approach. Every non-trivial recommendation should be validated against official PostgreSQL documentation.

## Outcome
- Deliver PostgreSQL guidance or implementation that is technically correct, version-aware, and traceable to official docs.
- Reduce guesswork by consulting the right chapter before proposing SQL, config, or operational changes.

## When to Use
- Query design and SQL correctness (joins, CTEs, window functions, DML).
- Schema and data type decisions (constraints, generated columns, JSONB, arrays, enums).
- Index strategy (B-tree, GIN, GiST, BRIN, partial, expression, covering indexes).
- Performance investigations (EXPLAIN/ANALYZE, planner stats, vacuum/analyze effects).
- Concurrency and locking issues (isolation, deadlocks, long transactions, serialization retries).
- Security and access control (roles, grants, RLS, pg_hba.conf, auth methods, SSL/TLS).
- Operations (backup/restore, PITR, WAL, replication, failover, monitoring).

## Inputs to Gather First
- PostgreSQL version and deployment target (self-managed, managed, containerized).
- Exact problem statement and success criteria.
- Current SQL/query or table/index definitions.
- Data profile: row count, cardinality, write/read mix, retention.
- Constraints: latency SLOs, downtime budget, security/compliance, recovery targets.
- Observability signals: EXPLAIN plan, lock view snapshots, error codes/messages.

## Core Workflow
1. Define scope and acceptance criteria.
2. Choose the relevant docs area and fetch only those pages with fetch_webpage.
3. Extract defaults, caveats, version notes, and command syntax from docs.
4. Propose a minimal safe change first (query rewrite, index, config, or runbook step).
5. Add validation plan (before/after metrics, EXPLAIN deltas, rollback path).
6. If production-impacting, include risk controls (lock impact, migration safety, backup step).
7. Present final recommendation with doc evidence summary.

## Mode Selection
- Use full workflow for schema design, migrations, tuning, incidents, security, HA, and recovery planning.
- Use quick checklist mode for focused tasks where speed matters and blast radius is low.

## Quick Checklist Mode
1. Restate the exact task in one sentence.
2. Fetch 1-3 highly relevant PostgreSQL 18 docs pages only.
3. Extract syntax, caveats, and one key risk.
4. Provide minimal implementation plus one verification query/check.
5. Add rollback or safe fallback note.

## Decision Points and Branching

### A) SQL and Schema
- If query is slow but logically correct: inspect [Performance Tips](https://www.postgresql.org/docs/18/performance-tips.html) and [Indexes](https://www.postgresql.org/docs/18/indexes.html) before rewriting business logic.
- If data shape is unclear: consult [Data Types](https://www.postgresql.org/docs/18/datatype.html) and [Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html).
- If introducing uniqueness or conditional access: prefer constraints and partial indexes validated against docs.

### B) Indexing
- If equality/range on scalar columns: start with B-tree guidance.
- If jsonb/array/text search patterns: evaluate GIN/GiST doc sections.
- If append-heavy large tables with natural ordering: evaluate BRIN trade-offs.
- If writes are degrading: quantify index maintenance overhead and prune redundant indexes.

### C) Performance
- If planner choice looks wrong: use docs for planner statistics and extended stats.
- If plan is unstable across environments: compare configuration and statistics freshness.
- If bulk load operation: use copy/populate recommendations and temporary tuning guardrails.

### D) Concurrency and Reliability
- If blocking/deadlocks: consult locking and monitoring chapters before changing isolation globally.
- If serialization failures: apply retry pattern supported by docs.
- If durability/performance tradeoff requested: document WAL and non-durable setting risks explicitly.

### E) Security and Access
- If connection fails: evaluate pg_hba.conf path, auth method, and role mapping.
- If privilege escalation risk: use roles/default privileges/RLS guidance from docs.
- If remote exposure: include TLS/auth hardening references.

### F) Backup, Restore, and HA
- If recovery objective is strict: prioritize PITR + WAL archival references.
- If failover design requested: compare synchronous vs asynchronous replication trade-offs.
- If operational runbook is missing: produce backup verification and restore drill steps.

## fetch_webpage Playbook

### 1) Query Design
Use targeted extraction requests that focus on defaults, caveats, and limitations.

Examples:
- "Extract syntax, prerequisites, and caveats for CREATE INDEX CONCURRENTLY in PostgreSQL 18 docs"
- "Summarize lock behavior and conflict points for ALTER TABLE operations"
- "Compare backup methods SQL dump vs filesystem vs continuous archiving from docs"

### 2) URL Selection Strategy
Start narrow and fetch only relevant sections:
- Entry:
  - https://www.postgresql.org/docs/18/index.html
- SQL and modeling:
  - https://www.postgresql.org/docs/18/sql.html
  - https://www.postgresql.org/docs/18/ddl.html
  - https://www.postgresql.org/docs/18/datatype.html
  - https://www.postgresql.org/docs/18/functions.html
- Query tuning and indexing:
  - https://www.postgresql.org/docs/18/performance-tips.html
  - https://www.postgresql.org/docs/18/indexes.html
  - https://www.postgresql.org/docs/18/using-explain.html
- Concurrency and locking:
  - https://www.postgresql.org/docs/18/mvcc.html
  - https://www.postgresql.org/docs/18/explicit-locking.html
  - https://www.postgresql.org/docs/18/monitoring-locks.html
- Admin and operations:
  - https://www.postgresql.org/docs/18/admin.html
  - https://www.postgresql.org/docs/18/runtime-config.html
  - https://www.postgresql.org/docs/18/maintenance.html
  - https://www.postgresql.org/docs/18/monitoring.html
- Security:
  - https://www.postgresql.org/docs/18/client-authentication.html
  - https://www.postgresql.org/docs/18/user-manag.html
- Recovery and HA:
  - https://www.postgresql.org/docs/18/backup.html
  - https://www.postgresql.org/docs/18/continuous-archiving.html
  - https://www.postgresql.org/docs/18/high-availability.html
  - https://www.postgresql.org/docs/18/logical-replication.html

### 3) Extraction Checklist
Always capture:
- Required syntax and parameters.
- Preconditions and prerequisites.
- Defaults and fallback behavior.
- Locking, performance, and failure caveats.
- Version-specific notes and compatibility constraints.

### 4) Cross-Validation Pattern
For high-impact changes, validate with at least two doc sections.

Examples:
- Index proposal: index types page + planner/performance page.
- Authentication change: client-authentication + role management.
- Recovery runbook: backup + continuous archiving + HA chapter.

### 5) Failure-Driven Fetching
When an error appears, fetch the most specific chapter and any linked prerequisites.

Examples:
- Lock waits and deadlocks: monitoring locks + explicit locking.
- Connection/auth failures: pg_hba/auth method docs.
- Replication lag/failover issues: high availability + replication + monitoring stats.

## Quality Gates
- Recommendation cites relevant official PostgreSQL docs sections.
- SQL/config examples are version-aligned with PostgreSQL 18 unless user specifies otherwise.
- Risk, rollback, and verification steps are included for production-impacting changes.
- Performance claims are supported by measurable validation guidance.
- Security-sensitive changes include least-privilege and transport/auth checks.

## Completion Checklist
- Clear outcome and success metric defined.
- Docs fetched for the exact topic, not generic summaries.
- Final guidance includes: implementation, validation, rollback, and caveats.
- Open assumptions are explicitly listed.

## Common Pitfalls
- Suggesting commands without checking version-specific behavior.
- Recommending indexes without considering write amplification and maintenance cost.
- Tuning planner settings globally before fixing stats/query/index design.
- Applying auth changes without documenting pg_hba order and role implications.
- Proposing backup strategy without restore verification steps.

## Recommended Output Format
1. Situation summary.
2. Docs consulted via fetch_webpage and key rules extracted.
3. Proposed SQL/config/runbook change.
4. Validation plan and expected outcomes.
5. Risks, rollback, and next tuning steps.

## References
- [PostgreSQL Documentation Map](./references/postgres-doc-map.md)
---
name: jinja-template-component-expert
description: 'Create excellent Jinja templates and reusable components using official documentation. Use when designing template inheritance, macros, call blocks, includes/imports, context boundaries, escaping, and maintainable component APIs.'
argument-hint: 'Describe the page/component goal, input context shape, framework (Flask/Django/other), design constraints, and whether output is HTML, email, or text.'
user-invocable: true
disable-model-invocation: false
---

# Jinja Template Component Expert

Use this skill to build production-grade Jinja templates and component systems with a docs-first workflow.

## Outcome
- Produce reusable Jinja components with clear macro APIs and predictable rendering behavior.
- Keep template logic lean while preserving flexibility through inheritance and composition.
- Default to safe escaping and explicit context handling.

## When to Use
- Designing a new template system for pages, partials, or emails.
- Creating or refactoring shared components with macros and call blocks.
- Standardizing include/import/context conventions across templates.
- Fixing brittle template inheritance, whitespace, or undefined-variable failures.
- Auditing escaping and sandbox safety for untrusted content scenarios.

## Inputs to Gather First
- Rendering context source (Flask, Django, custom Environment, static generation).
- Output target (HTML page, HTML email, text, config).
- Component catalog and naming expectations.
- Escaping and trust boundaries for user-provided fields.
- Performance constraints (template count, cold start latency, caching strategy).

## Core Workflow
1. Restate target UI/content and define the template contract:
   - Required inputs.
   - Optional inputs with defaults.
   - Safety expectations (safe HTML vs plain text).
2. Choose composition strategy before writing markup:
   - Use inheritance (`extends` + `block`) for page shells.
   - Use macros for reusable leaf components.
   - Use include for structural partials that render immediately.
3. Define component APIs with macro signatures and strict defaults:
   - Prefer keyword arguments.
   - Use explicit default values.
   - Use `call` blocks when child content slots are needed.
4. Configure environment-level behavior deliberately:
   - Set sensible autoescape defaults.
   - Decide `undefined` policy (prefer strict for early failure in development).
   - Set whitespace rules (`trim_blocks`, `lstrip_blocks`) intentionally.
5. Implement templates with context discipline:
   - Use `import`/`from ... import` for macro libraries.
   - Use `with context` or `without context` explicitly when needed.
   - Avoid hidden coupling to ambient variables.
6. Apply escaping and formatting rules:
   - Escape untrusted values.
   - Use `safe` only for verified, trusted HTML.
   - Keep data shaping in Python where possible; keep template logic simple.
7. Add diagnostics and reliability checks:
   - Add representative render examples.
   - Validate undefined behavior and fallback paths.
   - Ensure include/import failures are intentional (`ignore missing` only when justified).
8. Optimize once correctness is stable:
   - Confirm loader strategy is appropriate.
   - Enable bytecode caching where startup cost matters.
   - Consider precompilation or async only when justified by runtime needs.
9. Summarize implementation decisions with documentation references.

## Decision Points and Branching

### A) Inheritance vs Macro vs Include
- If the concern is page skeleton/layout: prefer inheritance.
- If the concern is reusable UI element with parameters: prefer macro.
- If the concern is static or simple structural composition: prefer include.

### B) Context Sharing
- If a component should be portable: avoid implicit ambient context.
- If a partial requires broad page context: include with context intentionally.
- If deterministic behavior matters most: import macros and pass explicit args.

### C) Escaping Strategy
- HTML output: enable autoescape by default for HTML-like extensions.
- Non-HTML output: disable autoescape unless explicitly required.
- Mixed trusted/untrusted content: pass trusted markup explicitly and document why.

### D) Undefined Policy
- Development and QA hardening: use StrictUndefined.
- User-facing best-effort rendering: use softer undefined policy with guarded defaults.

### E) Performance
- Many templates or frequent cold starts: add bytecode cache.
- Mostly static render graph: consider precompiled templates.
- Async stack only: enable async rendering after validating call chains.

## Quality Gates
- Every reusable component has a documented macro signature.
- Inheritance tree is intentional and easy to trace.
- Escaping behavior is explicit and safe for untrusted values.
- Includes/imports use explicit context strategy.
- Undefined-variable behavior is intentional and tested.
- At least one representative render is validated per changed component.

## Completion Checklist
- Component APIs and expected context are documented.
- Templates render correctly for happy path and missing/edge inputs.
- Escaping and `safe` usage reviewed for XSS risk.
- Whitespace behavior matches output expectations.
- Relevant docs were consulted via [Jinja Official Doc Map](references/jinja-official-doc-map.md).

## Common Pitfalls
- Overusing include where macros would produce cleaner APIs.
- Relying on implicit context instead of explicit parameters.
- Using `safe` on untrusted user input.
- Allowing silent undefined values to hide data bugs.
- Moving too much application logic into templates.

## Recommended Output Format
1. Component plan (inheritance, macro libraries, include boundaries).
2. Macro/API definitions and context contract.
3. Escaping and undefined policy choices.
4. Render examples and validation notes.
5. Documentation links used.

## References
- [Jinja Official Doc Map](references/jinja-official-doc-map.md)
- https://jinja.palletsprojects.com/en/stable/

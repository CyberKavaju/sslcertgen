# Jinja Official Doc Map

Use this map to quickly select the right official section for template and component work.

Source root: https://jinja.palletsprojects.com/en/stable/

## Quick Start Path (Most Template Work)
1. Template language fundamentals:
   - https://jinja.palletsprojects.com/en/stable/templates/
2. Inheritance, blocks, macros, include/import:
   - https://jinja.palletsprojects.com/en/stable/templates/#template-inheritance
   - https://jinja.palletsprojects.com/en/stable/templates/#macros
   - https://jinja.palletsprojects.com/en/stable/templates/#call
   - https://jinja.palletsprojects.com/en/stable/templates/#include
   - https://jinja.palletsprojects.com/en/stable/templates/#import
3. Escaping and safety behavior:
   - https://jinja.palletsprojects.com/en/stable/templates/#html-escaping
   - https://jinja.palletsprojects.com/en/stable/api/#autoescaping

## By Problem Type

### 1) Reusable Components (Macros and Slots)
- Macros and call blocks:
  - https://jinja.palletsprojects.com/en/stable/templates/#macros
  - https://jinja.palletsprojects.com/en/stable/templates/#call
- Import and module-style macro usage:
  - https://jinja.palletsprojects.com/en/stable/templates/#import
  - https://jinja.palletsprojects.com/en/stable/templates/#import-context-behavior

### 2) Page Layout Architecture
- Template inheritance and block behavior:
  - https://jinja.palletsprojects.com/en/stable/templates/#template-inheritance
  - https://jinja.palletsprojects.com/en/stable/templates/#blocks
  - https://jinja.palletsprojects.com/en/stable/templates/#required-blocks
  - https://jinja.palletsprojects.com/en/stable/templates/#block-nesting-and-scope

### 3) Include vs Import vs Extends Confusion
- Include behavior and missing-template options:
  - https://jinja.palletsprojects.com/en/stable/templates/#include
- Import behavior and caching/context implications:
  - https://jinja.palletsprojects.com/en/stable/templates/#import
  - https://jinja.palletsprojects.com/en/stable/templates/#import-context-behavior

### 4) Escaping and XSS Safety
- Template-side escaping rules:
  - https://jinja.palletsprojects.com/en/stable/templates/#html-escaping
  - https://jinja.palletsprojects.com/en/stable/templates/#autoescape-overrides
- Environment-level autoescape setup:
  - https://jinja.palletsprojects.com/en/stable/api/#autoescaping
  - https://jinja.palletsprojects.com/en/stable/api/#jinja2.select_autoescape
- FAQ rationale:
  - https://jinja.palletsprojects.com/en/stable/faq/#why-is-html-escaping-not-the-default

### 5) Undefined Variables and Failure Modes
- Undefined type behavior:
  - https://jinja.palletsprojects.com/en/stable/api/#undefined-types
  - https://jinja.palletsprojects.com/en/stable/api/#jinja2.StrictUndefined

### 6) Whitespace and Output Cleanliness
- Whitespace control tags and environment settings:
  - https://jinja.palletsprojects.com/en/stable/templates/#whitespace-control
  - https://jinja.palletsprojects.com/en/stable/api/#high-level-api

### 7) Custom Filters, Tests, and Globals
- Registering custom filters/tests:
  - https://jinja.palletsprojects.com/en/stable/api/#custom-filters
  - https://jinja.palletsprojects.com/en/stable/api/#custom-tests
- Context/environment decorators:
  - https://jinja.palletsprojects.com/en/stable/api/#utilities
- Global namespace rules:
  - https://jinja.palletsprojects.com/en/stable/api/#the-global-namespace

### 8) Environment and Loader Setup
- Environment options and lifecycle:
  - https://jinja.palletsprojects.com/en/stable/api/#jinja2.Environment
- Loader strategies:
  - https://jinja.palletsprojects.com/en/stable/api/#loaders

### 9) Performance and Runtime Behavior
- Template and bytecode caching:
  - https://jinja.palletsprojects.com/en/stable/api/#bytecode-cache
- Async rendering model:
  - https://jinja.palletsprojects.com/en/stable/api/#async-support
- Performance FAQ:
  - https://jinja.palletsprojects.com/en/stable/faq/#how-fast-is-jinja

### 10) Security for Untrusted Templates
- Sandboxed environment and restrictions:
  - https://jinja.palletsprojects.com/en/stable/sandbox/
  - https://jinja.palletsprojects.com/en/stable/sandbox/#security-considerations

### 11) Native Python Return Types
- NativeEnvironment behavior:
  - https://jinja.palletsprojects.com/en/stable/nativetypes/

### 12) Framework Integration
- Flask and other integration notes:
  - https://jinja.palletsprojects.com/en/stable/integration/

## Component Authoring Checkpoints (Doc-Backed)
- Inheritance structure reviewed against template inheritance docs.
- Macro signatures and call blocks validated against macro docs.
- Include/import context behavior explicitly chosen.
- Autoescape defaults and overrides confirmed.
- Undefined policy intentionally selected.
- Any custom filters/tests validated against API decorators and registration rules.

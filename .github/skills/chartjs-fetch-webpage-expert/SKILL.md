---
name: chartjs-fetch-webpage-expert
description: 'Implement production-grade Chart.js charts using official docs and the fetch_webpage tool. Use when building new charts, customizing tooltips/legends/scales/plugins, optimizing performance, fixing registration errors, or validating Chart.js API behavior against docs.'
argument-hint: 'Describe chart goal, framework, dataset shape, and constraints (performance/responsive/accessibility)'
user-invocable: true
disable-model-invocation: false
---

# Chart.js + fetch_webpage Expert

Build, customize, optimize, and debug Chart.js implementations using a docs-first workflow powered by fetch_webpage.

## When to Use
- Implementing any Chart.js chart in JavaScript/TypeScript.
- Migrating from quick prototype (`chart.js/auto`) to optimized tree-shaken imports.
- Designing advanced scales, tooltips, legends, and plugins.
- Diagnosing runtime issues such as unregistered controllers/scales/plugins.
- Verifying API details against the latest official documentation.

## Inputs You Should Gather First
- Chart goal: trend, comparison, distribution, part-to-whole, etc.
- Data shape: labels + primitive values, tuples, objects, or custom keys.
- Runtime: plain JS, React, Vue, Svelte, Angular, Node, bundler, or script tag.
- Constraints: performance targets, responsiveness, accessibility, print behavior.
- Interactions: tooltip behavior, legend behavior, click/hover callbacks, drilldown.

## Core Workflow
1. Scope the chart and success criteria.
2. Fetch only relevant docs with fetch_webpage.
3. Select chart type + data structure.
4. Choose integration mode (auto vs tree-shaken registration).
5. Build minimal working chart config.
6. Layer customizations (scales, tooltip, legend, elements).
7. Add update lifecycle handling (`chart.update()` patterns).
8. Add performance options and validate responsiveness.
9. If needed, add plugins (inline/local/global) with proper IDs/options.
10. Validate against docs and provide final implementation notes.

## fetch_webpage Deep-Use Playbook

### 1) Query Design
Use intent-focused queries that ask for constraints, defaults, and gotchas, not just examples.

Examples:
- "Extract required registration components for line and bar charts with bundlers"
- "Summarize tooltip callbacks, context fields, and dataset overrides"
- "List performance knobs: parsing false, normalized true, decimation, animation false"

### 2) URL Selection Strategy
Prefer official pages by topic and fetch in narrow batches:
- Integration/setup:
  - https://www.chartjs.org/docs/latest/getting-started/installation.html
  - https://www.chartjs.org/docs/latest/getting-started/integration.html
- Core model:
  - https://www.chartjs.org/docs/latest/configuration/
  - https://www.chartjs.org/docs/latest/general/data-structures.html
  - https://www.chartjs.org/docs/latest/general/options.html
- Feature detail:
  - https://www.chartjs.org/docs/latest/configuration/tooltip.html
  - https://www.chartjs.org/docs/latest/configuration/legend.html
  - https://www.chartjs.org/docs/latest/axes/
- Lifecycle + extension:
  - https://www.chartjs.org/docs/latest/developers/updates.html
  - https://www.chartjs.org/docs/latest/developers/plugins.html
- Performance:
  - https://www.chartjs.org/docs/latest/general/performance.html

### 3) Extraction Checklist
From fetch_webpage results, always capture:
- Required components to register for chosen chart type.
- Namespace paths (for example `options.plugins.tooltip`).
- Defaults and fallback behavior.
- Callback signatures and context object fields.
- Non-obvious caveats (for example responsive container requirements).
- Version cues and "Last Updated" hints when available.

### 4) Cross-Validation Pattern
When a behavior is critical, verify from two pages:
- Example: tooltip behavior from tooltip page + options resolution from options page.
- Example: scale config from axes page + chart-type defaults from chart page.

### 5) Failure-Driven Fetching
If runtime error occurs, fetch the matching docs section directly.

Examples:
- Error: "\"bar\" is not a registered controller"
  - Fetch integration bundle optimization + target chart page.
- Incorrect tooltip content
  - Fetch tooltip callbacks + tooltip item context.
- Blurry or shrinking chart
  - Fetch responsive docs and enforce dedicated relative container.

## Decision Matrix
- Need speed and prototype: use `import Chart from 'chart.js/auto'`.
- Need smaller bundles: import/register exact controllers/elements/scales/plugins.
- Need object-shaped domain data: use parsing keys (`xAxisKey`, `yAxisKey`, `key`).
- Need maximum render throughput: prefer sorted internal format, `parsing: false`, `normalized: true`, decimation, `animation: false`.
- Need reusable behavior across many charts: use registered plugin with ID + defaults.
- Need one-off behavior in single chart: use inline plugin in chart config.

## Implementation Quality Gates
- Chart renders without registration errors.
- Data and labels align with selected data structure.
- Options placed in correct namespace.
- Responsive behavior works in dedicated chart container.
- Update flows (`add/remove data`, options mutation vs replacement) are intentional.
- Performance options are explicit for large datasets.
- Any custom plugin has unique lowercase ID and scoped options.
- Tooltip/legend callbacks return predictable values for edge cases (nulls, hidden datasets).

## Completion Checklist
- Minimal chart created and visible.
- All requested customizations implemented.
- Docs-backed validation performed for each advanced option.
- Runtime errors resolved via targeted fetch_webpage pulls.
- Final code includes note on why integration mode was chosen.
- User receives "what to tweak next" list (scales, tooltip, legend, plugins, performance).

## Common Pitfalls
- Mixing `chart.js/auto` with manual registration in a way that defeats tree-shaking goals.
- Placing plugin options outside `options.plugins.<plugin-id>`.
- Assuming canvas CSS alone handles responsiveness without a dedicated container.
- Replacing entire options object when only mutation was intended.
- Disabling parsing without providing sorted/internal-format-compatible data.

## Recommended Output Format
1. "Chosen chart architecture" summary.
2. Working config/code.
3. Registration rationale.
4. Fetch-webpage evidence summary (pages + key rules extracted).
5. Final tuning options and next optimizations.

## References
- [Fetch Workflow Notes](./references/fetch-webpage-workflow.md)
- [Chart.js Implementation Cheatsheet](./references/chartjs-implementation-cheatsheet.md)

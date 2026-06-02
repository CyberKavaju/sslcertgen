# fetch_webpage Workflow for Chart.js

Use this note when you need high-precision extraction from Chart.js documentation.

## Prompt Shapes That Work Well
- "Extract API namespaces, defaults, and callback signatures for tooltip and legend"
- "List required controllers/elements/scales/plugins for [chart type] with bundlers"
- "Summarize performance options and their tradeoffs for large line datasets"

## High-Signal URL Sets
- Setup: installation, integration
- Data/options: data-structures, options, configuration
- UX: tooltip, legend, responsive, axes
- Runtime: developers/updates, developers/plugins
- Performance: general/performance

## Reliability Rules
- Ask for "actionable details and gotchas" explicitly.
- Include enough URLs to triangulate behavior, but keep each batch focused.
- For conflicting snippets, prioritize page-specific docs over generic examples.
- Re-fetch with narrower query when response is too broad.

## Error-to-Doc Mapping
- Unregistered controller/scale/plugin:
  - integration + target chart docs
- Tooltip formatting issues:
  - tooltip callbacks + options context
- Unexpected resizing:
  - responsive docs + container requirements
- Slow rendering:
  - performance + decimation + parsing/normalization

## Output Discipline
Always turn extracted docs into:
- Rule (what must be true)
- Action (what to implement)
- Verification (what confirms it works)

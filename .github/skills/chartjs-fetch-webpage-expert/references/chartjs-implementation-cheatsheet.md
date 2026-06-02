# Chart.js Implementation Cheatsheet

## Config Skeleton
```js
const config = {
  type: 'line',
  data: {
    labels: [],
    datasets: []
  },
  options: {},
  plugins: []
};
```

## Integration Modes
- Prototyping: `import Chart from 'chart.js/auto'`
- Optimized: import/register only required components.

## Required Registration (Typical)
- Bar: `BarController`, `BarElement`, `CategoryScale`, `LinearScale`
- Line: `LineController`, `LineElement`, `PointElement`, `CategoryScale`, `LinearScale`
- Common optional plugins: `Legend`, `Tooltip`, `Title`, `SubTitle`, `Filler`, `Decimation`

## Data Strategy
- Primitive arrays + labels for simple series.
- Object arrays for flexible domain models.
- For custom object fields, use parsing keys.
- For speed with large datasets:
  - data in internal format
  - `parsing: false`
  - `normalized: true`

## Namespace Anchors
- Tooltip: `options.plugins.tooltip`
- Legend: `options.plugins.legend`
- Scales: `options.scales.<id>`
- Plugin options: `options.plugins.<plugin-id>`

## Responsive Essentials
- Wrap canvas in dedicated, relatively positioned container.
- Use `maintainAspectRatio: false` when explicit container height is needed.
- Do not rely on canvas style-only sizing for correct render resolution.

## Update Patterns
- Add/remove data: mutate labels and dataset arrays then `chart.update()`.
- Mutate options in place to preserve computed internals.
- Replace options object only when full reset is intended.
- Use `chart.update('none')` to skip animation during updates.

## Performance Knobs
- `animation: false`
- `parsing: false`
- `normalized: true`
- Decimation for dense line data
- Explicit `min`/`max` on scales where possible
- Optional worker rendering with OffscreenCanvas for heavy workloads

## Plugin Rules
- Plugin needs unique lowercase `id`.
- Reusable plugins: `Chart.register(plugin)`.
- One-off plugins: inline in chart config.
- Disable plugin per chart via `options.plugins.<id> = false`.

---
description: "Glassmorphism UI design system rules for MKTReport (Frozen Light theme). Apply when creating or modifying Jinja templates, HTML, or static CSS/JS. Covers color tokens, glass components, layout structure, typography, interactive states, badges, progress bars, charts, and forbidden patterns."
name: "UI Design System — Frozen Light"
applyTo:
  - "app/views/**"
  - "app/static/**"
  - "docs/architecture/**"
---

# UI Design System — Frozen Light (Glassmorphism)

All UI output must match the "Frozen Light" aesthetic: ethereal depth through dark, atmospheric, translucent surfaces.

## Tailwind Config — Required Setup

Every page must include this Tailwind config. Color tokens are **canonical**; do not substitute hex values inline.

```js
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "background":                "#0a0e1a",
        "surface":                   "#0f1524",
        "surface-dim":               "#0f1524",
        "surface-bright":            "#1a2438",
        "surface-container-lowest":  "#0a0e1a",
        "surface-container-low":     "#111828",
        "surface-container":         "#141c2e",
        "surface-container-high":    "#1a2438",
        "surface-container-highest": "#202c42",
        "surface-variant":           "#1a2438",
        "on-surface":                "#e0e8f0",
        "on-background":             "#e0e8f0",
        "on-surface-variant":        "#a0b4c4",
        "primary":                   "#7dd3fc",
        "primary-fixed":             "#c8eaff",
        "primary-fixed-dim":         "#7dd3fc",
        "primary-container":         "#0e4d6e",
        "on-primary":                "#001f2e",
        "on-primary-container":      "#c8eaff",
        "secondary":                 "#88b4cc",
        "secondary-container":       "#1a3a4e",
        "tertiary":                  "#c8a0f0",
        "tertiary-container":        "#3d2060",
        "tertiary-fixed-dim":        "#c8a0f0",
        "outline":                   "#4a6070",
        "outline-variant":           "#2a3a48",
        "error":                     "#ff6b6b",
        "error-container":           "#3d1414",
        "inverse-primary":           "#0a4c6e",
        "inverse-surface":           "#e0e8f0",
        "inverse-on-surface":        "#0a0e1a",
        "surface-tint":              "#7dd3fc",
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg:      "1rem",
        xl:      "1.5rem",
        full:    "9999px",
      },
      fontFamily: {
        headline: ["Inter"],
        display:  ["Inter"],
        body:     ["Inter"],
        label:    ["Inter"],
      },
    },
  },
}
```

Required `<head>` dependencies (in order):
```html
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
```

---

## Glass CSS Classes — Exact Definitions

Include these in every page `<style>` block. Do **not** inline these values with Tailwind utilities.

```css
body {
  font-family: 'Inter', sans-serif;
  background-color: #0a0e1a;
  color: #e0e8f0;
}

/* Layer 1: Standard glass surface */
.glass-card,
.glass-panel {
  background: rgba(15, 21, 36, 0.6);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(125, 211, 252, 0.1);
}

/* Layer 2: Elevated glass surface */
.glass-card-elevated,
.glass-panel-elevated {
  background: rgba(15, 21, 36, 0.75);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(125, 211, 252, 0.15);
}
```

### When to use each layer
| Layer | Class | Use case |
|-------|-------|----------|
| 1 | `glass-card` / `glass-panel` | KPI cards, table containers, section panels |
| 2 | `glass-card-elevated` / `glass-panel-elevated` | Modals, dropdowns, popovers, tooltips |
| Sidebar | `bg-slate-950/75 backdrop-blur-2xl` | Left nav — Tailwind utility only |
| Top bar | `bg-slate-950/60 backdrop-blur-md` | Sticky header — Tailwind utility only |

---

## Reusable Components — Jinja Macros

Never duplicate HTML patterns across templates. All recurring UI elements must be extracted into Jinja macros under `app/views/components/` and imported where needed.

### File Organisation

| Component file | Contains |
|----------------|----------|
| `app/views/components/badges.html` | `status_badge()`, `role_badge()`, `delta_badge()` |
| `app/views/components/cards.html` | `kpi_card()`, `glass_card()` |
| `app/views/components/buttons.html` | `btn_primary()`, `btn_ghost()`, `btn_icon()` |
| `app/views/components/progress.html` | `progress_bar()` |
| `app/views/components/tables.html` | `data_table()` header/row helpers |
| `app/views/layouts/base.html` | Base page skeleton (head, sidebar, topbar, content block) |

### Import Pattern

```jinja
{% from "components/badges.html" import status_badge, role_badge %}
{% from "components/cards.html" import kpi_card %}
{% from "components/buttons.html" import btn_primary %}

{{ status_badge("Active") }}
{{ role_badge("Admin") }}
{{ kpi_card(label="TOTAL SPEND", value="$142,384.20", delta="+12.4%", progress=72) }}
```

### Layout Inheritance

All feature templates must extend the base layout — never write standalone `<html>` pages:

```jinja
{% extends "layouts/base.html" %}

{% block content %}
  <div class="p-8 space-y-8">
    ...
  </div>
{% endblock %}
```

The base layout provides: `<html>`, Tailwind config, `<head>` dependencies, glass CSS classes, sidebar, and topbar. Individual templates only fill `{% block content %}` (and optionally `{% block page_title %}` and `{% block head_extra %}`).

### Macro Design Rules

- Macros accept only the data they need — no template logic in macro arguments.
- Default values must match the design system (e.g., default progress bar color is `primary`).
- Never hardcode colours or sizes inside macros — use the Tailwind token classes from this document.
- If a component variant doesn't fit an existing macro, add a parameter — do not create a second macro.

---

## Layout Structure

```html
<!-- Sidebar: fixed, full height, 256px wide -->
<aside class="flex flex-col h-screen w-64 fixed left-0 top-0
              bg-slate-950/75 backdrop-blur-2xl
              border-r border-white/5 font-sans text-sm">
  ...
</aside>

<!-- Main canvas: offset by sidebar width -->
<main class="ml-64 min-h-screen relative">

  <!-- Top app bar: sticky, glass -->
  <header class="flex justify-between items-center w-full px-6 h-16
                 sticky top-0 z-50
                 bg-slate-950/60 backdrop-blur-md
                 border-b border-sky-400/10
                 shadow-[0_0_20px_rgba(125,211,252,0.05)]">
    ...
  </header>

  <!-- Page content -->
  <div class="p-8 space-y-8">
    ...
  </div>
</main>
```

---

## Typography Scale

| Role | Classes |
|------|---------|
| Page title | `text-3xl font-black text-white tracking-tight` |
| Page subtitle | `text-slate-400 text-sm mt-1` |
| Section heading | `text-sm font-bold text-on-surface uppercase tracking-wider` |
| Card label | `text-xs text-on-surface-variant uppercase tracking-wider` |
| KPI value (large) | `text-3xl font-black text-on-surface` |
| KPI value (medium) | `text-2xl font-bold text-on-surface` |
| Body text | `text-sm text-on-surface` |
| Muted/secondary text | `text-xs text-on-surface-variant` |
| Accent/primary text | `text-primary` or `text-sky-300` |
| Mono (numbers/IDs) | `font-mono text-sm text-on-surface` |

- Never use `text-white` for body content — use `text-on-surface` (`#e0e8f0`).
- `text-sky-300` is an alias for primary accent in Tailwind utilities when `text-primary` is unavailable.

---

## Sidebar Navigation

```html
<!-- Active state -->
<a class="flex items-center gap-3 px-4 py-3 font-semibold
           bg-sky-400/10 text-sky-300
           border-r-2 border-sky-400
           hover:translate-x-1 duration-200 cursor-pointer">
  <span class="material-symbols-outlined">dashboard</span>
  <span>Dashboard</span>
</a>

<!-- Inactive state -->
<a class="flex items-center gap-3 px-4 py-3
           text-slate-400
           hover:bg-white/5 hover:text-white
           transition-all hover:translate-x-1 duration-200 cursor-pointer">
  <span class="material-symbols-outlined">campaign</span>
  <span>Campaigns</span>
</a>
```

---

## Buttons

```html
<!-- Primary CTA -->
<button class="bg-primary hover:bg-sky-400 text-on-primary
               text-xs font-bold px-6 py-2 rounded-lg
               transition-all shadow-[0_0_15px_rgba(125,211,252,0.3)]
               flex items-center gap-2">
  <span class="material-symbols-outlined text-sm">file_download</span>
  EXPORT REPORT
</button>

<!-- Ghost / secondary -->
<button class="glass-card px-4 py-2 rounded-lg
               flex items-center gap-3
               text-xs font-medium text-slate-300
               hover:border-sky-400/30 transition-all">
  ...
</button>

<!-- Icon button (circular) -->
<button class="p-2 rounded-full text-slate-400
               hover:bg-sky-400/5 hover:text-sky-200
               transition-all duration-300 active:scale-95">
  <span class="material-symbols-outlined">notifications</span>
</button>
```

---

## Form Inputs

```html
<!-- Search / text input -->
<input type="text"
  class="bg-surface-container-low border-none rounded-full
         pl-10 pr-4 py-1.5 text-xs text-slate-300
         focus:ring-1 focus:ring-sky-400/50
         transition-all duration-300"
  placeholder="Search..."/>
```

- No opaque solid backgrounds on inputs — use `bg-surface-container-low`.
- Focus state: `focus:ring-1 focus:ring-sky-400/50` only — no outline, no heavy glow.
- Toggles/switches: `bg-primary` when active, `bg-white/10` when inactive.

---

## KPI / Metric Cards

```html
<div class="glass-card p-6 rounded-xl relative overflow-hidden group">
  <!-- Ambient glow blob (optional, per card) -->
  <div class="absolute top-0 right-0 w-24 h-24
              bg-sky-400/5 blur-3xl -mr-8 -mt-8 rounded-full
              group-hover:bg-sky-400/10 transition-all duration-500"></div>

  <!-- Card content -->
  <p class="text-xs text-on-surface-variant uppercase tracking-wider mb-2">TOTAL SPEND</p>
  <p class="text-3xl font-black text-on-surface">$142,384.20</p>

  <!-- Delta badge -->
  <span class="text-xs font-bold text-green-400">+12.4% ↗</span>

  <!-- Progress bar -->
  <div class="h-1 w-full bg-surface-container rounded-full overflow-hidden mt-4">
    <div class="h-full bg-primary rounded-full" style="width: 72%"></div>
  </div>
</div>
```

---

## Tables

```html
<div class="glass-card rounded-xl overflow-hidden">
  <table class="w-full">
    <thead>
      <tr class="border-b border-outline-variant">
        <th class="px-6 py-4 text-left text-xs font-medium text-on-surface-variant uppercase tracking-wider">
          COLUMN
        </th>
      </tr>
    </thead>
    <tbody class="divide-y divide-outline-variant/50">
      <tr class="hover:bg-white/5 transition-colors group">
        <td class="px-6 py-5 text-sm text-on-surface">Value</td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## Status Badges

```html
<!-- Active -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold
             bg-green-500/10 text-green-400 border border-green-500/20">
  ● Active
</span>

<!-- Paused -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold
             bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
  ● Paused
</span>

<!-- Error / Inactive -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold
             bg-red-500/10 text-red-400 border border-red-500/20">
  ● Error
</span>

<!-- Role badge (Admin / Editor / Viewer) -->
<span class="px-3 py-1 rounded-full text-xs font-bold border
             border-primary/40 text-primary bg-primary/10">
  Admin
</span>
```

---

## Progress Bars

```html
<!-- Standard thin bar (KPI cards, table rows) -->
<div class="h-1 w-full bg-surface-container rounded-full overflow-hidden">
  <div class="h-full bg-primary rounded-full" style="width: 72%"></div>
</div>

<!-- Spend-to-budget indicator (campaigns) -->
<div class="h-1 w-full bg-surface-container rounded-full overflow-hidden">
  <div class="h-full bg-tertiary rounded-full" style="width: 100%"></div>
</div>
```

---

## Icons

Use **Material Symbols Outlined** exclusively.

```html
<span class="material-symbols-outlined">dashboard</span>
```

Default variation settings (include in `<style>`):
```css
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
```

- Size: use Tailwind `text-sm`, `text-base`, `text-lg`, `text-xl` on the `<span>`.
- Color: inherit from parent or set with `text-primary`, `text-on-surface-variant`, etc.
- Filled variant: set `'FILL' 1` inline via `style="font-variation-settings: 'FILL' 1;"`.

---

## Glow & Depth Effects

| Effect | Class / Style |
|--------|--------------|
| Button primary glow | `shadow-[0_0_15px_rgba(125,211,252,0.3)]` |
| Top bar ambient shadow | `shadow-[0_0_20px_rgba(125,211,252,0.05)]` |
| Card ambient blob | `absolute bg-sky-400/5 blur-3xl rounded-full` (inside card) |
| Active sidebar indicator | `border-r-2 border-sky-400` |

- Glow is only applied to interactive elements (buttons, active states) or structural anchors (top bar).
- Never add `box-shadow` to passive cards — use the ambient blob pattern instead.
- Never use drop shadows for depth; depth comes from blur intensity and opacity.

---

## Color Usage Rules

| Token | Use |
|-------|-----|
| `primary` / `#7dd3fc` | CTAs, active states, progress bars, links, focus rings |
| `tertiary` / `#c8a0f0` | Secondary accents, spend bars, AI/insight highlights |
| `on-surface` | Primary content text |
| `on-surface-variant` | Labels, captions, placeholders, muted metadata |
| `surface-container-*` | Container backgrounds (prefer tokens over raw hex) |
| `outline-variant` | Table dividers, subtle separators |
| `outline` | Visible borders, input outlines |

---

## Forbidden Patterns

- **No opaque solid backgrounds** on cards, panels, modals, or dropdowns — always use the glass classes or `rgba()`.
- **No hard box shadows** (`shadow-md`, `shadow-lg`, etc.) — use glow sparingly via `shadow-[...]` custom syntax.
- **No raw hex values** inline in HTML/Jinja — use Tailwind tokens or glass CSS classes.
- **No font other than Inter** — do not import or use other typefaces.
- **No `text-white`** for body content — use `text-on-surface`.
- **No `bg-gray-*` or `bg-zinc-*`** — use `surface-container-*` tokens.
- **No border radius below `rounded-lg`** on cards — use `rounded-xl` minimum.
- **No structural shadows** on floating elements — depth only through blur + opacity.
- **No `border-opacity-*` utilities** — use Tailwind slash notation (`border-sky-400/10`).
- **No duplicated HTML patterns** — extract any recurring markup into a macro in `app/views/components/` on first reuse.
- **No standalone `<html>` pages** for feature templates — always extend `layouts/base.html`.

# ONTO Design System — Color Scheme v1.1

## Core Palette

### Primary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Safe (Green)** | `#15803d` | `rgb(21, 128, 61)` | Calibrated state, success, CTA |
| **Danger (Red)** | `#dc2626` | `rgb(220, 38, 38)` | Uncalibrated state, errors |
| **Warning (Amber)** | `#d97706` | `rgb(217, 119, 6)` | Caution, pending states |

### Subtle Variants (15% opacity)

| Name | Value | Usage |
|------|-------|-------|
| **Safe Subtle** | `rgba(21, 128, 61, 0.15)` | Backgrounds, cards, buttons |
| **Danger Subtle** | `rgba(220, 38, 38, 0.15)` | Error backgrounds |
| **Warning Subtle** | `rgba(217, 119, 6, 0.15)` | Warning backgrounds |

---

## Dark Theme

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#0a0a0a` | Main background |
| `--bg-secondary` | `#121212` | Secondary background |
| `--bg-card` | `#1a1a1a` | Card background |
| `--bg-elevated` | `#242424` | Elevated surfaces |
| `--border` | `#333333` | Borders |
| `--text` | `#fafafa` | Primary text |
| `--text-secondary` | `#a0a0a0` | Secondary text |
| `--text-muted` | `#606060` | Muted text, hints |

---

## Light Theme

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#ffffff` | Main background |
| `--bg-secondary` | `#f9fafb` | Secondary background |
| `--bg-card` | `#ffffff` | Card background |
| `--bg-elevated` | `#f3f4f6` | Elevated surfaces |
| `--border` | `#e5e7eb` | Borders |
| `--text` | `#111827` | Primary text |
| `--text-secondary` | `#6b7280` | Secondary text |
| `--text-muted` | `#9ca3af` | Muted text, hints |

---

## CSS Variables

```css
/* === DARK THEME (default) === */
:root {
    --bg: #0a0a0a;
    --bg-secondary: #121212;
    --bg-card: #1a1a1a;
    --bg-elevated: #242424;
    --border: #333333;
    --text: #fafafa;
    --text-secondary: #a0a0a0;
    --text-muted: #606060;
    
    --safe: #15803d;
    --safe-subtle: rgba(21, 128, 61, 0.15);
    --danger: #dc2626;
    --danger-subtle: rgba(220, 38, 38, 0.15);
    --warning: #d97706;
    --warning-subtle: rgba(217, 119, 6, 0.15);
}

/* === LIGHT THEME === */
[data-theme="light"] {
    --bg: #ffffff;
    --bg-secondary: #f9fafb;
    --bg-card: #ffffff;
    --bg-elevated: #f3f4f6;
    --border: #e5e7eb;
    --text: #111827;
    --text-secondary: #6b7280;
    --text-muted: #9ca3af;
}
```

---

## Semantic Usage

### Orb States

| State | Core Color | Ring Color | Text |
|-------|------------|------------|------|
| Uncalibrated | `--danger` | `--danger` | `CONF: 94%` (glitch) |
| Calibrated | `--safe` | `--safe` | `calibrated` (calm) |

### Signal Hash (σ)

```css
.signal-hash .label { color: #6b7280; }
.signal-hash .byte { color: #15803d; }
.signal-hash .ellipsis { color: #6b7280; }
```

### Buttons

| Type | Background | Text | Border |
|------|------------|------|--------|
| Primary (CTA) | `--safe-subtle` | `--safe` | `--safe` |
| Secondary | `--bg-card` | `--text` | `--border` |
| Danger | `--danger-subtle` | `--danger` | `--danger` |
| Ghost | transparent | `--text-secondary` | none |

### Cards

| Type | Background | Border |
|------|------------|--------|
| Default | `--bg-card` | `--border` |
| Highlighted | `--safe-subtle` | `--safe` |
| Danger | `--danger-subtle` | `--danger` |

---

## Typography Colors

| Element | Dark Theme | Light Theme |
|---------|------------|-------------|
| H1, H2, H3 | `--text` | `--text` |
| Body | `--text-secondary` | `--text-secondary` |
| Hints, Labels | `--text-muted` | `--text-muted` |
| Links | `--safe` | `--safe` |
| Errors | `--danger` | `--danger` |

---

## Migration Notes

### Changed from v0
| Old | New | Reason |
|-----|-----|--------|
| `#22c55e` | `#15803d` | Deep forest green, enterprise feel |
| `#ef4444` | `#dc2626` | Deeper red, consistent depth |
| `#f59e0b` | `#d97706` | Deeper amber, unified palette |

### Button Style
CTA buttons use outline style matching cards:
```css
.cta-button {
    background: var(--safe-subtle);
    color: var(--safe);
    border: 1px solid var(--safe);
}
.cta-button:hover {
    background: var(--safe);
    color: white;
}
```

### Applies To
- `onto-landing.html`
- `onto-client-portal-v4.html`
- `onto-v15-auto-lang.html`
- Future ONTO interfaces

---

*ONTO Design System v1.1 — February 2026*

# PM Workflow Pipeline

## Overview

End-to-end pipeline from user idea submission to Linear work item.

## Flow

```
Canny submission (feature/idea only)
  ↓
PM reviews → sets status in Canny
  ↓
  ├── Discovery - L1  →  pm-discovery  →  inc-prd-builder  →  inc-prd-figma-make  →  linear-sync (Epics + Stories)
  ├── Discovery - L2  →  pm-discovery  →  inc-epic-builder  →  linear-sync (Epic + Stories)
  └── Discovery - L3  →  pm-discovery  →  inc-story-builder  →  linear-sync (Story)
```

## Levels

| Level | Type | Skill | When to use |
|-------|------|-------|-------------|
| L1 | PRD | `inc-prd-builder` | Large, significant product change with major UX impact |
| L2 | Epic | `inc-epic-builder` | Larger, complex work item with meaningful UX impact |
| L3 | Story | `inc-story-builder` | Small, well-understood, self-contained change |

## Skills

| Skill | Stage | Status |
|-------|-------|--------|
| `pm-discovery` | Discovery | ✅ Active |
| `inc-prd-builder` | Planning | ✅ Active |
| `inc-prd-figma-make` | Design | ✅ Active |
| `inc-epic-builder` | Planning | 🚧 Coming soon |
| `inc-story-builder` | Planning | 🚧 Coming soon |
| `linear-sync` | Delivery | 🚧 Coming soon |

## Trigger (GitHub Actions)

Canny webhook → GitHub Actions → routes by status → invokes Claude skill → pushes to Linear

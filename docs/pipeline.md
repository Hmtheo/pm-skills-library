# PM Workflow Pipeline

## Overview

End-to-end pipeline from user idea submission to Linear work item.

## Flow

```
Canny submission (feature/idea only)
  ↓
PM reviews → sets status in Canny
  ↓
  ├── Discovery - L1  →  pm-discovery  →  prd-increment-writer  →  inc-prd-figma-make  →  linear-sync (Epics + Stories)
  ├── Discovery - L2  →  pm-discovery  →  prd-epic-writer  →  linear-sync (Epic + Stories)
  └── Discovery - L3  →  pm-discovery  →  prd-story-writer  →  linear-sync (Story)
```

## Levels

| Level | Type | Skill | When to use |
|-------|------|-------|-------------|
| L1 | PRD | `prd-increment-writer` | Large, significant product change with major UX impact |
| L2 | Epic | `prd-epic-writer` | Larger, complex work item with meaningful UX impact |
| L3 | Story | `prd-story-writer` | Small, well-understood, self-contained change |

## Skills

| Skill | Stage | Status |
|-------|-------|--------|
| `pm-discovery` | Discovery | ✅ Active |
| `prd-increment-writer` | Planning | ✅ Active |
| `inc-prd-figma-make` | Design | ✅ Active |
| `prd-epic-writer` | Planning | 🚧 Coming soon |
| `prd-story-writer` | Planning | 🚧 Coming soon |
| `linear-sync` | Delivery | 🚧 Coming soon |

## Trigger (GitHub Actions)

Canny webhook → GitHub Actions → routes by status → invokes Claude skill → pushes to Linear

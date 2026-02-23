# PM Skills Library

Personal PM skills library for Claude Code. Covers the full pipeline from user idea to Linear work item.

## Pipeline

```
Canny → Discovery Interview → PRD / Epic / Story → Figma → Linear
```

See [docs/pipeline.md](docs/pipeline.md) for the full workflow.

## Skills

### Discovery
| Skill | Description |
|-------|-------------|
| `pm-discovery` | Canny-triggered discovery interview → discovery doc |
| `discovery-interview` | Baseline discovery interview (reference) |

### Planning
| Skill | Description |
|-------|-------------|
| `inc-prd-builder` | Discovery doc → L1 PRD with epics (Jira/Linear ready) |
| `inc-epic-builder` | Discovery doc → L2 Epic for Linear 🚧 |
| `inc-story-builder` | Discovery doc → L3 Story for Linear 🚧 |

### Design
| Skill | Description |
|-------|-------------|
| `inc-prd-figma-make` | PRD → Figma Make screen specs and flows |

### Delivery
| Skill | Description |
|-------|-------------|
| `linear-sync` | Push L1/L2/L3 output to Linear 🚧 |

## Installing a skill

```bash
npx skills add Hmtheo/pm-skills-library --skill <skill-name> -g -y
```

## Structure

```
skills/
  discovery/       # intake and validation
  planning/        # PRD, epic, story generation
  design/          # Figma handoff
  delivery/        # Linear sync
workflows/
  canny-intake/    # GitHub Actions webhook receiver
docs/
  pipeline.md      # full pipeline diagram
```

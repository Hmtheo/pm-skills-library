# PM Skills Library

## Skills

### Discovery
| Skill | Description |
|-------|-------------|
| `discovery-interview` | Baseline discovery interview (reference) |

### Planning
| Skill | Description |
|-------|-------------|
| `prd-increment-writer` | Discovery doc → L1 PRD with epics  Jira or Linear
| `prd-epic-writer` | Discovery doc → L2 Epic for  Jira or Linear
| `prd-story-writer` | Discovery doc → L3 Story for Jira or Linear 

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

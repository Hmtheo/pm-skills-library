---
name: inc-prd-figjam-flow
description: Convert a Product Requirements Document (PRD) into a structured UX flow map for FigJam. Use as a precursor to inc-prd-figma-make to establish user journeys, decision trees, and interaction flows before screen-level prototyping. Accepts any PRD format and outputs FigJam-ready flow architecture with full FR/AC traceability.
user-invocable: true
model: claude-opus-4-6
---

# PRD to FigJam UX Flow Map

Convert PRD content into a structured, buildable UX flow map that establishes the full interaction architecture before screen-level prototyping in Figma Make.

## Purpose

This skill bridges PRD analysis and screen design. It produces a flow map that:
- Surfaces all user journeys, decision branches, and system events before visual design begins
- Provides a shared reference for design, engineering, and product to align on interaction logic
- Feeds directly into `inc-prd-figma-make` as richer context for screen specs

## Inputs

Accept any PRD format, including partial, inconsistent, or draft documents.

Extract and normalize when present:
- Product area and objective/problem statement
- Personas and jobs-to-be-done
- Scope boundaries (in/out of scope)
- Functional requirements (FRs) and acceptance criteria (ACs)
- Use cases and scenarios
- Error states, edge conditions, and system behaviors

If sections are missing, continue with explicit assumptions and flag unresolved questions.

## Workflow

1. Parse and normalize the PRD
   - Identify all user personas and their goals
   - Extract the complete list of use cases and scenarios
   - Group functional requirements into interaction clusters: entry, navigation, action, validation, error, exit
   - Keep all original requirement identifiers (for example `FR-4`, `AC-2`)

2. Define the node inventory
   - Enumerate every screen, state, event, and decision point
   - Assign each a node type: Entry, Screen, Action, Decision, System Event, Error State, or Success/Exit
   - Record each node's triggering condition, data dependencies, and persona visibility

3. Build the flow graph
   - Trace each persona's primary path through the node inventory
   - Identify branching logic (conditional connectors) at every decision node
   - Map all alternative paths: secondary flows, error recovery, empty states, and edge cases
   - Note where flows share nodes (convergence points)

4. Structure for FigJam output
   - Organize flows into sections or swim lanes by persona or journey
   - Apply shape and color conventions from the Node Legend
   - Write connector labels for every conditional branch
   - Annotate key decision nodes with FR/AC references

5. Generate traceability and handoff notes
   - Map every node to linked FR/AC IDs
   - Flag requirements not yet covered by any node
   - Summarize decisions and open questions that will affect screen specs in `inc-prd-figma-make`

## Output format

Return output using this exact section order.

### 1) Flow Map Brief
- Feature/product name
- Flow map goal (what interaction questions this map is intended to answer)
- Personas in scope
- Flows in scope (primary and secondary)
- Out-of-scope flows

### 2) Node Legend

Use these conventions consistently across all flows.

| Shape | Color | Node Type | Description |
|-------|-------|-----------|-------------|
| Oval | Green | Entry Point | Where users enter the flow |
| Rectangle | Blue | Screen / View | A UI page, modal, drawer, or panel |
| Rounded rectangle | Yellow | User Action | An explicit action the user takes |
| Diamond | Orange | Decision | A branch point requiring conditional logic |
| Hexagon | Purple | System Event | A background operation (API call, notification, timer) |
| Rectangle | Red | Error State | A blocking or recoverable error condition |
| Rectangle | Teal | Success / Exit | A completion, confirmation, or exit state |
| Sticky note | White | Annotation | FR/AC references, open questions, or design notes |

### 3) Assumptions and Open Questions
- Assumptions made due to missing PRD detail
- Open questions that affect flow logic (not just visual design)
- Dependency flags (for example, auth system behavior, data availability, permissions model)

### 4) User Flows

For each flow:

**Flow: [Flow Name]**
- Persona: [Persona name]
- Trigger: [What initiates this flow]
- Goal: [User's intended outcome]
- Linked FRs/ACs: [Requirement IDs]

Node sequence:
```
[Node ID] ([Node Type]) [Node Label]
  → [connector label if conditional] → [Node ID] [Node Label]
  → [connector label for alternate path] → [Node ID] [Node Label]
```

Branch logic:
- [Node ID] Decision: [Label] — [Condition A] → [Destination Node ID], [Condition B] → [Destination Node ID]

Termination:
- Success: [Node ID] — [Label]
- Error: [Node ID] — [Label]

### 5) Decision Tree Summary

Consolidated view of all decision nodes across all flows.

| Decision Node ID | Label | Condition A | Destination A | Condition B | Destination B | Linked FR/AC |
|-----------------|-------|-------------|---------------|-------------|---------------|--------------|

### 6) Cross-Flow Integration Points

Nodes shared across multiple flows.

| Node ID | Node Label | Appears in Flows | Notes |
|---------|-----------|-----------------|-------|

### 7) FigJam Build Instructions

**Canvas setup:**
- Create one labeled section (FigJam Section) per primary flow
- Within multi-persona maps, use horizontal swim lanes inside each section
- Place the Node Legend in a dedicated frame in the top-left corner of the canvas
- Use a consistent node grid: 200 × 80 px for screens and actions, 120 × 120 px for decisions

**For each flow section:**
1. Place the Entry Point node at the top of the section
2. Add Screen and Action nodes in sequential order, flowing top-to-bottom or left-to-right
3. At each Decision diamond, fork with clearly labeled connectors for every condition
4. Terminate every path with a Success (teal) or Error (red) node — no dangling connectors
5. Add sticky note annotations beside decision nodes and error states citing linked FR/AC IDs

**Connector conventions:**
- Solid arrow: forward / positive path
- Dashed arrow: conditional or alternate path
- Red-colored arrow: error or failure path
- Label every connector at a decision point with a short condition phrase (for example `If verified`, `On timeout`, `No results found`)

**Cross-flow links:**
- Use a gray connector for any node referenced in more than one flow section
- Add the shared node ID to a sticky note in each referencing flow section

### 8) Requirement Traceability Map

| Node ID | Node Label | Flow | FR IDs | AC IDs | Coverage Status |
|---------|-----------|------|--------|--------|-----------------|

Coverage status values:
- **Covered** — node maps explicitly to at least one FR or AC
- **Partial** — node relates to a requirement but mapping is inferred; needs confirmation
- **Gap** — requirement present in PRD but not represented in any node

### 9) Handoff Notes for Figma Make

Summarize what `inc-prd-figma-make` needs before building screen specs:
- Flow conditions to encode as interactive prototype triggers and transitions
- Screens requiring multiple states (empty, loading, error, success, blocked)
- Decision points that require conditional visibility or navigation branching in Figma Make
- Data fields or validation rules surfaced by the flow that must appear in screen specs
- Open questions from the flow map that must be resolved before screens can be fully specified

## Style rules

- Assign short, unique node IDs using a prefix per type: `ENT-` (entry), `SCR-` (screen), `ACT-` (action), `DEC-` (decision), `SYS-` (system event), `ERR-` (error), `EXIT-` (success/exit)
- Number IDs sequentially per type within each flow (for example `SCR-01`, `SCR-02`, `DEC-01`)
- Use imperative verbs for action nodes (for example `Submit form`, `Select filter`, `Confirm deletion`)
- Use question form for decision node labels (for example `Is user authenticated?`, `Has required permission?`)
- Do not invent business logic not present in the PRD; record invented logic as an explicit assumption
- Preserve domain terminology from the PRD
- Keep node labels concise (five words or fewer when possible)

## Quality bar

Before finalizing, verify:
- Every persona mentioned in the PRD scope has at least one flow
- Every flow has at least one success path and at least one error or empty-state path
- Every decision node has at least two labeled outgoing connectors
- Every functional requirement in scope is represented in at least one node or flagged as a coverage gap
- The Handoff Notes section contains at least three specific, actionable insights for `inc-prd-figma-make`
- No dangling nodes exist (every node except exits has at least one outgoing connector)

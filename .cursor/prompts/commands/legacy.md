# Legacy - Reverse Engineering Documentation

Analyzes existing code and generates documentation (ADR/SDD/DDD/TDD/VDD flows) automatically.

## Command: $ARGUMENTS

```
/legacy                              # BFS from project root
/legacy src/auth                     # BFS from src/auth (analyze only this subtree)
/legacy src/auth "JWT validation"    # DFS: focus on "JWT validation" within src/auth
```

### Mode Selection

| Arguments | Mode | Behavior |
|-----------|------|----------|
| none | BFS | Full project analysis, breadth-first |
| path only | BFS | Analyze subtree starting from path |
| path + "comment" | DFS | Deep focus on comment topic within path |

**Path** = WHERE to look for source code (starting point)
**Comment** = WHAT to focus on (triggers DFS mode)

---

## Core Concept: Recursive Understanding Tree

**Critical**: This is NOT filesystem mirroring. AI builds a **logical understanding tree** that grows DEEP, not wide.

```
WRONG (mirror filesystem):
analysis/src/auth/jwt/tokens/_analysis.md  ❌

WRONG (flat structure):
analysis/depth-0.md, depth-1.md, depth-2.md  ❌

RIGHT (logical tree growing deep):
understanding/
├── _root.md                      # Project overview
└── core-domain/                  # Logical concept (NOT a source path!)
    ├── _node.md                  # Understanding of this level
    └── authentication/           # Deeper concept
        ├── _node.md
        └── token-lifecycle/      # Even deeper
            └── _node.md
```

Each directory = logical concept discovered during analysis.
Each `_node.md` = understanding at that depth level.
Tree grows as AI discovers deeper concepts to explore.

---

## Recursive Traversal Algorithm

AI performs **depth-first traversal** of understanding tree, persisting state to `_traverse.md`.

```
RECURSIVE-UNDERSTAND(node):
    1. ENTER   → Push to stack, create _node.md, form hypothesis
    2. EXPLORE → Read source code, validate understanding
    3. SPAWN   → Identify child concepts needing deeper analysis
    4. RECURSE → For each child: RECURSIVE-UNDERSTAND(child)
    5. SYNTH   → Combine children insights, update _node.md
    6. EXIT    → Pop from stack, bubble summary to parent
```

### Phase Diagram

```
        ┌─────────────────────────────────────────┐
        │                                         │
        ▼                                         │
    ENTERING ──► EXPLORING ──► SPAWNING           │
        │                          │              │
        │                          ▼              │
        │                    [has children?]      │
        │                     /         \         │
        │                   yes          no       │
        │                    │            │       │
        │                    ▼            │       │
        │               RECURSE ──────────┤       │
        │              (for each)         │       │
        │                    │            │       │
        │                    ▼            ▼       │
        │               SYNTHESIZING ◄────┘       │
        │                    │                    │
        │                    ▼                    │
        └─────────────── EXITING ─────────────────┘
                            │
                            ▼
                     [pop from stack]
                     [bubble up to parent]
```

---

## State Persistence: _traverse.md

AI reads `_traverse.md` to know exactly where it is and what to do next.

### Stack Structure

```markdown
## Current Stack

/ (root)                           DONE
└── core-domain                    DONE
    └── authentication             EXPLORING ← current position
        └── token-management       PENDING (child to explore)
```

### Resume Protocol

1. Read `_traverse.md`
2. Find top of stack (current position)
3. Check phase (ENTERING/EXPLORING/SPAWNING/SYNTHESIZING/EXITING)
4. Execute that phase's actions
5. Update `_traverse.md` with new state
6. Continue or pause for next invocation

### Phase Actions

| Phase | Read | Write | Next |
|-------|------|-------|------|
| ENTERING | Source paths | _node.md (hypothesis) | EXPLORING |
| EXPLORING | Source code | _node.md (validated) | SPAWNING |
| SPAWNING | _node.md | Pending children | RECURSE or SYNTH |
| SYNTHESIZING | Children summaries | _node.md (synthesis) | EXITING |
| EXITING | _node.md | Parent's bubble-up | Pop stack |

---

## Directory Structure

```
flows/legacy/
├── _status.md                    # Overall progress
├── _traverse.md                  # Recursion stack & state
├── log.md                        # Iteration history
├── understanding/                # The tree (grows deep)
│   ├── _root.md                  # Entry point
│   ├── _node.template.md         # Template for new nodes
│   └── [domain]/                 # First logical domain
│       ├── _node.md
│       └── [subdomain]/          # Deeper...
│           ├── _node.md
│           └── [concept]/        # Even deeper...
│               └── _node.md
├── mapping.md                    # Node → Flow mapping
└── review.md                     # Items for human review
```

---

## Flow Type Detection

Flows are per-module, not per-file-type.

### Decision by Purpose

| Purpose | Flow Type |
|---------|-----------|
| Internal service logic | SDD |
| Stakeholder-facing feature | DDD |
| Correctness-critical logic | TDD |
| User experience primary | VDD |

### TDD Indicators (Cases-First)
- High test coverage (>80%)
- Tests define behavior, not verify implementation
- Edge cases matter, failures have consequences

### DDD Indicators (Stakeholder Communication)
- Needs explanation to clients/executives
- Feature is "sellable"
- Documentation is a deliverable

---

## Execution Steps

### Step 1: Initialize

```
1. Read _traverse.md
2. If empty: create root node, push to stack
3. Determine mode from arguments
```

### Step 2: Traverse (Recursive)

Execute current phase, update state, continue or pause.

**Each invocation:**
```
1. Read _traverse.md (current position)
2. Execute phase actions
3. Update _traverse.md (new state)
4. Update _node.md (current understanding)
5. If more work: continue
6. If paused/interrupted: state is saved
```

### Step 3: Generate Flows

When a node reaches EXITING with high confidence:
```
1. Create flows/[type]-[name]/
2. Generate 01-requirements.md from understanding
3. Generate 02-specifications.md from code analysis
4. Status = DRAFT
```

### Step 4: Generate ADRs

For discovered architectural decisions:
```
1. Create flows/adr-[NNN]-[name]/
2. Type: constraining | enabling
3. Status = DRAFT
```

---

## Idempotency & Existing Flows

Command is safe to run multiple times. Respects existing ADR/SDD/DDD/TDD/VDD flows.

### Check-Before-Write Protocol

For each discovered module/decision:
```
1. CHECK: Does flows/[type]-[name]/ exist?

2. IF EXISTS:
   - Read existing 01-requirements.md, 02-specifications.md
   - Compare with new analysis
   - APPEND only new insights (don't overwrite)
   - Mark as UPDATED in mapping.md

3. IF NOT EXISTS:
   - Create new flow directory
   - Generate documents from understanding
   - Mark as CREATED in mapping.md

4. IF CONFLICT (analysis contradicts existing):
   - Do NOT modify existing flow
   - Add to review.md with CONFLICT flag
   - Human must resolve
```

### Additive-Only Changes

When updating existing flows:
```markdown
## [Existing Section]
[original content unchanged]

## [Existing Section] - Legacy Additions
> Added by /legacy on [DATE]

- [new insight discovered]
- [nuance not previously documented]
```

### Mapping Status

| Status | Meaning |
|--------|---------|
| CREATED | New flow created by /legacy |
| UPDATED | Existing flow received new insights |
| UNCHANGED | Flow exists, no new info found |
| CONFLICT | Analysis contradicts existing docs |

### State Recovery
- _traverse.md fully describes current position
- Can resume from any interruption
- Phase operations are idempotent

---

## Example Traversal

```
Invocation 1:
  Read _traverse.md: empty
  Action: Create root, ENTERING
  Write: understanding/_root.md
  Update: _traverse.md (stack: [/ ENTERING])

Invocation 2:
  Read: stack = [/ ENTERING]
  Action: EXPLORING root
  Write: _root.md (validated understanding)
  Update: _traverse.md (stack: [/ EXPLORING])

Invocation 3:
  Read: stack = [/ EXPLORING]
  Action: SPAWNING - found "authentication" domain
  Write: Pending children: [authentication]
  Create: understanding/authentication/
  Update: _traverse.md (stack: [/ SPAWNING], pending: [auth])

Invocation 4:
  Read: stack = [/ SPAWNING], pending: [auth]
  Action: RECURSE into authentication
  Push: authentication to stack
  Update: _traverse.md (stack: [/ SPAWNING, auth ENTERING])

Invocation 5:
  Read: stack = [/ SPAWNING, auth ENTERING]
  Action: ENTERING authentication
  Write: understanding/authentication/_node.md
  ... continues deep ...
```

---

## _node.md Structure

```markdown
# Understanding: [Logical Name]

## Phase: EXPLORING

## Hypothesis
[Initial guess]

## Sources
- src/auth/*.ts - authentication logic
- src/middleware/auth.ts - middleware

## Validated Understanding
[Confirmed after code analysis]

## Children
| Child | Status |
|-------|--------|
| token-lifecycle | PENDING |
| session-mgmt | PENDING |

## Flow Recommendation
Type: SDD
Confidence: high
Rationale: Internal service, no stakeholder docs

## Bubble Up
- Handles JWT validation
- Depends on crypto module
```

---

## Always

- Persist state after EVERY action
- Tree grows DEEP (concepts within concepts)
- Names are LOGICAL (not source paths)
- One node may reference MANY source files
- Resume from _traverse.md
- Flows created in DRAFT only
- Never auto-approve

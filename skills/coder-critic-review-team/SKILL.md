---
name: coder-critic-review-team
description: Multi-agent coder-critic team workflow with unlimited review rounds and direct inter-agent communication
triggers:
  - "coder-critic"
  - "无限审核"
  - "无限轮审查"
  - "agent team 代码审查"
  - "coder critic pair"
  - "review team"
---

# Coder-Critic Agent Team Workflow

## Core Rule: Team-Lead Never Writes or Reviews Code

**The team-lead is a coordinator, not a coder or reviewer.** All code writing must be done by coder agents. All code review must be done by critic agents.

Team-lead may only: check coder/critic progress, relay messages verbatim when direct communication fails (no summarization or interpretation), and make escalation decisions after 3 strikes.

**Why this destroys the workflow if violated:** The coder-critic pair is an adversarial quality system — the coder knows a critic will check their work, and the critic has no incentive to approve sloppy code because they didn't write it. The moment team-lead writes a line of code, they become an uncriticized coder. The moment team-lead reviews a line of code, they become a critic without a counterpart. Both break the separation of powers that makes this pattern work. No exceptions — not for "trivial fixes," not for "just this once."

If team-lead writes or reviews code: the task has failed. Stop and report to the user.

## The Insight

Code review by spawning agents is NOT fire-and-forget. The right pattern is a **closed-loop system**: coder and critic form a persistent pair within one team, communicating directly via SendMessage across unlimited rounds until score ≥ 80. The critic must be the **same instance** across rounds — spawning a new critic each round wastes context and loses prior findings.

## Why This Matters

Without this pattern:
- Each critic spawn re-reads all files from scratch, duplicating work
- Prior round feedback is lost, causing repeated fixes of already-resolved issues
- Coder never learns from critic's feedback because they never see it directly
- Team-lead becomes bottleneck relaying messages between coder and critic
- Sessions bloat from redundant agent spawns

## Recognition Pattern

Use this when:
- Modifying >1 file in a shared pipeline
- Code correctness matters more than speed
- Changes touch data logic (SQL, transformations, cleaning)
- Multiple developers could work on different files concurrently
- User says "coder-critic team", "无限审核", "review until pass"

## The Approach

### 1. Team Setup

```
TeamCreate → TaskCreate (one per file/concern) → spawn coders → wait → spawn critics
```

**Rule**: One team for all related work. Don't create new teams for sub-tasks.

### 2. Task Division

Split work by **file ownership**, not by step:
- Task A: `track_a_comnum_multi.py` → coder-a owns this file
- Task B: `prep_comnum1_multi.py` → coder-b owns this file

Each coder reads their file(s) and implements changes independently. Coders never touch each other's files.

### 3. Coder Briefing

Every coder prompt MUST include:
1. **Exact file paths** to modify
2. **Specific changes** — what to add/remove/change, not vague goals
3. **What NOT to change** — prevent scope creep
4. **Verification steps** — how to confirm the edit worked
5. **"Send results via SendMessage to team-lead when done"**

Example:
```
Modify `D:\path\to\file.py`:
1. Replace X with Y at line N
2. Remove unused import Z

Do NOT refactor other code. Do NOT add features.
After editing, grep for X to verify it's gone.
SendMessage to team-lead when done.
```

### 4. Critic Briefing

Every critic prompt MUST include:
1. **Exact file paths** to review
2. **What changed** — so they know what to focus on
3. **Specific verification points** — checklist of things to confirm
4. **Scoring criteria** — what categories to score against
5. **"Send report via SendMessage to team-lead"** — CRITICAL, otherwise results only visible in session transcript

```python
# CRITIC PROMPT MUST END WITH:
"Report all issues with severity (CRITICAL/HIGH/MEDIUM/LOW), file:line, suggested fix. 
Give overall score /100. Send final report via SendMessage to team-lead."
```

### 5. Unlimited Review Loop (THE KEY PATTERN)

```
Round 1: coder finishes → spawn critic → critic reviews → score < 80?
  ↓ YES
Round 2: SendMessage to coder with critic's feedback → coder fixes → 
         SendMessage to SAME critic → critic re-reviews → score < 80?
  ↓ YES
Round 3+: Continue until score >= 80 or 3 strikes
  ↓ 3 strikes with no improvement → ESCALATE to team-lead
```

**CRITICAL: Reuse the same critic instance across rounds.**

```python
# RIGHT: Send feedback to existing critic for re-review
SendMessage(to="critic-b", message="Round 2 review: coder fixed issues 1-6. Re-check.")

# WRONG: Spawn new critic for each round
Agent(name="critic-b-r2", ...)  # loses prior context, re-reads everything
```

After each round, critic should report: "Round N. Previous score: X. New score: Y. Remaining issues: [...]"

### 6. Direct Agent-to-Agent Communication

Agents can SendMessage to EACH OTHER, not just to team-lead:

```
coder-a ──SendMessage──→ critic-a    (coder reports completion)
critic-a ──SendMessage──→ coder-a    (critic sends feedback directly)
critic-a ──SendMessage──→ team-lead  (critic reports final score)
```

The team-lead only needs to:
- Initialize the loop (spawn coders, spawn critics)
- Relay Round 1 feedback if critic didn't directly message coder
- Make escalation decisions after 3 strikes

**Do NOT be the bottleneck** — once the loop starts, coders and critics should communicate directly.

### 7. Critic Tool Limitations (Separation of Powers)

Critics (`coder-critic` type) have: Read, Grep, Glob, Agent. **No Write, Edit, or Bash.**

This is intentional. Critics:
- Read code and produce reports
- Dispatch verifier agents for execution checks
- NEVER fix code themselves

If a critic needs to verify execution, they spawn a verifier via `Agent(subagent_type="verifier")`.

### 8. Getting Critic Results (Common Pitfall)

Critics write their detailed report in their session transcript (`subagents/agent-*.jsonl`). The brief summary sent via SendMessage may omit details.

**To get the full report:**
1. Check the critic's idle notification for its agent ID
2. Read the last assistant message in its session file:
   ```
   subagents/agent-{id}.jsonl → last {"role":"assistant"} → content[].text
   ```
3. OR: Require in the prompt that the critic SendMessage the FULL report text

### 9. Parallel Execution

Multiple coder-critic pairs can work concurrently on different files:

```
Team opt-pipeline:
  ├── coder-a + critic-a  →  track_a_comnum_multi.py
  └── coder-b + critic-b  →  prep_comnum1_multi.py + merge_yearly.py
```

Spawn all coders in one message (parallel), wait for all to finish, then spawn all critics in one message.

### 10. Shutdown Protocol

After all pairs pass (score ≥ 80):
1. SendMessage `shutdown_request` to each remaining agent
2. Wait for `teammate_terminated` events
3. `TeamDelete` to clean up

If agents won't terminate: manually remove `~/.claude/teams/{name}/` and `~/.claude/tasks/{name}/`.

## Quality Gates

| Gate | Threshold | Action |
|------|-----------|--------|
| Commit | ≥ 80 | Allow |
| Blocked | < 80 | Fix and re-review |
| Stuck | 3 rounds, no improvement | Escalate to user |
| Pass | ≥ 80, no CRITICAL/HIGH | Merge ready |

## Anti-Patterns

- **Spawning new critic each round** — loses context, wastes tokens
- **Team-lead relaying all messages** — becomes bottleneck, agents should talk directly
- **Skipping critic review** — even trivial changes benefit from second pair of eyes
- **Critic fixing code** — separation of powers: critics never write
- **Not telling critic to SendMessage results** — report trapped in session transcript

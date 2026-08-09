# Task Blackboard

有效状态：`BACKLOG` / `IN_PROGRESS` / `BLOCKED` / `REVIEW` / `DONE`

| Task | Owner | Status | Contract / Output | Blockers |
|---|---|---|---|---|
| `001-fix-login-bug` | codex | DONE | `artifacts/contract/001-fix-login-bug.md` → 审查通过 | None |
| `002-full-refresh-job` | zcode | REVIEW | `artifacts/contract/002-full-refresh-job.md` | None |
| `003-performance-audit` | Claude子代理 | IN_PROGRESS | `artifacts/contract/003-performance-audit.md` | `001-fix-login-bug` |
| `004-release-v2.1` | Claude | BACKLOG | 无（汇总各执行者证据） | `002-full-refresh-job`, `003-performance-audit` |

规则：单一 owner / 单一 write scope；状态或产物消费变化时才更新；Blockers 指向阻塞源。

---
name: commander-executor
description: |
  大型项目「指挥官—多执行者」分工工作流。Claude 当指挥官（规则/拆解/分配/审查/验收/总结），执行者名册：zcode=全量批量、codex=debug与代码、codex-deepseek=省额度代码活、Claude子代理=数据研究文档。
  自动触发：负责大型/长期项目；需要任务拆解与监督；Claude+codex+zcode 多 CLI 分工；跨会话交接；「指挥官」「任务黑板」「TASKS.md」「谁负责哪块」「派给谁」。
  核心协议借鉴 changocr/agents-lab：TASKS.md 任务黑板 + artifacts/ 持久消息总线 + creator/reviewer/verifier 职责分离 + 规则化派发。
---

# 指挥官—执行者工作流

## 角色分工

| 角色 | 工具 | 职责 | 权限 |
|---|---|---|---|
| 指挥官 | Claude Code | 制定规则、拆解任务、写规则、按名册分配、只读审查、验证证据、更新黑板、总结进度与规划报告 | 可读写 TASKS.md 与 artifacts/ |
| 执行者（名册） | zcode / codex / Claude子代理 | 按规则实现、产出代码与证据 | 只读写规则指定范围 |
| 审查者 | Claude 独立只读 | 审查执行结果，按严重度门禁 | 只读 |
| 验证者 | Claude | 核对"确实跑了"的证据与产物 | 只读 |

同一会话内：指挥官可自行承担审查与验证，但**审查必须发生在派发之外的另一轮思考**，不能"写完自己盖章"。

## 执行者名册与路由

| 执行者 | 后端 | 适配任务 | 启动 |
|---|---|---|---|
| `zcode` | GLM/Kimi（智谱） | **全量/批量任务**：量大便宜，Coding Plan 每日约 300 万 token 免费 | `zcode` |
| `codex` | GPT-5.6-Terra | **debug、疑难代码**：质量优先 | `codex "..."` |
| `codex-deepseek` | DeepSeek | 普通代码活但不想花 GPT 额度时 | `codex-deepseek "..."` |
| Claude 子代理 | DeepSeek | 只读调研、数据、文档、代码审查 | 用 Agent 工具 |

路由规则：**按任务类型，不按心情。**
- 全量执行/大批量/机械性改动 → `zcode`
- 复现+定位+修复的疑难 bug、核心算法 → `codex`
- 只读调研、文档撰写、代码审查 → Claude 子代理
- 任务量小且不需要 GPT 质量 → `codex-deepseek` 省额度

> zcode 尚未安装时先装：`npm install -g @zcode/cli` → `zcode login`（智谱账号 open.bigmodel.cn）→ 项目目录 `zcode` 启动。API Key 用 ZAI_API_KEY 或智谱 Coding Plan 端点，具体以官方文档为准。

## 项目脚手架

```
项目根/
├── TASKS.md          # 唯一任务黑板（owner/状态/规则/阻塞）
├── AGENTS.md         # 项目级约束（可选）
└── artifacts/
    ├── rules/        # 派发给执行者的任务规则（自包含）
    ├── code/         # 执行产物说明/关键输出
    ├── review/       # 审查报告（原文保留）
    ├── verify/       # 验证证据
    └── handoff/      # 跨会话交接
```

## TASKS.md 黑板模板

状态仅允许：`BACKLOG` / `IN_PROGRESS` / `BLOCKED` / `REVIEW` / `DONE`。

| Task | Owner | Status | 规则 / 产出 | Blockers |
|---|---|---|---|---|
| `example-task` | Claude/Codex | BACKLOG | `artifacts/rules/xxx.md` | None |

规则：
- 每个任务**单一 owner**、单一 write scope；
- 只有状态或产物消费实际变化时才更新黑板；
- Blockers 指向阻塞它的任务或外部依赖。

## 任务规则模板（唯一权威，派发前必须自包含）

规则本质是**规则集**，执行者必须逐条遵守，任何一条未满足即未完成。执行者会话看不到指挥官上下文，规则必须能独立成立。`caw new-task` 以 `templates/rule.md.tpl` 为唯一模板生成，此处与之保持一致：

```markdown
# 任务：{任务名}

> 本文件是任务规则集，执行者必须逐条遵守；任何一条未满足，任务即未完成。

- ID：`{任务ID}`
- Owner：{执行者}
- Blockers：{阻塞源}

## 目标

{为什么做，完成到什么程度才算达成}

## 范围（in-scope）

{只允许改动的文件，明确 write scope，不得超出}

## 排除（out-of-scope）

{禁止触碰的相邻代码/文件，即使看起来相关也不得改动}

## 约束

{硬性限制：语言/框架/风格/性能/不引入新依赖等，必须遵守}

## 验收标准

{可执行、可逐条勾选：命令/测试/产物路径；全部通过才算 DONE}

## 输出证据

{必须汇报：跑了哪些命令、产物在哪、测试结果；不得只回"已完成"}
```

## caw 工具速查

协议落地为 `caw` CLI（仓库根 `caw.py`），全量子命令：

```bash
caw init                                       # 生成 TASKS.md + artifacts/ 骨架
caw new-task "标题" --owner codex --dep 001    # 建规则 + 登记黑板
caw show 001                                   # 查看规则内容
caw dispatch 001                               # 按 owner 打印派发命令
caw review 001                                 # 标记进入审查 REVIEW
caw verify 001 --evidence "pytest 全绿"         # 验证并完成 DONE（记录证据）
caw done 001                                   # 快捷完成 DONE
caw status / handoff                           # 汇总状态 / 跨会话交接
caw install / sync                             # 装/同步 skills 到 ~/.claude/skills/
```

完整子命令说明见仓库 README「caw CLI」章节。

## 流程

1. **拆解**：指挥官读 TASKS.md 与项目，把目标拆成有依赖边界的任务，标 owner 与顺序。
2. **写规则**：每个待派发任务写 `artifacts/rules/{task}.md`，正文全部进文件，聊天只传状态与路径。
3. **派发**：按「执行者名册与路由」选定执行者：
   - `zcode "读 artifacts/rules/{task}.md 并严格执行"`
   - `codex "读 artifacts/rules/{task}.md 并严格执行"`（或 `codex-deepseek`）
   - 只读类工作派给 Claude 子代理
4. **执行**：执行者实现并汇报证据（状态 + 路径 + 命令输出）。**全程不声明未运行过的验证。**
5. **审查**：Claude 只读审查 diff 与规则，按 `CRITICAL/HIGH/MEDIUM/LOW` 分级；`CRITICAL`/`HIGH` 阻断完成，退回执行者修订后复审。报告原文存 `artifacts/review/`。
6. **验证**：核对证据与产物真实存在、命令确实跑过、测试通过；区分"已实现/已审查/已验证"三种状态，不混用。
7. **更新黑板**：按实况改 TASKS.md 状态。
8. **交接**：跨会话或换人时写 `artifacts/handoff/`：已完成、当前文件、最后成功证据、阻塞、下一步精确动作。

## 硬规则

- **单一事实源**：任务状态只看 TASKS.md，完整正文只在 artifacts/，聊天不承载正文。
- **职责分离**：creator 实现，reviewer 只读审查，verifier 核对证据；CRITICAL/HIGH 不通过不标 DONE。
- **最小改动**：满足规则即可，不顺手改相邻代码或格式。
- **不越权**：缺授权、涉隐私数据、未解决 CRITICAL/HIGH 时停下并上报指挥官。
- **上下文交接代价**：每次 Claude↔各执行者切换以规则文件为准，避免口头传上下文；不同执行者互不相通，规则要更自包含。

## 应用示例

- 长项目初始化：指挥官拆 5 个任务 → 写 5 份规则 → 逐个派给执行者 → 审查+验证后更新 TASKS.md → 下班写 handoff。
- 多执行者协作：zcode 跑全量数据/批处理，codex 修疑难 bug，Claude 子代理做只读审查；Claude 汇总各执行者证据，更新 TASKS.md 并输出阶段进度与规划报告。
- 疑难 bug：把"复现+定位+修复+单测"打包成一份规则丢给 GPT，Claude 只审 diff 与测试证据，省 DeepSeek 上下文。

# Claude Agent Workflows

一套跨 Claude Code / Codex / ZCode 的个人工作流 Skill 集合与 Claude Code 配置指南。

## 内容

| 目录 | 功能作用 |
|---|---|
| `skills/commander-executor/` | **多 Agent 分工总控**：Claude 当指挥官（规则/拆解/分配/审查/验收/总结），把自包含任务规则派发给外部执行者——zcode=批量、codex=debug、claude子代理=只读，通过 TASKS.md 黑板 + artifacts/ 规则总线协作。适用大型/长期项目、跨 CLI 协作。触发词：任务拆解、谁负责哪块、指挥官 |
| `skills/resume-generator/` | **校招简历生成器（模板版）**：事实库 → 竞争策略（Winning Thesis / Evidence Map）→ 行业路由 → 表达保护 → 质检 Reviewer → 单页中文简历 PDF。含**完整虚构示例**（填好的事实库 + 示例 HTML + 构建脚本，纯中性设定）。适用投递前定制简历、匹配度分析。触发词：发 JD 要简历、帮我看看适合吗。⚠️ 本目录为脱敏模板，填入真实数据前请先阅读隐私提示 |
| `skills/gaodun-essay-grader/` | **申论大作文批改**：模拟高顿五维评分体系（立意/论证/素材/语言/结构），40 分制评分 + 逐维度分析 + 改进示例 + 提分优先级。适用公考申论作文批改。触发词：发作文要打分 |
| `skills/md2pdf/` | **MD → 专业中文 PDF**：MD → TEX（ctexart）→ PDF（XeLaTeX）管线，严格 TFP 排版风格。适用正式中文文档排版出 PDF。触发词：生成 PDF、按 TFP 格式 |
| `skills/coder-critic-review-team/` | **多 Agent 代码审查**：coder-critic 协作评审，无限轮迭代、agent 间直接沟通。适用代码质量把关、PR 审查 |
| `skills/workflow-to-skill/` | **工作流沉淀**：Agent 工作流结束后自动把流程固化为可复用 Skill 并入系统级目录。适用把一次性复杂流程沉淀成方法论。触发词：沉淀为 skill、记住这个流程 |
| `guides/claude-code-config-guide/` | **Claude Code 配置指南**（DeepSeek 版保姆级教程）：Node.js → Git → Claude Code → 编辑器 → DeepSeek API 连接 → Skill 导入，含 Windows PowerShell 权限问题。MD / TEX / PDF 三格式 |
| `caw.py` + `templates/` | **commander-executor 落地 CLI**：`init / new-task / show / dispatch / review / verify / done / set / status / handoff / install / sync` 十二子命令。纯 Python 标准库，零依赖 |
| `examples/commander-executor/` | **端到端 demo**：`demo.sh` 一键跑通 init→new-task→dispatch→status→handoff 全流程 |

## 安装 Skill

所有 Skill 都是标准 Claude Code Skill（`SKILL.md` + 可选 `references/`）。安装到本地即可被 Claude Code 自动识别：

```bash
# 克隆本仓库
git clone https://github.com/liuhao-hn/claude-multi-agent-workflows ~/claude-multi-agent-workflows

# 方式一：复制全部 skill（独立副本，推荐新手）
mkdir -p ~/.claude/skills
cp -r ~/claude-multi-agent-workflows/skills/* ~/.claude/skills/

# 方式二：软链接（跟随仓库更新，推荐进阶用户）
ln -s ~/claude-multi-agent-workflows/skills/commander-executor ~/.claude/skills/commander-executor
ln -s ~/claude-multi-agent-workflows/skills/md2pdf ~/.claude/skills/md2pdf
```

依赖说明：
- `resume-generator`：需要 Python3 + `pypdf` + Chrome（`python3 build_resume_{shortname}.py`）
- `md2pdf`：需要 XeLaTeX（`xelatex`），可选 `ctexart` 文档类
- `gaodun-essay-grader` / `coder-critic-review-team` / `workflow-to-skill` / `commander-executor`：零依赖，纯提示词
- `caw.py`：仅 Python3 标准库，零依赖

## caw CLI（把协议变成命令）

`commander-executor` 的落地工具，把 TASKS.md 黑板、规则生成、按执行者派发、状态汇总、跨会话交接全部变成一条命令：

```bash
# 安装（加个别名即可用）
alias caw="python3 ~/claude-multi-agent-workflows/caw.py"

# 用法（任务管理）
caw init                                        # 生成 TASKS.md + artifacts/ 骨架
caw new-task "修复登录bug" --owner codex --dep 001   # 建规则 + 登记黑板
caw show 001                                    # 查看规则内容
caw dispatch 001                                # 按 owner 打印派发命令
caw dispatch 002 --run                          # 打印后直接执行
caw review 001 --report "HIGH: 缺单测，退回"     # 审查（REVIEW）+ 报告存档 artifacts/review/
caw verify 001 --evidence "pytest 全绿"          # 验证并完成（DONE + 记录证据）
caw done 001                                    # 快捷完成（DONE）
caw set 001 IN_PROGRESS                         # 更新任意状态
caw status                                      # 汇总状态，标出 BLOCKED/REVIEW
caw handoff                                     # 生成跨会话交接文档

# 用法（skill 管理）
caw install                                     # 把仓库 skills 装进 ~/.claude/skills/（跳过已存在）
caw sync                                        # 仓库 skills 同步到本地（默认跳过 resume-generator，保护本地真实数据）
```

支持执行者：`zcode`（批量）/ `codex`（debug）/ `codex-deepseek`（省额度）/ `claude-subagent`（只读）。派发命令由 owner 自动路由。

> ⚠️ **codex 非交互执行注意**：`codex exec` 需加 `-s workspace-write`，否则默认沙箱写入不持久化；在 `~/` 受信目录可省 `--skip-git-repo-check`。`codex-deepseek` 只适合纯文本，agentic 写文件请用 codex-GPT 或 Claude 子代理。

完整演示：`bash examples/commander-executor/demo.sh`
测试：`python3 -m unittest tests.test_caw`

## 快速上手

### commander-executor（多 Agent 分工）

一个可直接套用的最小示例见 [`examples/commander-executor/`](./examples/commander-executor/)。

适用于大型/长期项目，由 Claude 统筹、多个外部 CLI 执行：

```text
项目根/
├── TASKS.md          # 唯一任务黑板（owner/状态/规则/阻塞）
└── artifacts/
    ├── rules/        # 派发给执行者的任务规则（自包含）
    ├── review/       # 审查报告
    └── handoff/      # 跨会话交接
```

派发示例：

```bash
# 批量任务 → zcode（GLM）
zcode "读 artifacts/rules/task-001.md 并严格执行"
# 疑难 debug → codex（GPT）
codex "读 artifacts/rules/task-002.md 并严格执行"
# 只读调研 → Claude 子代理
```

核心原则：任务状态只看 TASKS.md，正文只在 artifacts/；creator 实现、reviewer 只读审查、verifier 核对证据；CRITICAL/HIGH 不通过不标 DONE。完整协议见 `skills/commander-executor/SKILL.md`。

> 以上手动流程可以用 `caw` 工具自动化（见下文「caw CLI」章节）。

其他 skill 的用法见各自 `SKILL.md`，触发条件已在「内容」表格列出。

## 致谢 / Credits

部分设计概念参考自 [agents-lab](https://github.com/changocr/agents-lab) 与 [autumn-recruitment-resume-ai-system](https://github.com/changocr/autumn-recruitment-resume-ai-system)（均 MIT）。

## License

MIT。见 [LICENSE](./LICENSE)。

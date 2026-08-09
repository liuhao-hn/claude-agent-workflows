# Claude Agent Workflows

一套跨 Claude Code / Codex / ZCode 的个人工作流 Skill 集合与 Claude Code 配置指南。

## 内容

| 目录 | 说明 |
|---|---|
| `skills/commander-executor/` | **指挥官—多执行者**工作流：Claude 当指挥官（规则/拆解/分配/审查/验收/总结），执行者名册（zcode=批量、codex=debug、claude 子代理=只读）通过 TASKS.md 黑板 + artifacts/ 契约总线协作 |
| `skills/resume-generator/` | **校招简历生成器（模板版）**：事实库 → 竞争策略 → 行业路由 → 表达保护 → 质检 Reviewer，生成单页中文简历 PDF。本目录为脱敏模板，填入真实数据前请先阅读其中隐私提示 |
| `skills/gaodun-essay-grader/` | **申论大作文批改**：模拟高顿五维评分体系（立意/论证/素材/语言/结构），40 分制评分 + 逐维度分析 + 改进示例 + 提分优先级 |
| `skills/md2pdf/` | **MD → 专业中文 PDF**：严格 TFP 排版风格，MD → TEX（ctexart）→ PDF（XeLaTeX）管线 |
| `skills/coder-critic-review-team/` | **多 Agent 代码审查团队**：coder-critic 协作评审，无限轮迭代，agent 间直接沟通 |
| `skills/workflow-to-skill/` | **工作流沉淀**：Agent 工作流结束后自动把流程沉淀为可复用 Skill，并入系统级目录 |
| `guides/claude-code-config-guide/` | **Claude Code 完整配置指南**（DeepSeek 版保姆级教程）：Node.js → Git → Claude Code → 编辑器 → DeepSeek API 连接 → Skill 导入，含 Windows PowerShell 权限问题。MD / TEX / PDF 三格式 |

## 安装 Skill

所有 Skill 都是标准 Claude Code Skill（`SKILL.md` + 可选 `references/`）。安装到本地即可被 Claude Code 自动识别：

```bash
# 克隆本仓库
git clone https://github.com/liuhao-hn/claude-agent-workflows ~/claude-agent-workflows

# 方式一：复制全部 skill（独立副本，推荐新手）
mkdir -p ~/.claude/skills
cp -r ~/claude-agent-workflows/skills/* ~/.claude/skills/

# 方式二：软链接（跟随仓库更新，推荐进阶用户）
ln -s ~/claude-agent-workflows/skills/commander-executor ~/.claude/skills/commander-executor
ln -s ~/claude-agent-workflows/skills/md2pdf ~/.claude/skills/md2pdf
```

依赖说明：
- `resume-generator`：需要 Python3 + `pypdf` + Chrome（`python3 build_resume_{shortname}.py`）
- `md2pdf`：需要 XeLaTeX（`xelatex`），可选 `ctexart` 文档类
- `gaodun-essay-grader` / `coder-critic-review-team` / `workflow-to-skill` / `commander-executor`：零依赖，纯提示词

## 快速上手

### commander-executor（多 Agent 分工）

一个可直接套用的最小示例见 [`examples/commander-executor/`](./examples/commander-executor/)。

适用于大型/长期项目，由 Claude 统筹、多个外部 CLI 执行：

```text
项目根/
├── TASKS.md          # 唯一任务黑板（owner/状态/契约/阻塞）
└── artifacts/
    ├── contract/     # 派发给执行者的任务契约（自包含）
    ├── review/       # 审查报告
    └── handoff/      # 跨会话交接
```

派发示例：

```bash
# 批量任务 → zcode（GLM）
zcode "读 artifacts/contract/task-001.md 并严格执行"
# 疑难 debug → codex（GPT）
codex "读 artifacts/contract/task-002.md 并严格执行"
# 只读调研 → Claude 子代理
```

核心原则：任务状态只看 TASKS.md，正文只在 artifacts/；creator 实现、reviewer 只读审查、verifier 核对证据；CRITICAL/HIGH 不通过不标 DONE。完整协议见 `skills/commander-executor/SKILL.md`。

### resume-generator（单页简历）

工作流：事实库核对 → JD 拆解/行业路由 → Winning Thesis + Evidence Map → 生成 MD → Python/Chrome headless 构建 PDF → 独立质检 Reviewer。

```bash
# 需要：Python3 + pypdf + Chrome
cd skills/resume-generator && python3 build_resume_{shortname}.py
```

## 致谢 / Credits

设计思路受以下 MIT 项目启发：

- [changocr/agents-lab](https://github.com/changocr/agents-lab) — 任务黑板 / artifacts 消息总线 / creator-reviewer-verifier 职责分离
- [changocr/autumn-recruitment-resume-ai-system](https://github.com/changocr/autumn-recruitment-resume-ai-system) — 事实库唯一事实源 / 竞争策略 / 行业路由 / 表达保护 / 独立质检

## License

MIT。见 [LICENSE](./LICENSE)。

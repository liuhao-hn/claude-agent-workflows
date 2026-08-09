---
name: workflow-to-skill
description: |
  每次 Agent 工作流结束后，自动将工作流沉淀为可复用的 Skill，放入系统级目录。
  相似 Skill 自动合并优化。同时输出文件清单、更新 Memory，实现持续迭代学习。
  触发条件：Agent 任务结束、工作流完成、用户说"沉淀为 skill""记住这个流程""生成 skill"等。
---

# Workflow → Skill 自动沉淀引擎

## 触发时机

每次完成一个较复杂的 Agent 工作流后执行以下流程。判断标准：
- 涉及 3 个以上工具调用
- 有明确的输入 → 处理 → 输出链路
- 用户表示"以后都按这个来""记住这个做法""生成 skill"

## 工作流程

### Step 1: 输出文件清单

工作流结束后，列出本次涉及的所有文件：

```
## 本次涉及文件
- `/path/to/file1` — 新建/修改，说明
- `/path/to/file2` — 新建/修改，说明
```

### Step 2: 提取工作流要素

从本次对话中提取：
- **触发词**：用户用什么话触发了这个工作流
- **输入**：需要什么文件/信息
- **处理步骤**：核心操作流程（工具调用序列）
- **输出**：产出了什么
- **关键配置**：涉及的环境变量、路径、模板等

### Step 3: 检索相似 Skill

```bash
# 搜索已有 skill 中是否有相似功能
ls ~/.claude/skills/
# 读取每个 SKILL.md 的 description 和触发词，判断是否重叠
```

相似度判断标准：
- 相同工具链（如都是 xelatex 编译）
- 相同领域（如都是文档排版）
- 相同输入输出类型（如都是 MD→PDF）

### Step 4: 合并或新建

**如果找到相似 Skill（相似度 > 50%）：**
- 将新工作流合并进已有 Skill
- 扩展触发词列表
- 补充新的处理步骤/变体
- 更新 references 目录下的模板文件

**如果没有相似 Skill：**
- 在 `~/.claude/skills/<skill-name>/` 下创建：
  - `SKILL.md` — 主指令文件（含 frontmatter）
  - `references/` — 模板、配置等参考文件（如有）

### Step 5: 更新 Memory

将本次工作流的偏好和决策记录写入：
- `{Claude 记忆目录}` 下的对应文件
- 更新 `MEMORY.md` 索引（如需要）

## SKILL.md 模板

新建 Skill 时使用以下结构：

```markdown
---
name: <skill-name>
description: |
  <一句话描述>
  触发条件：<触发词列表>
---

# <Skill 标题>

## 工作流程

### Step 1: <步骤名>
<具体操作>

### Step 2: <步骤名>
<具体操作>

## 关键检查项
- [ ] <检查项>
```

## 排除范围

以下情况不生成 Skill：
- 一次性的临时操作（如"帮我看看这个文件"）
- 简单的信息查询（单次 Read/Grep 调用）
- 用户明确说不需要记住的操作
- 修复 bug 的临时调试过程

## 已沉淀的 Skill 列表

维护在 `~/.claude/skills/` 下，当前已有：

| Skill | 用途 |
|---|---|
| `academic-search` | 经济学论文搜索 |
| `coder-critic-review-team` | 多 Agent 代码审查 |
| `deeppapernote` | 论文深度阅读笔记 |
| `gaodun-essay-grader` | 申论大作文批改 |
| `md2pdf` | MD→TEX→PDF 专业排版 |

## 示例：本次 md2pdf 工作流的沉淀过程

1. **触发词**："生成 PDF""排版""按 TFP 格式输出"
2. **输入**：Markdown 文件
3. **处理**：读 MD → 写 ctexart TEX → xelatex 编译两遍 → 清理 aux 文件
4. **输出**：A4 PDF
5. **关键配置**：hidelinks, fvextra+breaklines, ragged2e+\RaggedRight, emergencystretch
6. **相似检索**：无已有 skill，新建 `md2pdf`
7. **模板沉淀**：`references/tex-template.tex`

# 示例：commander-executor 最小可套用结构

这是一个虚构的"数据看板项目"示例，展示指挥官—执行者协议的最小骨架：

```
examples/commander-executor/
├── TASKS.md                                   # 任务黑板：owner/状态/契约/阻塞
└── artifacts/contract/
    └── 002-full-refresh-job.md                # 一份自包含任务契约（派发给 zcode/codex）
```

## 使用流程

1. **拆解**：Claude 读 `TASKS.md`，把目标拆成有依赖边界的任务，标 owner 与顺序。
2. **写契约**：每个待派发任务写 `artifacts/contract/{task}.md`，正文全进文件，聊天只传状态与路径。
3. **派发**（按任务类型选执行者）：

   ```bash
   # 全量/批量任务 → zcode（GLM）
   zcode "读 artifacts/contract/002-full-refresh-job.md 并严格执行"
   # 疑难 debug → codex（GPT）
   codex "读 artifacts/contract/001-fix-login-bug.md 并严格执行"
   ```

4. **审查**：Claude 只读审查 diff，CRITICAL/HIGH 阻断，退回修订后复审。
5. **验证**：核对"确实跑了"的命令与产物，区分 已实现/已审查/已验证。
6. **更新黑板**：按实况改 `TASKS.md` 状态；跨会话前写 `artifacts/handoff/`。

完整协议见 [`skills/commander-executor/SKILL.md`](../../skills/commander-executor/SKILL.md)。

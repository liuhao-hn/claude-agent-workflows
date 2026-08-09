#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""caw — Claude Agent Workflows CLI.

把 commander-executor 的「指挥官—多执行者」协作协议落地为命令行工具。
仅依赖 Python 标准库，无第三方依赖。

子命令：
  init                生成 TASKS.md + artifacts/ 骨架
  new-task <标题>     创建任务规则并登记到 TASKS.md
  dispatch <任务ID>   按执行者打印派发命令（--run 直接执行）
  status              汇总 TASKS.md 任务状态
  set <任务ID> <状态>  更新任务状态（BACKLOG/IN_PROGRESS/BLOCKED/REVIEW/DONE）
  handoff             生成跨会话交接文档
"""

import argparse
import re
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

STATES = ("BACKLOG", "IN_PROGRESS", "BLOCKED", "REVIEW", "DONE")
OWNERS = ("zcode", "codex", "codex-deepseek", "claude-subagent")

DISPATCH = {
    "zcode": 'zcode "读 {rule} 并严格执行"',
    "codex": 'codex "读 {rule} 并严格执行"',
    "codex-deepseek": 'codex-deepseek "读 {rule} 并严格执行"',
    "claude-subagent": "（只读任务）用 Claude 子代理执行，规则：{rule}",
}

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"


def load_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def render(template: str, **kwargs: str) -> str:
    for key, value in kwargs.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def parse_tasks(blackboard: Path) -> list:
    """解析 TASKS.md 表格，返回任务 dict 列表；文件缺失或无可解析时返回空列表。"""
    if not blackboard.exists():
        return []
    lines = blackboard.read_text(encoding="utf-8").splitlines()
    data_start = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("|") and "Task" in s and "Owner" in s:
            data_start = i + 2  # 跳过表头与分隔行
            break
    if data_start is None:
        return []
    tasks = []
    for line in lines[data_start:]:
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 5:
            continue
        tid = cells[0].strip("` ").strip()
        if not tid or tid == "Task":
            continue
        tasks.append({
            "id": tid,
            "owner": cells[1].strip(),
            "status": cells[2].strip(),
            "rule": cells[3].strip(),
            "blockers": cells[4].strip(),
        })
    return tasks


def next_task_id(tasks: list) -> str:
    nums = []
    for t in tasks:
        m = re.match(r"(\d+)", t["id"])
        if m:
            nums.append(int(m.group(1)))
    return f"{max(nums) + 1:03d}" if nums else "001"


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w一-鿿]+", "-", text.lower()).strip("-")
    return slug or "task"


# ---- 子命令 ----

def cmd_init(args) -> None:
    root = Path(args.dir)
    root.mkdir(parents=True, exist_ok=True)
    bb = root / "TASKS.md"
    if bb.exists():
        print(f"已存在: {bb}")
    else:
        bb.write_text(load_template("TASKS.md.tpl"), encoding="utf-8")
        print(f"已创建: {bb}")
    for sub in ("rules", "review", "verify", "handoff"):
        p = root / "artifacts" / sub
        p.mkdir(parents=True, exist_ok=True)
        print(f"已创建: {p}/")


def cmd_new_task(args) -> None:
    root = Path(args.dir)
    bb = root / "TASKS.md"
    if not bb.exists():
        sys.exit("未找到 TASKS.md，先运行 caw init")
    tasks = parse_tasks(bb)
    tid = args.id or next_task_id(tasks)
    if any(t["id"] == tid for t in tasks):
        sys.exit(f"任务 ID 已存在: {tid}")
    slug = slugify(args.title)
    fname = f"{tid}-{slug}.md"
    rpath = root / "artifacts" / "rules" / fname
    if rpath.exists() and not args.force:
        sys.exit(f"规则已存在: {rpath}（用 --force 覆盖）")
    rpath.parent.mkdir(parents=True, exist_ok=True)
    tpl = load_template("rule.md.tpl")
    rpath.write_text(
        render(tpl, id=tid, title=args.title, owner=args.owner, dep=args.dep or "None"),
        encoding="utf-8",
    )
    rel = rpath.relative_to(root)
    row = f"| `{tid}` | {args.owner} | BACKLOG | `{rel}` | {args.dep or 'None'} |"
    text = bb.read_text(encoding="utf-8").rstrip() + "\n" + row + "\n"
    bb.write_text(text, encoding="utf-8")
    print(f"已创建规则: {rpath}")
    print(f"已登记: {bb} → {tid} ({args.owner}, BACKLOG)")


def cmd_dispatch(args) -> None:
    bb = Path(args.dir) / "TASKS.md"
    tasks = parse_tasks(bb)
    t = next((x for x in tasks if x["id"] == args.task), None)
    if not t:
        sys.exit(f"未找到任务: {args.task}")
    owner = t["owner"]
    if owner not in DISPATCH:
        sys.exit(f"未知执行者: {owner}（可用: {', '.join(OWNERS)}）")
    command = DISPATCH[owner].format(rule=t["rule"].strip("`"))
    print(command)
    if args.run:
        print(f"# 执行: {command}", file=sys.stderr)
        subprocess.run(command, shell=True, check=False)


def cmd_status(args) -> None:
    bb = Path(args.dir) / "TASKS.md"
    tasks = parse_tasks(bb)
    if not tasks:
        print("TASKS.md 无任务。")
        return
    c = Counter(t["status"] for t in tasks)
    summary = "  ".join(f"{s}={c.get(s, 0)}" for s in STATES)
    print(f"任务总数: {len(tasks)}  {summary}")
    attention = [t for t in tasks if t["status"] in ("BLOCKED", "REVIEW")]
    if attention:
        print("\n需要关注:")
        for t in attention:
            print(f"  ⚠ {t['id']:>6} [{t['status']}] owner={t['owner']:>14} 阻塞={t['blockers']}")
    done = [t for t in tasks if t["status"] == "DONE"]
    if done:
        print("\n已完成:")
        for t in done:
            print(f"  ✓ {t['id']:>6} {t['rule']}")
    todo = [t for t in tasks if t["status"] in ("BACKLOG", "IN_PROGRESS")]
    if todo:
        print("\n待推进:")
        for t in todo:
            print(f"  → {t['id']:>6} [{t['status']}] owner={t['owner']:>14} {t['rule']}")


def cmd_handoff(args) -> None:
    root = Path(args.dir)
    bb = root / "TASKS.md"
    tasks = parse_tasks(bb)
    today = date.today().isoformat()
    out = root / "artifacts" / "handoff" / f"{today}_handoff.md"
    lines = [
        "# Handoff",
        "",
        f"生成时间：{datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## 已完成",
        "",
    ]
    done = [t for t in tasks if t["status"] == "DONE"]
    lines += [f"- {t['id']} {t['rule']}" for t in done] or ["- 无"]
    lines += ["", "## 进行中 / 阻塞", ""]
    active = [t for t in tasks if t["status"] in ("IN_PROGRESS", "BLOCKED", "REVIEW")]
    lines += [
        f"- {t['id']} [{t['status']}] owner={t['owner']} 阻塞={t['blockers']} 规则={t['rule']}"
        for t in active
    ] or ["- 无"]
    lines += ["", "## 下一步", ""]
    backlog = [t for t in tasks if t["status"] == "BACKLOG"]
    lines += [f"- 派发 {t['id']} → {t['owner']}" for t in backlog] or ["- 无"]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已生成: {out}")


def cmd_set(args) -> None:
    bb = Path(args.dir) / "TASKS.md"
    status = args.status.upper()
    if status not in STATES:
        sys.exit(f"无效状态: {status}（可用: {', '.join(STATES)}）")
    if not bb.exists():
        sys.exit("未找到 TASKS.md，先运行 caw init")
    lines = bb.read_text(encoding="utf-8").splitlines()
    new_lines, changed = [], False
    for line in lines:
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 5 and cells[0].strip("` ").strip() == args.task:
                cells[2] = status
                new_lines.append("| " + " | ".join(cells) + " |")
                changed = True
                continue
        new_lines.append(line)
    if not changed:
        sys.exit(f"未找到任务: {args.task}")
    bb.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"已更新: {args.task} → {status}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="caw",
        description="Claude Agent Workflows CLI — 指挥官—多执行者协作协议落地工具",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="生成 TASKS.md + artifacts/ 骨架")
    p_init.add_argument("--dir", default=".", help="项目目录（默认当前目录）")
    p_init.set_defaults(func=cmd_init)

    p_new = sub.add_parser("new-task", help="创建任务规则并登记到 TASKS.md")
    p_new.add_argument("title", help="任务标题")
    p_new.add_argument("--owner", choices=OWNERS, default="codex", help="执行者")
    p_new.add_argument("--id", help="任务 ID（默认自动编号）")
    p_new.add_argument("--dep", help="阻塞源任务 ID")
    p_new.add_argument("--force", action="store_true", help="覆盖已存在的规则")
    p_new.add_argument("--dir", default=".", help="项目目录")
    p_new.set_defaults(func=cmd_new_task)

    p_disp = sub.add_parser("dispatch", help="按执行者打印派发命令")
    p_disp.add_argument("task", help="任务 ID")
    p_disp.add_argument("--run", action="store_true", help="打印后直接执行")
    p_disp.add_argument("--dir", default=".", help="项目目录")
    p_disp.set_defaults(func=cmd_dispatch)

    p_st = sub.add_parser("status", help="汇总 TASKS.md 任务状态")
    p_st.add_argument("--dir", default=".", help="项目目录")
    p_st.set_defaults(func=cmd_status)

    p_ho = sub.add_parser("handoff", help="生成跨会话交接文档")
    p_ho.add_argument("--dir", default=".", help="项目目录")
    p_ho.set_defaults(func=cmd_handoff)

    p_set = sub.add_parser("set", help="更新任务状态")
    p_set.add_argument("task", help="任务 ID")
    p_set.add_argument("status", help=f"新状态（{', '.join(STATES)}，大小写均可）")
    p_set.add_argument("--dir", default=".", help="项目目录")
    p_set.set_defaults(func=cmd_set)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

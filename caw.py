#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""caw — Claude Agent Workflows CLI.

把 commander-executor 的「指挥官—多执行者」协作协议落地为命令行工具。
仅依赖 Python 标准库，无第三方依赖。

子命令：
  init                生成 TASKS.md + artifacts/ 骨架
  new-task <标题>     创建任务规则并登记到 TASKS.md
  dispatch <任务ID>   按执行者打印派发命令（--run 直接执行）
  show <任务ID>       查看任务规则内容
  status              汇总 TASKS.md 任务状态
  set <任务ID> <状态>  更新任务状态（BACKLOG/IN_PROGRESS/BLOCKED/REVIEW/DONE）
  review <任务ID>     标记任务进入审查（REVIEW）
  verify <任务ID>     验证并完成（DONE + 记录证据）
  done <任务ID>       快捷完成（DONE）
  handoff             生成跨会话交接文档
  install             把仓库 skills 装进本地（默认跳过已存在）
  sync                把仓库 skills 同步到本地（默认跳过 resume-generator）
"""

import argparse
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

STATES = ("BACKLOG", "IN_PROGRESS", "BLOCKED", "REVIEW", "DONE")
OWNERS = ("zcode", "codex", "codex-deepseek", "claude-subagent")
# sync 默认保护的 skill：本地含真实私有数据（真实路径/真实经历），仓库是脱敏模板，不能被覆盖
PROTECTED_SKILLS = ("resume-generator", "gaodun-essay-grader", "workflow-to-skill")

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


def _set_status(dir_str: str, task_id: str, status: str) -> None:
    bb = Path(dir_str) / "TASKS.md"
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
            if len(cells) >= 5 and cells[0].strip("` ").strip() == task_id:
                cells[2] = status
                new_lines.append("| " + " | ".join(cells) + " |")
                changed = True
                continue
        new_lines.append(line)
    if not changed:
        sys.exit(f"未找到任务: {task_id}")
    bb.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"已更新: {task_id} → {status}")


def cmd_set(args) -> None:
    _set_status(args.dir, args.task, args.status.upper())


def cmd_review(args) -> None:
    _set_status(args.dir, args.task, "REVIEW")
    if args.report:
        bb = Path(args.dir) / "TASKS.md"
        tasks = parse_tasks(bb)
        t = next((x for x in tasks if x["id"] == args.task), None)
        rdir = Path(args.dir) / "artifacts" / "review"
        rdir.mkdir(parents=True, exist_ok=True)
        rpath = rdir / f"{date.today().isoformat()}_{args.task}.md"
        rpath.write_text(
            f"# 审查报告｜{args.task}\n\n- 日期：{date.today().isoformat()}\n- 任务：`{t['rule']}`\n\n{args.report}\n",
            encoding="utf-8",
        )
        print(f"报告已存: {rpath}")


def cmd_done(args) -> None:
    _set_status(args.dir, args.task, "DONE")


def cmd_verify(args) -> None:
    _set_status(args.dir, args.task, "DONE")
    if args.evidence:
        bb = Path(args.dir) / "TASKS.md"
        tasks = parse_tasks(bb)
        t = next((x for x in tasks if x["id"] == args.task), None)
        rpath = Path(args.dir) / t["rule"].strip("`")
        rpath.write_text(
            rpath.read_text(encoding="utf-8")
            + f"\n## 验证证据（{date.today().isoformat()}）\n\n{args.evidence}\n",
            encoding="utf-8",
        )
        print(f"证据已记录到: {rpath}")


def cmd_show(args) -> None:
    bb = Path(args.dir) / "TASKS.md"
    tasks = parse_tasks(bb)
    t = next((x for x in tasks if x["id"] == args.task), None)
    if not t:
        sys.exit(f"未找到任务: {args.task}")
    rpath = Path(args.dir) / t["rule"].strip("`")
    if not rpath.exists():
        sys.exit(f"规则文件不存在: {rpath}")
    print(f"# {t['id']} [{t['status']}] owner={t['owner']} 阻塞={t['blockers']}")
    print("-" * 44)
    print(rpath.read_text(encoding="utf-8"), end="")


def _skill_names() -> list:
    skills_dir = HERE / "skills"
    return sorted(d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists())


def _copy_skill(name: str, target: Path, mode: str) -> None:
    src = HERE / "skills" / name
    dst = target / name
    if dst.is_symlink() or dst.exists():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink(missing_ok=True)
    if mode == "link":
        dst.symlink_to(src, target_is_directory=True)
        print(f"  链接: {dst}")
    else:
        shutil.copytree(src, dst)
        print(f"  已装: {dst}")


def cmd_install(args) -> None:
    target = Path(args.target).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    skills = args.skills or _skill_names()
    for name in skills:
        if name not in _skill_names():
            sys.exit(f"仓库无此 skill: {name}")
        dst = target / name
        if (dst.exists() or dst.is_symlink()) and not args.force:
            print(f"  跳过(已存在): {name}（用 --force 覆盖）")
            continue
        _copy_skill(name, target, args.mode)
    print(f"完成。目标: {target}")


def cmd_sync(args) -> None:
    target = Path(args.target).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    if args.skills:
        skills = args.skills
    else:
        skills = [n for n in _skill_names() if n not in PROTECTED_SKILLS]
        print(f"（默认跳过受保护: {', '.join(PROTECTED_SKILLS)}，如需覆盖请显式指定 skill 名）")
    for name in skills:
        if name not in _skill_names():
            sys.exit(f"仓库无此 skill: {name}")
        _copy_skill(name, target, args.mode)
    print(f"完成。目标: {target}")


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

    p_show = sub.add_parser("show", help="查看任务规则内容")
    p_show.add_argument("task", help="任务 ID")
    p_show.add_argument("--dir", default=".", help="项目目录")
    p_show.set_defaults(func=cmd_show)

    p_review = sub.add_parser("review", help="标记任务进入审查（REVIEW）")
    p_review.add_argument("task", help="任务 ID")
    p_review.add_argument("--report", help="审查报告文本（存到 artifacts/review/）")
    p_review.add_argument("--dir", default=".", help="项目目录")
    p_review.set_defaults(func=cmd_review)

    p_verify = sub.add_parser("verify", help="验证并完成（DONE + 记录证据）")
    p_verify.add_argument("task", help="任务 ID")
    p_verify.add_argument("--evidence", help="验证证据文本")
    p_verify.add_argument("--dir", default=".", help="项目目录")
    p_verify.set_defaults(func=cmd_verify)

    p_done = sub.add_parser("done", help="快捷完成（DONE）")
    p_done.add_argument("task", help="任务 ID")
    p_done.add_argument("--dir", default=".", help="项目目录")
    p_done.set_defaults(func=cmd_done)

    p_install = sub.add_parser("install", help="把仓库 skills 装进本地（默认跳过已存在）")
    p_install.add_argument("skills", nargs="*", help="skill 名（默认全部）")
    p_install.add_argument("--target", default="~/.claude/skills", help="目标目录")
    p_install.add_argument("--mode", choices=("copy", "link"), default="copy", help="copy=复制 / link=软链接")
    p_install.add_argument("--force", action="store_true", help="覆盖已存在")
    p_install.set_defaults(func=cmd_install)

    p_sync = sub.add_parser("sync", help="把仓库 skills 同步到本地（默认跳过 resume-generator）")
    p_sync.add_argument("skills", nargs="*", help="skill 名（默认除 resume-generator 外全部）")
    p_sync.add_argument("--target", default="~/.claude/skills", help="目标目录")
    p_sync.add_argument("--mode", choices=("copy", "link"), default="copy", help="copy=复制 / link=软链接")
    p_sync.set_defaults(func=cmd_sync)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

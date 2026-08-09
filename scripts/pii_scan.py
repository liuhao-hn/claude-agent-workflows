#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/pii_scan.py — 扫描仓库是否混入 PII/敏感信息。

用法：python scripts/pii_scan.py
命中任意敏感模式即退出码 1（供 CI 与提交前自检使用）。
"""

import re
import sys
from pathlib import Path

PATTERNS = {
    "手机号": r"1[3-9][0-9]{9}",
    "API Key": r"sk-(?![Xx]{24,})[A-Za-z0-9]{24,}",
    "绝对路径": r"/Users/[A-Za-z0-9_-]+/",
    "邮箱": r"[A-Za-z0-9._%+-]+@(?!example\.com\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
}
EXCLUDE_DIRS = {".git", "node_modules"}
EXTS = {".md", ".py", ".tex", ".tpl", ".html", ".sh", ".yml", ".yaml", ".json", ".toml"}


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    hits = []
    for p in root.rglob("*"):
        if not p.is_file() or any(x in EXCLUDE_DIRS for x in p.parts):
            continue
        if p.suffix not in EXTS:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for name, pat in PATTERNS.items():
                if re.search(pat, line):
                    hits.append(f"  {p.relative_to(root)}:{i}: {name}: {line.strip()[:50]}")
    if hits:
        print("⚠️ 检测到疑似 PII/敏感信息，请检查后重新提交：")
        print("\n".join(hits))
        return 1
    print("✓ PII 扫描通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())

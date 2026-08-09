#!/usr/bin/env bash
# commander-executor 端到端 demo：用 caw 跑通
#   init → new-task → dispatch → status → handoff
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "================ caw init ================"
python3 "$ROOT/caw.py" init --dir "$TMP"

echo
echo "============== new-task ×3 =============="
python3 "$ROOT/caw.py" new-task "全量数据刷新Job超时修复" --owner zcode --dir "$TMP"
python3 "$ROOT/caw.py" new-task "修复登录态丢失bug" --owner codex --dep 001 --dir "$TMP"
python3 "$ROOT/caw.py" new-task "性能基线调研" --owner claude-subagent --dir "$TMP"

echo
echo "============= dispatch 派发 ============="
python3 "$ROOT/caw.py" dispatch 001 --dir "$TMP"
python3 "$ROOT/caw.py" dispatch 002 --dir "$TMP"
python3 "$ROOT/caw.py" dispatch 003 --dir "$TMP"

echo
echo "=============== status ================="
python3 "$ROOT/caw.py" status --dir "$TMP"

echo
echo "=============== handoff ================"
python3 "$ROOT/caw.py" handoff --dir "$TMP"

echo
echo "============ 生成的骨架 ================"
find "$TMP" -type f | sort

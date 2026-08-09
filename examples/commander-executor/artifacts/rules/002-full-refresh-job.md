# 任务：002 全量数据刷新 Job 超时修复

## 目标

修复 nightly 全量刷新 Job 在数据量超过 500 万行时超时（>30min）的问题。验收后 Job 在 15 分钟内完成且无数据丢失。

## 范围（in-scope）

- `scripts/refresh_job.py`
- `tests/test_refresh_job.py`

## 排除（out-of-scope）

- 不改 `scripts/sync_schema.py`（归属另一个任务）
- 不引入新的第三方依赖（除非在约束中说明并被批准）

## 约束

- Python 3.11，只允许标准库 + 已安装的 pandas / psycopg2
- 保持对外接口 `main()` 签名不变
- 批量提交（batch commit），不逐行 commit

## 验收标准

- [ ] `python scripts/refresh_job.py --dry-run` 在 500 万行模拟数据上 < 15min
- [ ] `pytest tests/test_refresh_job.py` 全绿
- [ ] 失败回滚逻辑有单测覆盖

## 输出证据

- 报告：跑过的命令、耗时、测试输出
- 产物：改动文件 diff、测试报告

# Qinglong-UV 开发指南

## 项目入口

- Python 3.15 依赖由 `uv` 管理，入口为 `qinglong/__main__.py`。`qinglong/web.py` 提供 FastAPI `/api` 接口并托管前端，`qinglong/api.py` 实现项目和任务操作。
- Vue 3 / Vite 前端在 `frontend/src/`。接口变更时同步检查 `frontend/src/api.js` 和使用该接口的页面。前端构建产物在 `qinglong/web_dist/`，由 Docker 构建生成。
- `qinglong/scheduler.py` 处理定时触发和并发上限，`qinglong/uvtask.py` 执行 `uv run` 并管理子进程和日志。

## 部署与调度约定

- 生产环境使用 Docker Compose 和单个 Uvicorn worker。升级面板代码时重建容器，使用 `./data:/code/data` 保留项目、任务配置和日志。
- Docker 构建使用 Node.js 和 LinuxServer FFmpeg 的 `latest` 镜像。Compose 每次构建都会检查这两个标签是否有更新。直接用 `docker build` 时加 `--pull`。
- 面板 Python 由容器启动时的 uv 管理，只固定 `3.15` 小版本系列。容器启动先更新 uv 的发行版，再升级共享目录中 uv 管理的 CPython 补丁版本，并执行 `uv cache prune --force`。生产数据目录由单个面板容器使用。
- 项目首次运行时按目录清空并重建旧 `.venv`，随后用 `uv run` 同步依赖。同一服务进程中，同一项目的任务共用这次重建；保留磁盘上的 uv 缓存。
- 保留进程内 APScheduler 3.x 调度器。启动时从 SQLite 恢复任务配置和暂停状态。正在运行的任务随旧容器结束，停机期间错过的触发允许跳过。
- 保持已有五段 Cron 和正整数秒间隔的行为。暂停只影响定时触发，手动 `Run` 仍可用。两种触发共用同一任务的并发上限，手动运行不改变下一次定时时间。
- `runs.sqlite` 保存最近的运行结果及日志尾部。运行结果区分超时、手动停止、服务中断和计划触发被跳过。超时是任务可选项，涵盖环境准备和命令执行。Webhook 由独立线程投递。

## 本地开发和验证

- 实现改动若改变入口、部署方式、版本约束或调度行为，在同一次改动中主动更新本指南及受影响的 README 段落。

- 后端依赖用 `uv sync --locked` 安装，开发服务用 `uv run main.py` 启动，监听 `127.0.0.1:8080`。
- 本地前端开发使用 Node.js 24 LTS。安装用 `npm --prefix frontend ci`，开发用 `npm --prefix frontend run dev`，验证打包用 `npm --prefix frontend run build`。Vite 开发服务器将 `/api` 转发给本地后端。
- 按改动范围选择 `tests/` 下的 pytest 测试。`tests/test_api.py` 会清空配置指向的项目和任务数据库，运行测试前将 `DB_PATH`、`PROJECT_PATH`、`TASK_LOG_PATH` 指向临时目录。

```sh
test_data=$(mktemp -d)
DB_PATH="$test_data/db" PROJECT_PATH="$test_data/projects" TASK_LOG_PATH="$test_data/log" \
  uv run pytest tests/test_scheduler.py -m 'not slow'
```

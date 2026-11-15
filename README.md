# Qinglong-UV

A lightweight Vue + FastAPI task panel for **scheduled execution of Python projects with uv**.
基于 Vue + FastAPI 的轻量任务面板，使用 uv 定时运行 Python 项目。

Core idea: clone Git projects locally, initialize and run tasks with `uv`, and manage projects, tasks, and logs in a Web UI.
核心思路：把 Git 项目拉到本地后，用 `uv` 初始化并执行任务，通过 Web 页面统一管理项目、任务和日志。

## 功能概览 | Features

### 项目管理 | Project Management
- 通过 Git URL 克隆项目（已存在时执行 pull） | Clone projects from Git URLs (pull if already exists)
- 在页面中手动更新项目 | Manually update projects in UI
- 可视化查看项目列表和更新时间 | View project list and update timestamps
- 在线编辑项目根目录的 `config.*`（支持 `toml` / `yaml` 校验） | Edit root `config.*` in UI (with `toml` / `yaml` validation)

### 任务管理 | Task Management
- 为项目创建定时任务（支持 crontab） | Create scheduled tasks per project (crontab supported)
- 也支持用纯数字秒数作为间隔触发（例如 `60`） | Also supports pure integer seconds as interval triggers (e.g. `60`)
- 可暂停或恢复调度、立即运行、停止进程、删除任务和同步任务注册表 | Pause or resume schedules, run immediately, stop processes, delete tasks, and sync the task registry
- 任务详情分别显示调度状态、进程状态和下次运行时间，日志面板打开时每 2 秒刷新 | Task details show schedule state, process state, and next run time. The visible log pane refreshes every 2 seconds

### 运行机制 | Runtime Behavior
- 任务实际执行命令格式：`uv run <你的命令>` | Actual execution format: `uv run <your command>`
- 由 `uv run` 按项目配置和锁文件准备运行环境 | `uv run` prepares the environment using the project's configuration and lockfile
- 每次运行记录退出码。在 Linux 和 macOS 上，超时和手动停止会终止任务进程组。 | Each run records its exit code. On Linux and macOS, a timeout or manual stop terminates the task's process group.

## 环境要求 | Requirements

- `uv`（必需） | `uv` (required)
- `git`（克隆/更新项目必需） | `git` (required for clone/pull)
- Node.js 24 LTS 和 npm（本地前端构建和开发） | Node.js 24 LTS and npm (local frontend builds and development)
- 操作系统可正常运行 `uv` 与 Python 子进程 | OS environment capable of running `uv` and Python subprocesses

> 面板使用 Python 3.15.2（见 `.python-version`）。各任务项目可声明自己的 Python 版本。 | The panel uses Python 3.15.2 (see `.python-version`). Each task project can declare its own Python version.

## 快速开始 | Quick Start

### 1) 安装依赖并构建页面 | Install dependencies and build the UI

```bash
uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
```

### 2) 启动服务 | Start Service

生产方式（默认） | Production mode (default):

```bash
uv run -m qinglong
```

- 浏览器访问 `http://localhost`，API 文档位于 `/api/docs` | Open `http://localhost`. API docs are at `/api/docs`
- FastAPI 启动和手动同步时从 SQLite 恢复调度及暂停状态，部署使用单个 worker | Startup and manual sync restore schedules and paused state from SQLite. Deploy with a single worker
- 任务通过 `uv run` 按需同步依赖并执行，超时覆盖整个过程 | `uv run` syncs dependencies as needed and runs the command within the task timeout

开发时在两个终端分别运行 | For development, run in separate terminals:

```bash
uv run main.py
npm --prefix frontend run dev
```

- 打开 Vite 输出的地址。它会把 `/api` 转发到 `127.0.0.1:8080` | Open the URL printed by Vite. It proxies `/api` to `127.0.0.1:8080`

### 3) 使用 Web 界面 | Use the Web UI

1. 点击侧栏 `Projects` 旁的 `+` 克隆 Git 项目。选中项目后可拉取更新或通过工具栏菜单编辑配置。 | Use `+` beside `Projects` to clone a Git project. Select a project to pull updates or edit its configuration from the toolbar menu.
2. 点击 `New Task`，填写全局唯一的任务名、五字段 cron 表达式或正整数秒数、执行命令和超时。 | Use `New Task` to enter a globally unique name, five-field cron expression or positive interval in seconds, command, and timeout.
3. 选择任务后用 `Run Now` 立即运行，在 `Logs` 查看输出。暂停调度后仍可手动运行一次。 | Select a task, click `Run Now`, and view its output in `Logs`. Paused schedules still allow a manual run.

## Docker 部署 | Docker Deployment

项目内置了 `dockerfile` 与 `docker-compose.yaml`。
This repository includes `dockerfile` and `docker-compose.yaml`.

```bash
docker compose up -d --build
```

- 默认容器内部端口为 `80` | Default container port: `80`
- `docker-compose.override.yaml` 示例将本机 `8080` 映射到容器 `80` | Example override maps host `8080` -> container `80`
- 镜像构建时打包 Vue 页面，由 FastAPI 提供，运行时共用一个端口。 | The Docker build bundles Vue and FastAPI serves it on the same port as the API.
- 数据目录挂载：`./data:/code/data`，原有数据可直接使用。 | Data volume: `./data:/code/data`. Existing data can be used directly.

## 配置说明 | Configuration

配置位于 `qinglong/config.py`（基于 `pydantic-settings`，可通过同名环境变量覆盖）。
Configuration is defined in `qinglong/config.py` (based on `pydantic-settings`, overridable by environment variables with the same names).

- `PROXY`：代理地址（默认空） | Proxy URL (default empty)
- `DB_PATH`：项目/任务元数据存储目录（默认 `./data/db`） | Metadata storage dir for projects/tasks (default `./data/db`)
- `PROJECT_PATH`：Git 项目保存目录（默认 `./data/projects`） | Git project directory (default `./data/projects`)
- `TASK_LOG_PATH`：任务日志目录（默认 `./data/log`） | Task log directory (default `./data/log`)
- `TASK_LOG_MAX_BYTES`：单日志最大大小（默认 `1MB`） | Max size per log file (default `1MB`)
- `TASK_LOG_BACKUP_COUNT`：日志备份数量（默认 `5`） | Number of rotated backups (default `5`)
- `DEBUG`：调试开关（默认 `True`） | Debug flag (default `True`)

## 目录结构（核心）| Core Structure

```text
qinglong/
  api.py         # 项目与任务核心逻辑 | Core project/task logic
  scheduler.py   # APScheduler 封装 | APScheduler wrapper
  uvtask.py      # uv 任务执行与进程控制 | uv task execution and process control
  web.py         # FastAPI 接口与静态页面 | FastAPI endpoints and static frontend
  config.py      # 配置项 | Settings
frontend/        # Vue 页面 | Vue frontend
data/
  db/            # 本地数据库文件 | Local DB files
  projects/      # 克隆下来的项目 | Cloned projects
  log/           # 任务日志 | Task logs
```

## 已知限制 | Known Limitations

- 当前只面向 Python/uv 工作流，不支持其他运行时 | Currently focused on Python/uv workflows only
- 删除项目之前须先删除关联任务 | Delete a project's tasks before removing the project
- 任务命令会被拼接为 `uv run ...`，复杂 shell 语法建议封装成脚本再调用 | Commands are wrapped as `uv run ...`; put complex shell logic into scripts

## Roadmap

- [ ] 运行历史：记录触发来源、起止时间、结果和对应日志。 | Run history with trigger source, start and end times, outcome, and per-run logs.
- [ ] 失败通知：按任务订阅失败和超时，支持重复失败时合并通知。 | Per-task failure and timeout alerts with deduplication.
- [ ] 调度预览：保存前展示时区和接下来几次触发时间。 | Schedule preview with the time zone and next few fire times before saving.

## 贡献 | Contributing

欢迎提交 Issue 和 Pull Request。
Issues and Pull Requests are welcome.

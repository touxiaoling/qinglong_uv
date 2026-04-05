# Qinglong-UV

A lightweight task panel built with `uv` + `NiceGUI`, similar in spirit to Qinglong and currently focused on **scheduled execution for Python projects**.
一个基于 `uv` + `NiceGUI` 的轻量任务面板，定位类似青龙，当前专注于 **Python 项目定时执行**。

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
- 支持 `Start` / `Pause` / `Run` / `Kill` / `Remove` / `Sync` | Supports `Start` / `Pause` / `Run` / `Kill` / `Remove` / `Sync`
- 支持实时查看任务日志（页面每 2 秒刷新） | Real-time task logs (refresh every 2 seconds in UI)

### 运行机制 | Runtime Behavior
- 启动时会执行 | On startup:
  - `uv python upgrade`
  - `uv cache prune --force`
- 任务首次运行某项目时会执行（每个项目仅一次） | On first task run per project (once per project):
  - `uv venv --clear`
  - `uv sync`
- 任务实际执行命令格式：`uv run <你的命令>` | Actual execution format: `uv run <your command>`

## 环境要求 | Requirements

- `uv`（必需） | `uv` (required)
- `git`（克隆/更新项目必需） | `git` (required for clone/pull)
- 操作系统可正常运行 `uv` 与 Python 子进程 | OS environment capable of running `uv` and Python subprocesses

> 项目当前声明的 Python 版本为 `3.14`（见 `pyproject.toml` 的 `requires-python = "==3.14.*"`）。
> Current declared Python version is `3.14` (see `pyproject.toml`: `requires-python = "==3.14.*"`).

## 快速开始 | Quick Start

### 1) 安装依赖 | Install Dependencies

```bash
git clone <your-repo-url>
cd qinglong-uv
uv sync
```

### 2) 启动服务 | Start Service

生产方式（默认） | Production mode (default):

```bash
uv run -m qinglong
```

- 默认监听：`0.0.0.0:80` | Default bind: `0.0.0.0:80`

开发调试方式（热重载） | Development mode (hot reload):

```bash
uv run main.py
```

- 默认监听：`localhost:8080` | Default bind: `localhost:8080`

### 3) 使用 Web 界面 | Use the Web UI

1. 在 `Project` 区域点击 `Clone`，填写项目名和 Git URL | Click `Clone` in `Project`, then input project name and Git URL
2. 在 `Task` 区域点击 `Set`，填写 | Click `Set` in `Task`, then fill:
   - `Name`：任务名（全局唯一） | Task name (globally unique)
   - `Cron`：crontab 表达式，或秒级整数 | Crontab expression or integer seconds
   - `Command`：执行命令（如 `main.py`、`python app.py`） | Command to run (e.g. `main.py`, `python app.py`)
3. 在任务列表中使用 `Start/Pause/Run/Kill/Logs` 管理和观察任务 | Use `Start/Pause/Run/Kill/Logs` in task table to manage and monitor tasks

## Docker 部署 | Docker Deployment

项目内置了 `dockerfile` 与 `docker-compose.yaml`。
This repository includes `dockerfile` and `docker-compose.yaml`.

```bash
docker compose up -d --build
```

- 默认容器内部端口为 `80` | Default container port: `80`
- `docker-compose.override.yaml` 示例将本机 `8080` 映射到容器 `80` | Example override maps host `8080` -> container `80`
- 数据目录挂载：`./data:/code/data` | Data volume: `./data:/code/data`

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
  ui.py          # NiceGUI 页面 | NiceGUI interface
  config.py      # 配置项 | Settings
data/
  db/            # 本地数据库文件 | Local DB files
  projects/      # 克隆下来的项目 | Cloned projects
  log/           # 任务日志 | Task logs
```

## 已知限制 | Known Limitations

- 当前只面向 Python/uv 工作流，不支持其他运行时 | Currently focused on Python/uv workflows only
- 删除项目时不会自动联动删除关联任务，请先处理任务再删项目 | Removing a project does not automatically remove related tasks
- 任务命令会被拼接为 `uv run ...`，复杂 shell 语法建议封装成脚本再调用 | Commands are wrapped as `uv run ...`; put complex shell logic into scripts

## Roadmap

- [ ] Git 项目自动更新（定时 / webhook） | Auto-update Git projects (scheduled / webhook)
- [ ] 通知系统集成（可考虑 [apprise](https://github.com/caronc/apprise)） | Notification integration (consider [apprise](https://github.com/caronc/apprise))
- [ ] 多项目联动与级联触发 | Cross-project linkage and cascading triggers
- [ ] 统一通知 SDK | Unified notification SDK

## 贡献 | Contributing

欢迎提交 Issue 和 Pull Request。
Issues and Pull Requests are welcome.

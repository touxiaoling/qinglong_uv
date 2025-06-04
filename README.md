# Qinglong-UV

一个使用uv管理Python版本和包的类qinglong定时运行面板，目前仅支持运行Python代码。

A Qinglong-like panel for managing Python tasks using uv package manager, currently supporting Python code execution only.

## 主要功能 | Main Features

### 项目管理 | Project Management
- 从URL下载Git项目 | Download Git projects from URLs
- 支持手动更新Git项目 | Support manual Git project updates
- 支持通过Web界面管理项目配置（`config.*`文件）| Manage project configurations via Web UI (`config.*` files)
- 支持查看和管理项目列表 | View and manage project list

### 任务管理 | Task Management
- 支持使用cron表达式定时运行文件或Git项目 | Schedule tasks using cron expressions for files or Git projects
- 支持长时间任务守护运行 | Support long-running task daemon
- 支持任务的启动、暂停、立即运行等操作 | Support task operations: start, pause, run now
- 支持查看任务运行日志 | View task execution logs
- 支持通过Web界面配置任务 | Configure tasks via Web UI

### Web界面 | Web Interface
- 使用NiceGUI实现的现代化Web界面 | Modern Web UI implemented with NiceGUI
- 支持项目管理和任务管理的可视化操作 | Visual operations for project and task management
- 支持实时查看任务状态和日志 | Real-time task status and log viewing

## 系统要求 | System Requirements
- Python 3.8+
- uv包管理器 | uv package manager
- Git

## 安装 | Installation

1. 安装uv | Install uv:
   - 访问 [uv安装文档](https://docs.astral.sh/uv/getting-started/installation/) 获取安装说明
   - Visit [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for installation instructions

2. 克隆项目 | Clone the project:
```bash
git clone https://github.com/yourusername/qinglong-uv.git
cd qinglong-uv
```

3. 使用uv安装依赖 | Install dependencies using uv:
```bash
uv sync
```

## 使用说明 | Usage

1. 启动服务 | Start the service:
```bash
uv run qinglong
```

2. 访问Web界面 | Access Web UI:
- 默认地址 | Default address: http://localhost:80

3. 添加项目 | Add project:
- 在Web界面输入项目名称和Git URL | Enter project name and Git URL in Web UI
- 点击"Clone"按钮下载项目 | Click "Clone" button to download project

4. 配置任务 | Configure task:
- 选择项目 | Select project
- 输入任务名称 | Enter task name
- 设置cron表达式 | Set cron expression
- 配置运行命令 | Configure run command
- 点击"Set"保存任务 | Click "Set" to save task

## 配置说明 | Configuration

系统配置文件位于`config.py`，主要配置项包括：
System configuration file is located at `config.py`, main configuration items include:

- `PROXY`: 代理设置 | Proxy settings
- `DB_PATH`: 数据库路径 | Database path
- `PROJECT_PATH`: 项目存储路径 | Project storage path
- `TASK_LOG_PATH`: 任务日志路径 | Task log path
- `TASK_LOG_MAX_BYTES`: 单个日志文件最大大小 | Maximum size of single log file
- `TASK_LOG_BACKUP_COUNT`: 日志备份数量 | Number of log backups

## 待开发功能 | Planned Features

- [ ] 自动更新Git项目（定时更新，支持webhook更新）| Auto-update Git projects (scheduled updates, webhook support)
- [ ] 支持API自动重定向 | Support API auto-redirect
- [ ] 通知系统集成 | Notification system integration
- [ ] 多项目间互相调用 | Inter-project calls
- [ ] 级联触发器支持 | Cascading trigger support
- [ ] 统一通知SDK | Unified notification SDK

## 问题与建议 | Issues and Suggestions

- 通知系统建议使用[apprise](https://github.com/caronc/apprise)库 | Notification system recommended to use [apprise](https://github.com/caronc/apprise) library
- 需要开发外部SDK用于 | Need to develop external SDK for:
  - 统一通知 | Unified notifications
  - 多项目级联触发 | Multi-project cascading triggers
  - 参数传递 | Parameter passing

## 贡献 | Contributing

欢迎提交Issue和Pull Request！
Issues and Pull Requests are welcome!

## 许可证 | License

[待定 | To be determined]

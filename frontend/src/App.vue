<script setup>
import { computed, defineAsyncComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Activity, ArrowDownToLine, Check, ChevronDown, ChevronRight, CircleAlert,
  Ellipsis, FileCode2, FolderGit2, Info, Layers3, PanelLeft, Pause, Pencil, Play, Plus,
  RefreshCw, Search, Square, Terminal, Trash2, X,
} from '@lucide/vue'
import { projectPath, request, taskPath } from './api.js'

const ConfigEditor = defineAsyncComponent(() => import('./ConfigEditor.vue'))
const projects = ref([])
const tasks = ref([])
const selectedProjectName = ref(null)
const selectedTaskName = ref(null)
const search = ref('')
const loading = ref(true)
const projectError = ref('')
const taskError = ref('')
const connectionError = computed(() => projectError.value || taskError.value)
const notice = ref('')
const actionError = ref('')
const busy = ref(false)
const sidebarOpen = ref(false)
const menu = ref('')
const dialog = ref(null)
const dialogElement = ref()
const searchInput = ref()
const taskTable = ref()
const logsElement = ref()
const lines = ref([])
const logError = ref('')
const logsLoading = ref(false)
const following = ref(true)
const tab = ref('logs')
const history = ref([])
const historyError = ref('')
const historyLoading = ref(false)
const selectedRunId = ref(null)
const selectedRun = ref(null)
const runError = ref('')
const revision = ref(null)
const revisionError = ref('')
const form = ref({})
const formError = ref('')
let projectRefresh = 0
let taskRefresh = 0
let logRefresh = 0
let historyRefresh = 0
let runRefresh = 0
let revisionRefresh = 0
let noticeTimer
let pollTimer

const project = computed(() => projects.value.find(({ name }) => name === selectedProjectName.value))
const scopedTasks = computed(() => tasks.value.filter((task) => (
  selectedProjectName.value === null || task.project_name === selectedProjectName.value
)))
const visibleTasks = computed(() => {
  const term = search.value.trim().toLowerCase()
  return scopedTasks.value.filter((task) => [task.name, task.project_name, task.command].some((value) => value.toLowerCase().includes(term)))
})
const task = computed(() => scopedTasks.value.find(({ name }) => name === selectedTaskName.value))
const runningCount = computed(() => tasks.value.filter(({ is_running }) => is_running).length)
const logText = computed(() => lines.value.join('\n'))
const groups = computed(() => projects.value.map((item) => ({
  ...item, count: tasks.value.filter((task) => task.project_name === item.name).length,
})))
const taskProjectExists = computed(() => projects.value.some(({ name }) => name === task.value?.project_name))
const dateTime = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'medium' })
const dayFormat = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' })
const timeFormat = new Intl.DateTimeFormat(undefined, { timeStyle: 'medium', hourCycle: 'h23' })
const resultLabels = {
  running: 'Running', succeeded: 'Succeeded', failed: 'Failed', timed_out: 'Timed out',
  stopped: 'Stopped', skipped: 'Skipped', interrupted: 'Interrupted',
}

function dateLabel(value) {
  return value ? dateTime.format(new Date(value.replace(' ', 'T'))) : '—'
}

function scheduleState(item) {
  if (!item.registered) return 'Unregistered'
  return item.status === 'paused' ? 'Paused' : 'Enabled'
}

async function loadProjects() {
  const revision = ++projectRefresh
  try {
    const data = await request('/projects')
    if (revision !== projectRefresh) return
    projects.value = data.sort((a, b) => a.name.localeCompare(b.name))
    if (selectedProjectName.value && !project.value) selectedProjectName.value = null
    projectError.value = ''
  } catch (error) {
    if (revision === projectRefresh) projectError.value = error.message
  }
}

async function loadTasks() {
  const revision = ++taskRefresh
  try {
    const data = await request('/tasks')
    if (revision !== taskRefresh) return
    tasks.value = data.sort((a, b) => a.name.localeCompare(b.name))
    if (!task.value) selectedTaskName.value = null
    taskError.value = ''
  } catch (error) {
    if (revision === taskRefresh) taskError.value = error.message
  }
}

async function loadWorkspace() {
  try {
    await Promise.all([loadProjects(), loadTasks()])
  } finally {
    loading.value = false
  }
}

function selectProject(name) {
  selectedProjectName.value = name
  search.value = ''
  selectedTaskName.value = null
  sidebarOpen.value = false
  menu.value = ''
}

function selectTask(name) {
  selectedTaskName.value = name
  selectedRunId.value = null
  tab.value = 'logs'
  menu.value = ''
}

async function closeTask() {
  const trigger = taskTable.value?.querySelector('button[aria-expanded="true"]')
  selectedTaskName.value = null
  menu.value = ''
  await nextTick()
  trigger?.focus({ preventScroll: true })
}

function refreshLogScope() {
  ++logRefresh
  lines.value = []
  logError.value = ''
  logsLoading.value = false
  following.value = true
  if (task.value?.registered && tab.value === 'logs') void loadLogs(true)
}

async function loadLogs(showLoading = false) {
  const current = task.value
  if (!current?.registered || tab.value !== 'logs' || document.hidden) return
  const revision = ++logRefresh
  if (showLoading) logsLoading.value = true
  try {
    const data = await request(taskPath(current.name) + '/logs')
    if (revision !== logRefresh) return
    lines.value = data
    logError.value = ''
    await nextTick()
    if (following.value) scrollToLatest()
  } catch (error) {
    if (revision === logRefresh) logError.value = error.message
  } finally {
    if (revision === logRefresh) logsLoading.value = false
  }
}

function scrollToLatest() {
  const element = logsElement.value
  if (element) element.scrollTop = element.scrollHeight
}

function trackScroll() {
  const element = logsElement.value
  if (element) following.value = element.scrollHeight - element.scrollTop - element.clientHeight < 12
}

function followLatest() {
  following.value = true
  scrollToLatest()
}

async function poll() {
  if (document.hidden) return
  await Promise.all([loadTasks(), loadLogs(), projectError.value ? loadProjects() : undefined])
}

async function loadHistory() {
  const current = task.value
  if (!current || tab.value !== 'history') return
  const requestId = ++historyRefresh
  historyLoading.value = true
  try {
    const data = await request(taskPath(current.name) + '/runs')
    if (requestId !== historyRefresh) return
    history.value = data
    historyError.value = ''
  } catch (error) {
    if (requestId === historyRefresh) historyError.value = error.message
  } finally {
    if (requestId === historyRefresh) historyLoading.value = false
  }
}

async function loadRun() {
  const current = task.value
  const id = selectedRunId.value
  const requestId = ++runRefresh
  selectedRun.value = null
  runError.value = ''
  if (!current || !id || tab.value !== 'history') return
  try {
    const data = await request(taskPath(current.name) + '/runs/' + id)
    if (requestId === runRefresh) selectedRun.value = data
  } catch (error) {
    if (requestId === runRefresh) runError.value = error.message
  }
}

async function openProjectDetails() {
  const current = project.value
  const requestId = ++revisionRefresh
  revision.value = null
  revisionError.value = ''
  await openDialog('project', { ...current })
  try {
    const data = await request(projectPath(current.name) + '/revision')
    if (requestId === revisionRefresh) revision.value = data
  } catch (error) {
    if (requestId === revisionRefresh) revisionError.value = error.message
  }
}

function showNotice(message) {
  clearTimeout(noticeTimer)
  notice.value = message
  noticeTimer = setTimeout(() => { notice.value = '' }, 3600)
}

async function act(callback, message, { reloadProjects = false, fromDialog = false } = {}) {
  if (busy.value) return
  busy.value = true
  actionError.value = ''
  formError.value = ''
  menu.value = ''
  try {
    await callback()
  } catch (error) {
    if (fromDialog) formError.value = error.message
    else actionError.value = error.message
    return
  } finally {
    busy.value = false
  }
  if (fromDialog) closeDialog()
  showNotice(message)
  if (reloadProjects) await loadWorkspace()
  else await loadTasks()
  await loadLogs()
}

function taskAction(action, message) {
  const name = task.value.name
  return act(() => request(taskPath(name) + '/' + action, { method: 'POST' }), message)
}

async function openDialog(kind, values = {}) {
  menu.value = ''
  form.value = values
  formError.value = ''
  dialog.value = kind
  await nextTick()
  if (!dialogElement.value.open) dialogElement.value.showModal()
}

function closeDialog() {
  if (busy.value) return
  dialogElement.value?.close()
  dialog.value = null
}

function newTask() {
  void openDialog('task', {
    name: '', project_name: project.value?.name ?? projects.value[0]?.name ?? '',
    cron: '', command: '', timeout: '', limitRuntime: false, notify_on_failure: false,
  })
}

function editTask() {
  void openDialog('task', { ...task.value, editing: true, limitRuntime: task.value.timeout > 0, timeout: task.value.timeout || '' })
}

async function openConfig() {
  const name = project.value.name
  await openDialog('config', { name, loading: true })
  try {
    const data = await request(projectPath(name) + '/config')
    if (dialog.value === 'config' && form.value.name === name) form.value = { name, ...data }
  } catch (error) {
    if (dialog.value === 'config' && form.value.name === name) {
      form.value.loading = false
      formError.value = error.message
    }
  }
}

function submitDialog() {
  const data = form.value
  const fromDialog = { fromDialog: true }
  if (dialog.value === 'clone') {
    const body = { url: data.url }
    if (data.name.trim()) body.name = data.name
    return act(() => request('/projects', { method: 'POST', body }), 'Project ready', { ...fromDialog, reloadProjects: true })
  }
  if (dialog.value === 'task') {
    const body = {
      cron: data.cron, command: data.command, timeout: data.limitRuntime ? data.timeout : 0,
      notify_on_failure: data.notify_on_failure,
    }
    if (!data.editing) Object.assign(body, { name: data.name, project_name: data.project_name })
    return act(async () => {
      const updated = await request(data.editing ? taskPath(data.name) : '/tasks', {
        method: data.editing ? 'PUT' : 'POST', body,
      })
      tasks.value = [...tasks.value.filter(({ name }) => name !== updated.name), updated]
      if (selectedProjectName.value !== null) selectProject(updated.project_name)
      selectTask(updated.name)
    }, data.editing ? 'Task updated' : 'Task added', fromDialog)
  }
  if (dialog.value === 'config') {
    return act(() => request(projectPath(data.name) + '/config', {
      method: 'PUT', body: { content: data.content },
    }), 'Configuration saved', fromDialog)
  }
  if (dialog.value === 'confirm') return act(data.callback, data.success, { ...fromDialog, reloadProjects: data.reloadProjects })
}

function confirmKill() {
  const name = task.value.name
  void openDialog('confirm', {
    title: 'Stop running task?', description: `The current run of ${name} will be terminated.`,
    label: 'Stop Task', success: 'Task stopped',
    callback: () => request(taskPath(name) + '/kill', { method: 'POST' }),
  })
}

function confirmTaskRemoval() {
  const name = task.value.name
  void openDialog('confirm', {
    title: 'Delete task?', description: `${name} will be removed from the panel and scheduler.`,
    label: 'Delete Task', success: 'Task deleted',
    callback: () => request(taskPath(name), { method: 'DELETE' }),
  })
}

function confirmProjectRemoval() {
  const name = project.value.name
  void openDialog('confirm', {
    title: 'Delete project?', description: `The local checkout for ${name} will be deleted.`,
    label: 'Delete Project', success: 'Project deleted', reloadProjects: true,
    callback: () => request(projectPath(name), { method: 'DELETE' }),
  })
}

function confirmSync() {
  void openDialog('confirm', {
    title: 'Sync task registry?', description: 'Sync registers saved tasks and removes scheduled jobs that have no saved task.',
    label: 'Sync Tasks', success: 'Task registry synced',
    callback: () => request('/sync', { method: 'POST' }),
  })
}

function toggleMenu(name) {
  menu.value = menu.value === name ? '' : name
}

function keyboard(event) {
  if (event.key === 'Escape') menu.value = ''
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k' && !dialog.value) {
    event.preventDefault()
    searchInput.value?.focus()
  }
}

watch([() => task.value?.name, () => task.value?.registered, tab], refreshLogScope)
watch([() => task.value?.name, tab], () => {
  ++historyRefresh
  history.value = []
  historyError.value = ''
  historyLoading.value = false
  void loadHistory()
})
watch([() => task.value?.latest_run?.id, () => task.value?.latest_run?.status, () => task.value?.is_running], () => {
  void loadHistory()
})
const selectedRunStatus = computed(() => history.value.find(({ id }) => id === selectedRunId.value)?.status)
watch([() => task.value?.name, tab, selectedRunId], loadRun)
watch(selectedRunStatus, (status, previous) => {
  if (previous === 'running' && status && status !== previous) void loadRun()
})

onMounted(() => {
  void loadWorkspace().then(() => {
    const params = new URLSearchParams(window.location.search)
    const name = params.get('task')
    const id = Number(params.get('run'))
    if (tasks.value.some(item => item.name === name) && Number.isSafeInteger(id) && id > 0) {
      selectTask(name)
      tab.value = 'history'
      selectedRunId.value = id
    }
  })
  pollTimer = setInterval(poll, 2000)
  window.addEventListener('keydown', keyboard)
  document.addEventListener('visibilitychange', poll)
})
onBeforeUnmount(() => {
  clearInterval(pollTimer)
  clearTimeout(noticeTimer)
  window.removeEventListener('keydown', keyboard)
  document.removeEventListener('visibilitychange', poll)
})
</script>

<template>
  <div class="workspace" @click="menu = ''">
    <button v-if="sidebarOpen" class="sidebar-scrim" aria-label="Close projects" @click="sidebarOpen = false"></button>
    <aside class="sidebar" :class="{ 'sidebar-open': sidebarOpen }" aria-label="Projects">
      <div class="brand">
        <div class="app-icon"><Terminal :size="23" :stroke-width="2.2" /></div>
        <div><strong>Qinglong UV</strong><span>Task scheduler</span></div>
      </div>

      <nav class="project-nav" aria-label="Project filter">
        <button class="nav-item" :class="{ selected: selectedProjectName === null }" :aria-pressed="selectedProjectName === null" @click="selectProject(null)">
          <Layers3 :size="17" /><span>All Tasks</span><small>{{ tasks.length }}</small>
        </button>
        <div class="nav-heading">
          <span>Projects</span>
          <button class="icon-button quiet" aria-label="Clone project" title="Clone project" :disabled="busy"
            @click="openDialog('clone', { url: '', name: '' })"><Plus :size="16" /></button>
        </div>
        <button v-for="item in groups" :key="item.name" class="nav-item" :class="{ selected: item.name === selectedProjectName }"
          :aria-pressed="item.name === selectedProjectName" :title="item.name" @click="selectProject(item.name)">
          <FolderGit2 :size="17" /><span>{{ item.name }}</span><small>{{ item.count }}</small>
        </button>
        <button v-if="!loading && !projects.length" class="nav-item empty-project" :disabled="busy"
          @click="openDialog('clone', { url: '', name: '' })">
          <Plus :size="17" /><span>Clone a project</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <span class="connection-dot" :class="{ offline: connectionError, connecting: loading }"></span>
        <span>{{ loading ? 'Connecting' : connectionError ? 'Disconnected' : 'Connected' }}</span>
        <span class="footer-running"><Activity :size="13" /> {{ runningCount }} running</span>
      </div>
    </aside>

    <main class="main">
      <header class="toolbar">
        <button class="icon-button sidebar-toggle" aria-label="Show projects" @click.stop="sidebarOpen = !sidebarOpen"><PanelLeft :size="19" /></button>
        <div class="breadcrumb">
          <span v-if="project">Projects <ChevronRight :size="13" /></span>
          <strong>{{ project?.name ?? 'All Tasks' }}</strong>
        </div>
        <div class="toolbar-actions">
          <button class="button subtle project-update" v-if="project" :disabled="busy"
            @click="act(() => request(projectPath(project.name) + '/pull', { method: 'POST' }), 'Project updated', { reloadProjects: true })">
            <ArrowDownToLine :size="15" /> <span>Pull</span>
          </button>
          <div class="menu-anchor">
            <button class="icon-button outlined" aria-label="Workspace actions" title="Workspace actions" :aria-expanded="menu === 'workspace'"
              @click.stop="toggleMenu('workspace')"><Ellipsis :size="19" /></button>
            <div v-if="menu === 'workspace'" class="popover" @click.stop>
              <button :disabled="busy" @click="loadWorkspace().finally(() => { menu = '' })"><RefreshCw :size="15" /> Refresh</button>
              <button :disabled="busy" @click="confirmSync"><Activity :size="15" /> Sync task registry</button>
              <template v-if="project">
                <hr />
                <button @click="openProjectDetails"><Info :size="15" /> Project details</button>
                <button :disabled="busy" @click="openConfig"><FileCode2 :size="15" /> Edit configuration</button>
                <button :disabled="busy || scopedTasks.length > 0" :title="scopedTasks.length ? 'Delete this project’s tasks first' : undefined"
                  class="danger-text" @click="confirmProjectRemoval"><Trash2 :size="15" /> Delete project</button>
              </template>
            </div>
          </div>
          <button class="button primary" :disabled="!projects.length || busy" @click="newTask"><Plus :size="17" /> New Task</button>
        </div>
      </header>

      <div v-if="connectionError || actionError" class="error-banner" role="alert">
        <CircleAlert :size="16" /> <span>{{ actionError || connectionError }}</span>
        <button v-if="actionError" class="icon-button quiet" aria-label="Dismiss error" @click="actionError = ''"><X :size="15" /></button>
        <button v-else class="button subtle" @click="loadWorkspace">Retry</button>
      </div>

      <div class="content">
        <section class="task-list" aria-label="Tasks">
          <div class="list-head">
            <div class="list-title"><h1>Tasks</h1><span class="count">{{ scopedTasks.length }}</span></div>
            <label class="search"><Search :size="16" /><input ref="searchInput" v-model="search" placeholder="Search tasks" aria-label="Search tasks" />
              <button v-if="search" type="button" class="icon-button quiet" aria-label="Clear search" @click="search = ''"><X :size="14" /></button>
              <kbd v-else>⌘ K</kbd>
            </label>
          </div>
          <div v-if="visibleTasks.length" class="list-scroll">
            <table ref="taskTable" class="task-table" aria-label="Task overview">
              <thead>
                <tr><th scope="col">Task</th><th scope="col">Schedule</th><th scope="col">Process</th><th scope="col">Next run</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in visibleTasks" :key="item.name" class="task-row"
                  :class="{ selected: item.name === task?.name }" @click="selectTask(item.name)">
                  <th scope="row">
                    <button class="row-name" :title="item.name" :aria-expanded="item.name === task?.name"
                      :aria-controls="item.name === task?.name ? 'task-details' : undefined" @click.stop="selectTask(item.name)">
                      <span class="task-glyph" :class="{ live: item.is_running }"><Terminal :size="17" /></span>
                      <span><strong>{{ item.name }}</strong><small :title="item.project_name">{{ item.project_name }}</small></span>
                    </button>
                  </th>
                  <td>
                    <span class="pill" :class="scheduleState(item).toLowerCase()">{{ scheduleState(item) }}</span>
                    <small class="row-cron" :title="item.cron">{{ /^\d+$/.test(item.cron) ? item.cron + 's interval' : item.cron }}</small>
                  </td>
                  <td>
                    <span class="row-status"><span class="status-dot" :class="{ live: item.is_running }"></span>{{ item.is_running ? 'Running' : 'Idle' }}</span>
                    <small class="row-result" :class="item.latest_run?.status" :title="item.latest_run?.reason || undefined">
                      {{ item.latest_run ? 'Latest: ' + resultLabels[item.latest_run.status] : 'No runs' }}
                    </small>
                  </td>
                  <td>
                    <time v-if="item.next_run_at" class="row-next" :datetime="item.next_run_at" :title="dateLabel(item.next_run_at)">
                      <span>{{ timeFormat.format(new Date(item.next_run_at)) }}</span>
                      <small>{{ dayFormat.format(new Date(item.next_run_at)) }}</small>
                    </time>
                    <span v-else class="no-next" aria-label="No next run">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty">
            <span class="empty-icon"><Layers3 :size="25" /></span>
            <strong>{{ loading ? 'Loading tasks…' : search ? 'No matching tasks' : 'No tasks yet' }}</strong>
            <button v-if="!loading && !search && projects.length" class="button subtle" :disabled="busy" @click="newTask">
              <Plus :size="16" /> New Task
            </button>
          </div>
        </section>

        <section v-if="task" id="task-details" class="details" aria-labelledby="task-detail-title">
          <div class="detail-heading">
            <span class="detail-icon"><Terminal :size="24" /></span>
            <div class="detail-title"><span>{{ task.project_name }}</span><h2 id="task-detail-title">{{ task.name }}</h2></div>
            <div class="detail-actions">
              <button v-if="task.is_running" class="button stop" :disabled="busy" @click="confirmKill"><Square :size="14" /> Stop</button>
              <button v-else class="button primary" :disabled="busy || !task.registered || !taskProjectExists" @click="taskAction('run', 'Run requested')"><Play :size="15" /> Run Now</button>
              <button v-if="task.status === 'paused'" class="button subtle" :disabled="busy || !task.registered || !taskProjectExists"
                @click="taskAction('resume', 'Schedule resumed')"><Play :size="14" /> Resume Schedule</button>
              <button v-else class="button subtle" :disabled="busy || !task.registered"
                @click="taskAction('pause', 'Schedule paused')"><Pause :size="15" /> Pause Schedule</button>
            </div>
            <div class="detail-tools">
              <div class="menu-anchor">
                <button class="icon-button outlined" aria-label="Task actions" title="Task actions" :aria-expanded="menu === 'task'"
                  @click.stop="toggleMenu('task')"><Ellipsis :size="19" /></button>
                <div v-if="menu === 'task'" class="popover" @click.stop>
                  <button :disabled="busy || !taskProjectExists" @click="editTask"><Pencil :size="15" /> Edit task</button>
                  <button :disabled="busy || task.is_running" class="danger-text" @click="confirmTaskRemoval"><Trash2 :size="15" /> Delete task</button>
                </div>
              </div>
              <button class="icon-button quiet" aria-label="Close task details" title="Close task details" @click="closeTask"><X :size="18" /></button>
            </div>
          </div>

          <div class="detail-tabs" aria-label="Task view">
            <button :aria-pressed="tab === 'logs'" @click="tab = 'logs'"><Terminal :size="15" /> Logs</button>
            <button :aria-pressed="tab === 'history'" @click="tab = 'history'"><Activity :size="15" /> Run History</button>
            <button :aria-pressed="tab === 'info'" @click="tab = 'info'"><Activity :size="15" /> Details</button>
          </div>
          <div v-if="tab === 'logs'" class="log-panel">
            <div class="log-heading">
              <span><span class="status-dot" :class="{ live: task.is_running }"></span> Output</span>
              <button v-if="!following" class="button subtle" @click="followLatest">Jump to latest <ChevronDown :size="14" /></button>
              <small v-else-if="lines.length">{{ lines.length }} lines</small>
            </div>
            <div ref="logsElement" class="log-output" tabindex="0" aria-label="Task output" @scroll="trackScroll">
              <pre v-if="lines.length">{{ logText }}</pre>
              <span v-else>{{ logError || (!task.registered ? 'This task is absent from the scheduler.' : logsLoading ? 'Loading output…' : 'No output yet.') }}</span>
            </div>
            <div v-if="logError && lines.length" class="log-error" role="alert">{{ logError }}</div>
          </div>
          <div v-else-if="tab === 'history'" class="run-history">
            <p v-if="historyError" role="alert">{{ historyError }}</p>
            <p v-else-if="!history.length && !selectedRunId">{{ historyLoading ? 'Loading runs…' : 'No runs recorded yet.' }}</p>
            <div v-if="history.length" class="run-list" aria-label="Recent runs">
              <button v-for="run in history" :key="run.id" class="run-entry"
                :aria-pressed="selectedRunId === run.id" @click="selectedRunId = run.id">
                <strong>{{ resultLabels[run.status] }}</strong>
                <span>{{ run.source === 'manual' ? 'Manual' : 'Scheduled' }} · {{ dateLabel(run.scheduled_at) }}</span>
                <small v-if="run.reason">{{ run.reason }}</small>
              </button>
            </div>
            <div v-if="selectedRunId" class="run-detail">
              <p v-if="runError" role="alert">{{ runError }}</p>
              <template v-else-if="selectedRun">
                <dl class="task-info">
                  <div><dt>Result</dt><dd>{{ resultLabels[selectedRun.status] }}<span v-if="selectedRun.reason"> · {{ selectedRun.reason }}</span></dd></div>
                  <div><dt>Trigger</dt><dd>{{ selectedRun.source === 'manual' ? 'Manual' : 'Scheduled' }} · {{ dateLabel(selectedRun.scheduled_at) }}</dd></div>
                  <div><dt>Started</dt><dd>{{ dateLabel(selectedRun.started_at) }}</dd></div>
                  <div><dt>Finished</dt><dd>{{ dateLabel(selectedRun.finished_at) }}</dd></div>
                  <div><dt>Exit code</dt><dd>{{ selectedRun.exit_code ?? '—' }}</dd></div>
                  <div><dt>Commit</dt><dd><code>{{ selectedRun.commit || '—' }}</code></dd></div>
                </dl>
                <pre v-if="selectedRun.output" class="run-output" tabindex="0" aria-label="Run output">{{ selectedRun.output }}</pre>
                <p v-else-if="selectedRun.status === 'running'">Open Logs to follow this run live.</p>
                <p v-else>No output was recorded for this run.</p>
              </template>
              <p v-else>Loading run…</p>
            </div>
          </div>
          <dl v-else class="task-info">
            <div><dt>Next run</dt><dd>{{ dateLabel(task.next_run_at) }}</dd></div>
            <div><dt>Schedule</dt><dd><code>{{ task.cron }}</code></dd></div>
            <div><dt>Command</dt><dd><code>{{ task.command }}</code></dd></div>
            <div><dt>Timeout</dt><dd>{{ task.timeout ? task.timeout + 's' : 'Unlimited' }}</dd></div>
            <div><dt>Failure alerts</dt><dd>{{ task.notify_on_failure ? 'Enabled' : 'Off' }}</dd></div>
            <div><dt>Updated</dt><dd>{{ dateLabel(task.upgrade_at) }}</dd></div>
            <div><dt>Created</dt><dd>{{ dateLabel(task.created_at) }}</dd></div>
          </dl>
        </section>
      </div>
    </main>
    <Transition><div v-if="notice" class="toast" role="status"><Check :size="17" /> {{ notice }}</div></Transition>

    <dialog ref="dialogElement" :class="{ wide: dialog === 'config' }" aria-labelledby="dialog-title"
      @cancel.prevent="closeDialog" @click.stop>
      <form v-if="dialog" @submit.prevent="submitDialog">
        <header class="dialog-title">
          <h2 id="dialog-title">{{ dialog === 'clone' ? 'Clone project' : dialog === 'task' ? (form.editing ? 'Edit task' : 'New task') : dialog === 'config' ? (form.filename || 'Project configuration') : dialog === 'project' ? form.name : form.title }}</h2>
          <button class="icon-button quiet" type="button" aria-label="Close dialog" :disabled="busy" @click="closeDialog"><X :size="18" /></button>
        </header>
        <div v-if="dialog === 'clone'" class="form-fields">
          <label>Git URL <input v-model="form.url" required placeholder="https://github.com/owner/repo.git" autofocus /></label>
          <label>Project name <input v-model="form.name" placeholder="Optional" /></label>
        </div>
        <div v-else-if="dialog === 'task'" class="form-fields">
          <label>Name <input v-model="form.name" :disabled="form.editing" required placeholder="backup" /></label>
          <label>Project <select v-model="form.project_name" :disabled="form.editing" required>
            <option v-for="item in projects" :key="item.name" :value="item.name">{{ item.name }}</option>
          </select></label>
          <label>Schedule <input v-model="form.cron" required placeholder="0 * * * * or 60" />
            <small>Enter a five-field cron expression or an interval in seconds.</small>
          </label>
          <label>Command <input v-model="form.command" required placeholder="python main.py" /></label>
          <label class="form-check"><input v-model="form.limitRuntime" type="checkbox" /> Stop after a time limit</label>
          <label v-if="form.limitRuntime">Timeout in seconds <input v-model.number="form.timeout" type="number" min="1" step="1" required />
            <small>Includes environment setup and command execution.</small>
          </label>
          <label class="form-check"><input v-model="form.notify_on_failure" type="checkbox" /> Send failure and recovery alerts</label>
          <small>Alerts use the webhook configured on the server.</small>
        </div>
        <div v-else-if="dialog === 'config'" class="config-body">
          <span v-if="form.loading">Loading configuration…</span>
          <ConfigEditor v-else-if="form.filename" v-model="form.content" :filename="form.filename" />
        </div>
        <dl v-else-if="dialog === 'project'" class="task-info project-info">
          <div><dt>Git URL</dt><dd>{{ form.url || '—' }}</dd></div>
          <div><dt>Local path</dt><dd><code>{{ form.project_path }}</code></dd></div>
          <div><dt>Branch</dt><dd>{{ revisionError || (revision ? revision.branch || (revision.commit ? 'Detached HEAD' : '—') : 'Loading…') }}</dd></div>
          <div><dt>Commit</dt><dd><code>{{ revision?.commit || '—' }}</code></dd></div>
          <div><dt>Updated</dt><dd>{{ dateLabel(form.upgrade_at) }}</dd></div>
          <div><dt>Created</dt><dd>{{ dateLabel(form.created_at) }}</dd></div>
        </dl>
        <p v-else class="confirm-copy">{{ form.description }}</p>
        <p v-if="formError" class="form-error" role="alert"><CircleAlert :size="15" /> {{ formError }}</p>
        <footer class="dialog-actions">
          <button type="button" class="button subtle" :disabled="busy" @click="closeDialog">{{ dialog === 'project' ? 'Close' : 'Cancel' }}</button>
          <button v-if="dialog !== 'project'" class="button" :class="dialog === 'confirm' && form.label !== 'Sync Tasks' ? 'destructive' : 'primary'"
            :disabled="busy || (dialog === 'config' && !form.filename)">
            <RefreshCw v-if="busy" class="spin" :size="14" />
            {{ dialog === 'clone' ? 'Clone' : dialog === 'confirm' ? form.label : 'Save' }}
          </button>
        </footer>
      </form>
    </dialog>
  </div>
</template>

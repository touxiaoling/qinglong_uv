class ProjectError(Exception):
    """Base class for all exceptions raised by the project."""

    pass


class ProjectNotFoundError(ProjectError):
    """Raised when a project is not found."""

    def __init__(self, project_name: str):
        super().__init__(f"Project '{project_name}' not found.")
        self.project_name = project_name

    def __str__(self):
        return f"Project '{self.project_name}' not found."


class TaskError(Exception):
    """Base class for all exceptions raised by the task."""

    pass


class SetTaskError(TaskError):
    """Raised when a task is not found."""

    def __init__(self, task_name: str):
        super().__init__(f"Task '{task_name}' set error.")
        self.task_name = task_name

    def __str__(self):
        return f"Task '{self.task_name}' set error."


class TaskNotFoundError(TaskError):
    """Raised when a task is not found."""

    def __init__(self, task_name: str):
        super().__init__(f"Task '{task_name}' not found.")
        self.task_name = task_name

    def __str__(self):
        return f"Task '{self.task_name}' not found."

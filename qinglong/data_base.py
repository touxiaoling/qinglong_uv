import shelve
from .config import settings as cfg

project_db = shelve.open(cfg.DB_PATH/"project.sqlite")
task_db = shelve.open(cfg.DB_PATH/"task.sqlite")
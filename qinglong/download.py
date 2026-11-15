from pathlib import Path
import logging
import httpx2
from git import GitError, Repo
from gitdb.exc import BadName
from .config import settings as cfg

_logger = logging.getLogger(__name__)


def git_revision(path: Path) -> tuple[str | None, str | None]:
    try:
        with Repo(path) as repo:
            head = repo.head
            branch = None if head.is_detached else repo.active_branch.name
            return branch, head.commit.hexsha
    except BadName, GitError, OSError, ValueError:
        return None, None


class FileDownloader:
    def __init__(self, url, filepath, cookies=None):
        self.url = url
        self.filepath = Path(filepath)
        self.session = httpx2.Client()
        self.session.headers.update(cfg.DOWNLOAD_HEADERS)
        if cookies:
            self.session.cookies.update(cookies)

    def download(self):
        url = self.url
        _logger.debug(f"Downloading file from {url} to {self.filepath}")
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        _logger.debug(f"Downloaded file from {url} to {self.filepath}")
        self.filepath.write_bytes(response.content)


class ProjectDownloder:
    def __init__(self, url, projectpath):
        self.url = url
        self.projectpath = Path(projectpath)

    def download(self):
        if not self.projectpath.exists():
            repo = Repo.clone_from(self.url, self.projectpath, depth=1)
        else:
            repo = Repo(self.projectpath)
            repo.remotes.origin.pull(ff_only=True)

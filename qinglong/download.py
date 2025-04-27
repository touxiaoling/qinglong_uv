from pathlib import Path
import logging
import httpx
from git import Repo
from .config import settings as cfg

_logger = logging.getLogger(__name__)
class FileDownloader():
    def __init__(self,url,filepath,cookies=None):
        self.url = url
        self.filepath = Path(filepath)
        self.session = httpx.AsyncClient()
        self.session.headers.update(cfg.DOWNLOAD_HEADERS)
        if cookies:
            self.session.cookies.update(cookies)

    async def download(self):
        url = self.url
        _logger.debug(f"Downloading file from {url} to {self.filepath}")
        response = await self.session.get(url, timeout=30)
        response.raise_for_status()
        _logger.debug(f"Downloaded file from {url} to {self.filepath}")
        self.filepath.write_bytes(response.content)

class ProjectDownloder():
    def __init__(self,url,projectpath):
        self.url = url
        self.projectpath = Path(projectpath)
    
    def download(self):
        if not self.projectpath.exists():
            repo = Repo.clone_from(self.url, self.projectpath, depth=1)
        else:
            repo = Repo(self.projectpath)
            res = repo.remotes.origin.pull()

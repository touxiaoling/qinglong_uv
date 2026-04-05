from pathlib import Path
from unittest.mock import MagicMock, patch

from qinglong.download import FileDownloader, ProjectDownloder


@patch("qinglong.download.httpx.Client")
def test_file_downloader_writes_bytes(mock_client_cls, tmp_path: Path):
    mock_resp = MagicMock()
    mock_resp.content = b"hello"
    mock_resp.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_client_cls.return_value = mock_client

    out = tmp_path / "a.bin"
    fd = FileDownloader("https://example.com/f", out, cookies={"a": "b"})
    fd.download()

    assert out.read_bytes() == b"hello"
    mock_client.cookies.update.assert_called_once()


@patch("qinglong.download.Repo")
def test_project_downloader_clone_when_missing(mock_repo_cls, tmp_path: Path):
    target = tmp_path / "proj"
    assert not target.exists()

    pd = ProjectDownloder("https://example.com/r.git", target)
    pd.download()

    mock_repo_cls.clone_from.assert_called_once()


@patch("qinglong.download.Repo")
def test_project_downloader_pull_when_exists(mock_repo_cls, tmp_path: Path):
    target = tmp_path / "proj"
    target.mkdir()

    pd = ProjectDownloder("https://example.com/r.git", target)
    pd.download()

    mock_repo_cls.assert_called_once_with(target)
    mock_repo_cls.return_value.remotes.origin.pull.assert_called_once()

import pytest

from qinglong import errors


@pytest.mark.parametrize(
    "exc_cls, args, expected_substr",
    [
        (errors.ProjectNotFoundError, ("p1",), "p1"),
        (errors.SetTaskError, ("t1",), "t1"),
        (errors.TaskNotFoundError, ("t2",), "t2"),
        (errors.TaskNotRunningError, ("t3",), "t3"),
    ],
)
def test_error_str(exc_cls, args, expected_substr):
    e = exc_cls(*args)
    assert expected_substr in str(e)

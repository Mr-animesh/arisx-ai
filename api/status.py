"""In-memory last pipeline run summary for the /status endpoint."""

from datetime import datetime
from threading import Lock

_lock = Lock()
_status: dict = {
    "last_run": None,
    "total_programs": 0,
    "new_this_run": 0,
    "last_new_program": None,
}


def update_status(
    *,
    total_programs: int,
    new_this_run: int,
    last_new_program: str | None,
) -> None:
    with _lock:
        _status["last_run"] = datetime.now().isoformat(timespec="seconds")
        _status["total_programs"] = total_programs
        _status["new_this_run"] = new_this_run
        _status["last_new_program"] = last_new_program


def get_status() -> dict:
    with _lock:
        return dict(_status)

import time
from typetrace.backend.db import (
    initialize_database,
    update_keystroke_counts,
)


def test_usability_backend_response(tmp_path):
    """Simulate backend response time for keystroke tracking."""
    db_path = tmp_path / "test.db"
    initialize_database(db_path)

    start = time.time()
    events = [{"scan_code": 1, "name": "a"}]
    update_keystroke_counts(db_path, events)
    duration = time.time() - start

    assert duration < 0.1, "Backend response too slow for usability"

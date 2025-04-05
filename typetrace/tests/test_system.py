import subprocess
import time
from typetrace.backend.db import initialize_database, get_db_connection
from pathlib import Path


def test_system_integration(tmp_path):
    """Test the integration of event tracing and
    database storage without GUI."""
    db_path = tmp_path / "test.db"
    initialize_database(db_path)

    # Simulate running the tracing process in a subprocess
    proc = subprocess.Popen(
        ["python", "-m", "typetrace.backend.events"],
        cwd=str(Path.cwd()),
    )
    time.sleep(1)  # Simulate some activity
    proc.terminate()

    # Check if the database has been initialized correctly
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='keystrokes'"
        )
        assert cursor.fetchone() is not None, "Keystrokes table should exist"

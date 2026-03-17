from typing import Optional


# ─────────────────────── Tasks ───────────────────────

def add_task(command: str, conn) -> int:
    """Insert a new PENDING task and return its auto-generated ID."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (command, status) VALUES (%s, %s)",
        (command, "PENDING"),
    )
    conn.commit()
    task_id = cursor.lastrowid
    cursor.close()
    return task_id


def get_task(task_id: int, conn) -> Optional[dict]:
    """Fetch a single task by ID; returns None if not found."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    cursor.close()
    return task


def list_tasks(conn) -> list[dict]:
    """Return all tasks ordered by creation time (newest first)."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    tasks = cursor.fetchall()
    cursor.close()
    return tasks


def update_task_status(task_id: int, status: str, conn) -> None:
    """Update the status field of a task."""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET status = %s WHERE id = %s",
        (status, task_id),
    )
    conn.commit()
    cursor.close()


def increment_retries(task_id: int, conn) -> None:
    """Atomically increment the retry counter for a task."""
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET retries = retries + 1 WHERE id = %s",
        (task_id,),
    )
    conn.commit()
    cursor.close()


def get_failed_tasks(conn) -> list[dict]:
    """Return all tasks that are in FAILED status."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks WHERE status = 'FAILED'")
    tasks = cursor.fetchall()
    cursor.close()
    return tasks


# ─────────────────────── Logs ───────────────────────

def add_log(task_id: int, output: str, status: str, conn) -> None:
    """Insert an execution log entry for a task."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (task_id, output, status) VALUES (%s, %s, %s)",
        (task_id, output, status),
    )
    conn.commit()
    cursor.close()


def get_logs(task_id: int, conn) -> list[dict]:
    """Return all log entries for a task, newest first."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM logs WHERE task_id = %s ORDER BY executed_at DESC",
        (task_id,),
    )
    logs = cursor.fetchall()
    cursor.close()
    return logs

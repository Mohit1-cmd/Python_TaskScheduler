import pytest
from unittest.mock import MagicMock, patch, call

from app.task_manager import (
    add_task,
    get_task,
    list_tasks,
    update_task_status,
    add_log,
    get_logs,
    get_failed_tasks,
    increment_retries,
)
from app.executor import run_command, run_with_retry


# ══════════════════════════════════════════════════════════════
#  TASK MANAGER TESTS
# ══════════════════════════════════════════════════════════════

class TestAddTask:
    def _mock_conn(self, lastrowid=1):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.lastrowid = lastrowid
        conn.cursor.return_value = cursor
        return conn, cursor

    def test_returns_auto_generated_id(self):
        conn, cursor = self._mock_conn(lastrowid=42)
        result = add_task("echo hello", conn)
        assert result == 42

    def test_executes_insert_statement(self):
        conn, cursor = self._mock_conn()
        add_task("ls -la", conn)
        cursor.execute.assert_called_once()
        sql, params = cursor.execute.call_args[0]
        assert "INSERT INTO tasks" in sql
        assert "ls -la" in params

    def test_commits_transaction(self):
        conn, _ = self._mock_conn()
        add_task("pwd", conn)
        conn.commit.assert_called_once()

    def test_closes_cursor(self):
        conn, cursor = self._mock_conn()
        add_task("date", conn)
        cursor.close.assert_called_once()


class TestGetTask:
    def _mock_conn(self, return_value):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = return_value
        conn.cursor.return_value = cursor
        return conn

    def test_returns_task_dict_when_found(self):
        expected = {"id": 1, "command": "echo hello", "status": "PENDING", "retries": 0}
        conn = self._mock_conn(expected)
        task = get_task(1, conn)
        assert task["id"] == 1
        assert task["command"] == "echo hello"
        assert task["status"] == "PENDING"

    def test_returns_none_for_missing_id(self):
        conn = self._mock_conn(None)
        task = get_task(9999, conn)
        assert task is None

    def test_queries_correct_id(self):
        conn = self._mock_conn(None)
        get_task(7, conn)
        cursor = conn.cursor.return_value
        sql, params = cursor.execute.call_args[0]
        assert "WHERE id" in sql
        assert 7 in params


class TestListTasks:
    def _mock_conn(self, rows):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = rows
        conn.cursor.return_value = cursor
        return conn

    def test_returns_all_tasks(self):
        rows = [
            {"id": 1, "command": "echo a", "status": "SUCCESS"},
            {"id": 2, "command": "echo b", "status": "PENDING"},
        ]
        tasks = list_tasks(self._mock_conn(rows))
        assert len(tasks) == 2
        assert tasks[0]["command"] == "echo a"

    def test_returns_empty_list_when_no_tasks(self):
        tasks = list_tasks(self._mock_conn([]))
        assert tasks == []


class TestUpdateTaskStatus:
    def test_executes_update_with_correct_values(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        update_task_status(3, "SUCCESS", conn)
        sql, params = cursor.execute.call_args[0]
        assert "UPDATE tasks" in sql
        assert "SUCCESS" in params
        assert 3 in params

    def test_commits_after_update(self):
        conn = MagicMock()
        conn.cursor.return_value = MagicMock()
        update_task_status(1, "FAILED", conn)
        conn.commit.assert_called_once()


class TestIncrementRetries:
    def test_increment_calls_correct_sql(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        increment_retries(5, conn)
        sql, params = cursor.execute.call_args[0]
        assert "retries = retries + 1" in sql
        assert 5 in params


class TestAddLog:
    def test_inserts_log_record(self):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        add_log(1, "hello output", "SUCCESS", conn)
        sql, params = cursor.execute.call_args[0]
        assert "INSERT INTO logs" in sql
        assert "hello output" in params
        assert "SUCCESS" in params

    def test_commits_after_insert(self):
        conn = MagicMock()
        conn.cursor.return_value = MagicMock()
        add_log(2, "out", "FAILED", conn)
        conn.commit.assert_called_once()


class TestGetLogs:
    def test_returns_logs_for_task(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 1, "task_id": 1, "output": "hello", "status": "SUCCESS"}
        ]
        conn.cursor.return_value = cursor
        logs = get_logs(1, conn)
        assert len(logs) == 1
        assert logs[0]["output"] == "hello"

    def test_returns_empty_list_when_no_logs(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        conn.cursor.return_value = cursor
        logs = get_logs(99, conn)
        assert logs == []


class TestGetFailedTasks:
    def test_returns_only_failed_tasks(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            {"id": 2, "command": "bad.sh", "status": "FAILED"},
        ]
        conn.cursor.return_value = cursor
        failed = get_failed_tasks(conn)
        assert len(failed) == 1
        assert failed[0]["status"] == "FAILED"

    def test_returns_empty_when_none_failed(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        conn.cursor.return_value = cursor
        assert get_failed_tasks(conn) == []


# ══════════════════════════════════════════════════════════════
#  EXECUTOR TESTS
# ══════════════════════════════════════════════════════════════

class TestRunCommand:
    def test_successful_echo_command(self):
        output, status = run_command("echo hello")
        assert status == "SUCCESS"
        assert "hello" in output

    def test_failed_command_nonzero_exit(self):
        # `false` always exits with code 1
        output, status = run_command("false")
        assert status == "FAILED"

    def test_unknown_command_returns_failed(self):
        output, status = run_command("nonexistent_cmd_xyz_99999")
        assert status == "FAILED"

    def test_output_captured_on_success(self):
        output, status = run_command("echo captured_value")
        assert "captured_value" in output
        assert status == "SUCCESS"

    def test_multiword_command(self):
        output, status = run_command("echo foo bar baz")
        assert status == "SUCCESS"
        assert "foo bar baz" in output


class TestRunWithRetry:
    def test_success_on_first_attempt(self):
        output, status, attempts = run_with_retry("echo ok", max_retries=3, delay=0)
        assert status == "SUCCESS"
        assert attempts == 1

    def test_always_failing_command_returns_failed(self):
        output, status, attempts = run_with_retry("false", max_retries=2, delay=0)
        assert status == "FAILED"
        assert attempts == 2

    def test_retry_count_matches_max_on_all_failures(self):
        _, _, attempts = run_with_retry("false", max_retries=3, delay=0)
        assert attempts == 3

    @patch("app.executor.run_command")
    def test_retries_until_success(self, mock_run):
        # Fail twice then succeed
        mock_run.side_effect = [
            ("err1", "FAILED"),
            ("err2", "FAILED"),
            ("ok",   "SUCCESS"),
        ]
        output, status, attempts = run_with_retry("cmd", max_retries=5, delay=0)
        assert status == "SUCCESS"
        assert attempts == 3
        assert output == "ok"

    @patch("app.executor.run_command")
    def test_stops_immediately_on_first_success(self, mock_run):
        mock_run.return_value = ("done", "SUCCESS")
        _, _, attempts = run_with_retry("cmd", max_retries=10, delay=0)
        assert attempts == 1
        assert mock_run.call_count == 1

    @patch("app.executor.time.sleep")
    @patch("app.executor.run_command")
    def test_sleeps_between_retries(self, mock_run, mock_sleep):
        mock_run.side_effect = [("e", "FAILED"), ("e", "FAILED"), ("ok", "SUCCESS")]
        run_with_retry("cmd", max_retries=3, delay=1.5)
        # sleep called between attempt 1→2 and 2→3 (not after final success)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(1.5)

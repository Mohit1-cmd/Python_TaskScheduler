import subprocess
import time

MAX_RETRIES = 3


def run_command(command: str) -> tuple[str, str]:
    """
    Execute a shell command.

    Returns:
        (output, status) where status is "SUCCESS" or "FAILED".
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            output = result.stdout.strip() or "(no output)"
            return output, "SUCCESS"
        else:
            output = (result.stderr or result.stdout or "(no output)").strip()
            return output, "FAILED"
    except subprocess.TimeoutExpired:
        return "Command timed out after 60 seconds.", "FAILED"
    except Exception as exc:
        return str(exc), "FAILED"


def run_with_retry(
    command: str,
    max_retries: int = MAX_RETRIES,
    delay: float = 2.0,
) -> tuple[str, str, int]:
    """
    Execute a shell command with automatic retry on failure.

    Returns:
        (output, final_status, total_attempts_made)
    """
    output, status = "", "FAILED"
    for attempt in range(1, max_retries + 1):
        output, status = run_command(command)
        if status == "SUCCESS":
            return output, status, attempt
        if attempt < max_retries:
            time.sleep(delay)
    return output, "FAILED", max_retries

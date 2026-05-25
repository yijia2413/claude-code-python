import os
import subprocess


def execute_bash(command: str, cwd: str) -> dict:
    """
    Executes a bash command in the given working directory.
    Captures stdout, stderr, exit code, and determines if the directory changed (e.g. via 'cd').
    """
    stripped_cmd = command.strip()
    if stripped_cmd.endswith("&"):
        actual_cmd = stripped_cmd[:-1].strip()
        from claude_code.daemon.task_manager import task_manager
        task_id = task_manager.start_task(actual_cmd, cwd)
        return {
            "stdout": f"[task {task_id}] 已在后台成功启动。你可以运行 `/ps` 查看状态，或 `/logs {task_id}` 追踪日志。",
            "stderr": "",
            "exit_code": 0,
            "new_cwd": cwd,
        }

    # Use the ___CWD_MARKER___ trick to capture the resulting cwd and exit code
    # We execute: ({ command; } ; EXIT_CODE=$? ; echo "___CWD_MARKER___" ; pwd ; exit $EXIT_CODE)
    # This guarantees that even if the command fails, we get the final cwd and the correct exit code.
    wrapped_command = (
        f"({{ {command} ; }} ; EXIT_CODE=$? ; "
        f"echo '___CWD_MARKER___' ; pwd ; exit $EXIT_CODE)"
    )

    try:
        res = subprocess.run(
            wrapped_command,
            shell=True,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=300,  # 5-minute timeout for safety
        )

        stdout_raw = res.stdout
        stderr = res.stderr
        exit_code = res.returncode

        # Parse stdout to extract the final CWD
        if "___CWD_MARKER___" in stdout_raw:
            parts = stdout_raw.split("___CWD_MARKER___")
            stdout = parts[0]
            # The remaining part is the final cwd, strip newlines and whitespace
            new_cwd = parts[1].strip()
        else:
            stdout = stdout_raw
            new_cwd = cwd

        # Validate that the new_cwd actually exists and is a valid directory
        if not os.path.isdir(new_cwd):
            new_cwd = cwd

        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "new_cwd": os.path.realpath(new_cwd),
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out after 300 seconds.",
            "exit_code": 124,
            "new_cwd": cwd,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Error running command: {str(e)}",
            "exit_code": 1,
            "new_cwd": cwd,
        }

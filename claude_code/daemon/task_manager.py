import os
import subprocess
import time
from typing import Dict, List, Any, Optional

class TaskManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TaskManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.tasks: Dict[int, Dict[str, Any]] = {}
        self.next_id: int = 1
        # Set up tasks logging directory
        self.tasks_dir = os.path.expanduser("~/.claude/tasks")
        os.makedirs(self.tasks_dir, exist_ok=True)

    def start_task(self, command: str, cwd: str) -> int:
        task_id = self.next_id
        self.next_id += 1

        log_path = os.path.join(self.tasks_dir, f"{task_id}.log")
        
        # Open log file to redirect stdout/stderr
        log_file = open(log_path, "w", encoding="utf-8")
        
        # Start background subprocess
        try:
            # On macOS/Linux, we might want to start it in a new process group or preexec_fn if needed,
            # but standard Popen is sufficient for normal background CLI tasks.
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=log_file,
                stderr=log_file,
                text=True,
                start_new_session=True  # prevent SIGINT in CLI from killing background daemon tasks
            )
            
            self.tasks[task_id] = {
                "id": task_id,
                "command": command,
                "cwd": cwd,
                "process": proc,
                "log_path": log_path,
                "log_file": log_file,
                "start_time": time.time(),
                "status": "RUNNING",
                "exit_code": None
            }
            return task_id
        except Exception as e:
            log_file.write(f"Failed to start process: {str(e)}\n")
            log_file.close()
            self.tasks[task_id] = {
                "id": task_id,
                "command": command,
                "cwd": cwd,
                "process": None,
                "log_path": log_path,
                "log_file": None,
                "start_time": time.time(),
                "status": "FAILED",
                "exit_code": 1
            }
            return task_id

    def update_task_status(self, task_id: int) -> str:
        task = self.tasks.get(task_id)
        if not task:
            return "UNKNOWN"
        
        proc = task.get("process")
        if not proc:
            return task["status"]

        poll_res = proc.poll()
        if poll_res is None:
            task["status"] = "RUNNING"
        else:
            # Process terminated, close file if open
            log_file = task.get("log_file")
            if log_file and not log_file.closed:
                log_file.close()

            exit_code = poll_res
            task["exit_code"] = exit_code
            
            # If terminated negative, it was killed by a signal
            if exit_code < 0 or task["status"] == "KILLED":
                task["status"] = "KILLED"
            elif exit_code == 0:
                task["status"] = "COMPLETED"
            else:
                task["status"] = "FAILED"
                
        return task["status"]

    def list_tasks(self) -> List[Dict[str, Any]]:
        result = []
        for task_id in list(self.tasks.keys()):
            self.update_task_status(task_id)
            task = self.tasks[task_id]
            result.append({
                "id": task["id"],
                "command": task["command"],
                "cwd": task["cwd"],
                "status": task["status"],
                "exit_code": task["exit_code"],
                "pid": task["process"].pid if task["process"] else None,
                "elapsed": round(time.time() - task["start_time"], 1)
            })
        return result

    def get_task_log(self, task_id: int, num_lines: int = 100) -> str:
        task = self.tasks.get(task_id)
        if not task:
            return f"Error: Task {task_id} not found."
        
        log_path = task["log_path"]
        if not os.path.exists(log_path):
            return "Log file empty or not created yet."

        try:
            # Flush process output before reading if still running
            proc = task.get("process")
            if proc and proc.poll() is None:
                log_file = task.get("log_file")
                if log_file and not log_file.closed:
                    log_file.flush()

            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                tail_lines = lines[-num_lines:]
                return "".join(tail_lines)
        except Exception as e:
            return f"Error reading log file: {str(e)}"

    def kill_task(self, task_id: int) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        self.update_task_status(task_id)
        if task["status"] != "RUNNING":
            return False

        proc = task.get("process")
        if proc:
            try:
                # Terminate the process
                proc.terminate()
                # Wait up to 1 second
                for _ in range(10):
                    if proc.poll() is not None:
                        break
                    time.sleep(0.1)
                
                # If still alive, kill it
                if proc.poll() is None:
                    proc.kill()
                
                task["status"] = "KILLED"
                task["exit_code"] = proc.poll()
                
                log_file = task.get("log_file")
                if log_file and not log_file.closed:
                    log_file.write("\nTask terminated by user.\n")
                    log_file.close()
                return True
            except Exception:
                return False
        return False

# Global instance
task_manager = TaskManager()

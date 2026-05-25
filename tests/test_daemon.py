import os
import time
import pytest
from claude_code.daemon.task_manager import TaskManager, task_manager

def test_task_manager_lifecycle():
    import sys
    # Setup test task with active python executable path (unbuffered output)
    cmd = f"{sys.executable} -u -c \"import time; print('hello background task'); time.sleep(5)\""
    cwd = os.getcwd()
    
    # 1. Start task
    task_id = task_manager.start_task(cmd, cwd)
    assert task_id > 0
    
    # Let process spin up
    time.sleep(1.0)
    
    # 2. Check status and list
    status = task_manager.update_task_status(task_id)
    assert status == "RUNNING"
    
    tasks = task_manager.list_tasks()
    task_entry = next((t for t in tasks if t["id"] == task_id), None)
    assert task_entry is not None
    assert task_entry["status"] == "RUNNING"
    assert task_entry["pid"] is not None
    
    # 3. Check logs
    log_content = task_manager.get_task_log(task_id)
    assert "hello background task" in log_content
    
    # 4. Kill task
    success = task_manager.kill_task(task_id)
    assert success is True
    
    # Give a tiny slice to register term
    time.sleep(0.5)
    status_after_kill = task_manager.update_task_status(task_id)
    assert status_after_kill == "KILLED"

def test_task_manager_non_existent():
    # Verify non-existent task handling
    log = task_manager.get_task_log(9999)
    assert "not found" in log.lower()
    
    kill_res = task_manager.kill_task(9999)
    assert kill_res is False

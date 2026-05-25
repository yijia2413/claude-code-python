import os
import tempfile
import pytest
from claude_code.tools.bash import execute_bash
from claude_code.tools.file_read import read_file
from claude_code.tools.file_write import write_file
from claude_code.tools.file_edit import edit_file
from claude_code.tools.search import grep_search, glob_files


def test_bash_tool():
    # Test simple command execution
    res = execute_bash("echo 'hello world'", os.getcwd())
    assert res["exit_code"] == 0
    assert "hello world" in res["stdout"].strip()

    # Test cwd updates upon executing cd
    with tempfile.TemporaryDirectory() as tmpdir:
        # Resolve real path in case of symlinks (macOS/tmp)
        tmpdir_real = os.path.realpath(tmpdir)
        
        # Test basic execution in tmpdir
        res = execute_bash("pwd", tmpdir_real)
        assert res["exit_code"] == 0
        assert tmpdir_real in os.path.realpath(res["stdout"].strip())

        # Test cd command updates the returned cwd
        res = execute_bash(f"cd .. && pwd", tmpdir_real)
        assert res["exit_code"] == 0
        parent_dir = os.path.dirname(tmpdir_real)
        assert parent_dir in os.path.realpath(res["stdout"].strip())
        assert os.path.realpath(res["new_cwd"]) == os.path.realpath(parent_dir)

        # Test background process shortcut via '&'
        res = execute_bash("sleep 5 &", tmpdir_real)
        assert res["exit_code"] == 0
        assert "已在后台成功启动" in res["stdout"]
        # Make sure task manager created the task
        from claude_code.daemon.task_manager import task_manager
        tasks = task_manager.list_tasks()
        assert len(tasks) > 0
        # Kill the task to cleanup
        task_id = tasks[-1]["id"]
        task_manager.kill_task(task_id)


def test_file_read_tool():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")
        temp_path = f.name

    try:
        # Test basic read
        res = read_file(temp_path)
        assert "line 1" in res
        assert "line 5" in res
        assert "1\tline 1" in res  # Cat -n style

        # Test offset and limit (1-indexed start_line)
        res = read_file(temp_path, start_line=2, end_line=4)
        assert "line 1" not in res
        assert "2\tline 2" in res
        assert "3\tline 3" in res
        assert "4\tline 4" in res
        assert "line 5" not in res
    finally:
        os.remove(temp_path)


def test_file_write_tool():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "new_file.txt")

        # Test write new file
        res = write_file(file_path, "hello python")
        assert "successfully written" in res
        assert os.path.exists(file_path)

        with open(file_path, "r") as f:
            assert f.read() == "hello python"

        # Test overwrite
        res = write_file(file_path, "updated content")
        assert "successfully written" in res
        with open(file_path, "r") as f:
            assert f.read() == "updated content"


def test_file_edit_tool():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("def func():\n    print('hello')\n    print('world')\n")
        temp_path = f.name

    try:
        # Test simple exact replacement
        res = edit_file(
            file_path=temp_path,
            old_string="    print('hello')",
            new_string="    print('hello edited')"
        )
        assert "successfully updated" in res
        with open(temp_path, "r") as f:
            content = f.read()
            assert "print('hello edited')" in content
            assert "print('hello')" not in content

        # Test non-existent string
        with pytest.raises(ValueError, match="String to replace not found"):
            edit_file(
                file_path=temp_path,
                old_string="missing string",
                new_string="replacement"
            )

        # Test non-unique string
        with open(temp_path, "w") as f:
            f.write("test\ntest\n")
        
        with pytest.raises(ValueError, match="Found 2 matches"):
            edit_file(
                file_path=temp_path,
                old_string="test",
                new_string="replacement"
            )
            
        # Test replace_all unique string
        res = edit_file(
            file_path=temp_path,
            old_string="test",
            new_string="replacement",
            replace_all=True
        )
        assert "successfully updated" in res
        with open(temp_path, "r") as f:
            assert f.read() == "replacement\nreplacement\n"
    finally:
        os.remove(temp_path)


def test_grep_and_glob_tools():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files
        os.makedirs(os.path.join(tmpdir, "subdir"))
        file1 = os.path.join(tmpdir, "file1.txt")
        file2 = os.path.join(tmpdir, "subdir", "file2.py")
        
        with open(file1, "w") as f:
            f.write("target query text here\n")
        with open(file2, "w") as f:
            f.write("another line of code\n")

        # Test glob_files
        res = glob_files(tmpdir, "**/*.py")
        assert any("file2.py" in p for p in res)

        # Test grep_search
        res = grep_search(tmpdir, "target query")
        assert len(res) == 1
        assert "file1.txt" in res[0]
        assert "target query text here" in res[0]

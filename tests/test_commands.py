import os
import tempfile
from claude_code.commands.doctor import run_doctor_diagnosis
from claude_code.commands.bug_hunter import run_bug_hunter_analysis
from claude_code.tools.file_undo import UNDO_STACK, pop_and_undo
from claude_code.tools.file_write import write_file
from claude_code.tools.file_edit import edit_file


def test_doctor_command():
    res = run_doctor_diagnosis()
    assert "System Diagnosis Report" in res
    assert "Operating System" in res


def test_bug_hunter_command():
    res = run_bug_hunter_analysis(os.getcwd())
    assert "Bug Hunter Report" in res


def test_file_undo_stack_restoration():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("original contents\n")
        temp_path = f.name

    try:
        # 1. Modify the file using write_file (should push to undo stack)
        write_file(temp_path, "overwritten contents\n")
        assert len(UNDO_STACK) > 0
        
        # Verify the file was overwritten
        with open(temp_path, "r") as f:
            assert f.read() == "overwritten contents\n"

        # 2. Trigger edit_file (should push another state)
        edit_file(
            file_path=temp_path,
            old_string="overwritten contents",
            new_string="edited contents"
        )
        
        with open(temp_path, "r") as f:
            assert f.read() == "edited contents\n"

        # 3. Pop and undo once (should restore overwritten contents)
        res = pop_and_undo()
        assert "Restored previous content" in res
        with open(temp_path, "r") as f:
            assert f.read() == "overwritten contents\n"

        # 4. Pop and undo again (should restore original contents)
        res = pop_and_undo()
        assert "Restored previous content" in res
        with open(temp_path, "r") as f:
            assert f.read() == "original contents\n"
    finally:
        os.remove(temp_path)

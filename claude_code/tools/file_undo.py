import os

# A global memory-based undo stack to store file state backups before modifications
# Each item is a dictionary: {"file_path": str, "content": str, "exists": bool}
UNDO_STACK = []


def push_file_state(file_path: str):
    """
    Captures and pushes the current state of a file to the undo stack before any edits or writes occur.
    """
    file_path = os.path.abspath(file_path)
    exists = os.path.exists(file_path) and os.path.isfile(file_path)
    
    content = ""
    if exists:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            pass

    UNDO_STACK.append({
        "file_path": file_path,
        "content": content,
        "exists": exists
    })


def pop_and_undo() -> str:
    """
    Pops the latest file state from the undo stack and restores it on the filesystem.
    """
    if not UNDO_STACK:
        return "No changes available to undo."

    state = UNDO_STACK.pop()
    file_path = state["file_path"]
    exists = state["exists"]
    content = state["content"]

    try:
        if not exists:
            # If the file didn't exist before, delete it
            if os.path.exists(file_path):
                os.remove(file_path)
            return f"Undo successful: Removed newly created file {file_path}"
        else:
            # Restore original content
            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Undo successful: Restored previous content of {file_path}"
    except Exception as e:
        return f"Error executing undo for {file_path}: {str(e)}"

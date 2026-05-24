import os


def write_file(file_path: str, content: str) -> str:
    """
    Writes a file to the local filesystem.
    Creates parent directories if they do not exist.
    Overwrites the file if it already exists.
    """
    from claude_code.tools.file_undo import push_file_state
    # Ensure file_path is absolute
    file_path = os.path.abspath(file_path)

    # Push state to undo stack before writing
    push_file_state(file_path)

    # Ensure parent directory exists
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"File successfully written to {file_path}"

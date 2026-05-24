import os


def write_file(file_path: str, content: str) -> str:
    """
    Writes a file to the local filesystem.
    Creates parent directories if they do not exist.
    Overwrites the file if it already exists.
    """
    # Ensure file_path is absolute
    file_path = os.path.abspath(file_path)

    # Ensure parent directory exists
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"File successfully written to {file_path}"

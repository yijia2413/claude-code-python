import os


def edit_file(
    file_path: str, old_string: str, new_string: str, replace_all: bool = False
) -> str:
    """
    Performs exact string replacements in a file.
    Validates that:
    1. The target file exists.
    2. The old_string is found in the file.
    3. If there are multiple occurrences of old_string, replace_all must be True.
    """
    file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Empty old_string handling
    if old_string == "":
        if content.strip() != "":
            raise ValueError(
                "Cannot insert content without old_string target in a non-empty file."
            )
        # Empty file with empty old_string: replace empty content with new_string
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_string)
        return f"The empty file {file_path} has been successfully updated with the content."

    # Exact match check
    occurrences = content.count(old_string)
    if occurrences == 0:
        raise ValueError(
            f"String to replace not found in file:\n{old_string}"
        )

    if occurrences > 1 and not replace_all:
        raise ValueError(
            f"Found {occurrences} matches of the string to replace, but replace_all is false. "
            "To replace all occurrences, set replace_all to true. To replace only one, "
            "provide more surrounding context to uniquely identify it."
        )

    # Perform the edit
    if replace_all:
        updated_content = content.replace(old_string, new_string)
    else:
        updated_content = content.replace(old_string, new_string, 1)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    return f"The file {file_path} has been successfully updated."

import fnmatch
import os


def grep_search(dir_path: str, query: str) -> list:
    """
    Ripgrep-like search: finds exact text matches within files in the given directory recursively.
    Returns a list of match strings with path, line number, and content line.
    """
    dir_path = os.path.abspath(dir_path)
    results = []

    # Limit search results to prevent huge output
    limit = 100

    for root, dirs, files in os.walk(dir_path):
        # Skip git folders and build folders for performance
        if any(ignored in root.split(os.sep) for ignored in (".git", "__pycache__", ".venv", "venv", "node_modules", "build", "dist")):
            continue

        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    for line_num, line in enumerate(f, 1):
                        if query in line:
                            rel_path = os.path.relpath(file_path, dir_path)
                            results.append(f"{rel_path}:{line_num}:{line.strip()}")
                            if len(results) >= limit:
                                return results
            except Exception:
                # Silently ignore binary files or permission issues
                continue

    return results


def glob_files(dir_path: str, pattern: str) -> list:
    """
    Finds files matching the glob pattern inside dir_path recursively.
    """
    dir_path = os.path.abspath(dir_path)
    matches = []

    for root, dirs, files in os.walk(dir_path):
        # Skip standard build/vcs folders
        if any(ignored in root.split(os.sep) for ignored in (".git", "__pycache__", ".venv", "venv", "node_modules")):
            continue

        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, dir_path)
            
            # fnmatch matches relative path cleanly
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(filename, pattern):
                matches.append(rel_path)

    return sorted(matches)

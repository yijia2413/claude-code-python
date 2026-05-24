import json
import os


def read_file(
    file_path: str, start_line: int = None, end_line: int = None
) -> str:
    """
    Reads a file from the local filesystem.
    Supports absolute paths, line numbering, start/end range offsets,
    and formats Jupyter notebooks (.ipynb) cleanly.
    """
    # Ensure the path is absolute
    file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if os.path.isdir(file_path):
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    # Handle Jupyter notebooks
    if file_path.endswith(".ipynb"):
        return _read_jupyter_notebook(file_path)

    # Read normal text file
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total_lines = len(lines)

    # Resolve default line limits
    start = 1 if start_line is None else max(1, start_line)
    end = total_lines if end_line is None else min(total_lines, end_line)

    if start > total_lines:
        return f"Warning: start_line ({start}) exceeds total line count ({total_lines}). File has empty contents here."

    output_lines = []
    # Lines in list are 0-indexed, start/end parameters are 1-indexed
    for idx in range(start - 1, end):
        line_num = idx + 1
        line_content = lines[idx]
        output_lines.append(f"{line_num}\t{line_content}")

    return "".join(output_lines)


def _read_jupyter_notebook(file_path: str) -> str:
    """
    Parses a Jupyter Notebook (.ipynb) and renders cells and outputs cleanly as text.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            notebook = json.load(f)

        cells = notebook.get("cells", [])
        output = []

        for idx, cell in enumerate(cells):
            cell_type = cell.get("cell_type", "code")
            source = "".join(cell.get("source", []))
            output.append(f"--- Cell [{idx + 1}] ({cell_type}) ---")
            output.append(source)

            # Render outputs for code cells
            if cell_type == "code" and "outputs" in cell:
                cell_outputs = cell.get("outputs", [])
                if cell_outputs:
                    output.append("\n[Outputs]")
                    for out in cell_outputs:
                        out_type = out.get("output_type", "")
                        if out_type == "stream":
                            output.append("".join(out.get("text", [])))
                        elif out_type in ("execute_result", "display_data"):
                            data = out.get("data", {})
                            # Prefer text/plain representation if available
                            if "text/plain" in data:
                                output.append("".join(data["text/plain"]))
                            elif "text/html" in data:
                                output.append("HTML output omitted.")
                        elif out_type == "error":
                            output.append(f"Error: {out.get('ename', '')}: {out.get('evalue', '')}")
            output.append("\n")

        return "\n".join(output)

    except Exception as e:
        return f"Error parsing Jupyter Notebook: {str(e)}"

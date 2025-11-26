# file_utils.py

import json
import csv
from pathlib import Path
from datetime import datetime


def _to_input_path(path: str | Path) -> Path:
    """
    Map a relative path to the 'input' folder.

    - If the path is absolute, it is returned as-is.
    - If the path is relative, it is resolved as 'input/<path>'.
    """
    p = Path(path)
    if p.is_absolute():
        return p
    return Path("input") / p


def _to_output_path(path: str | Path) -> Path:
    """
    Map a relative path to the 'output' folder.

    - If the path is absolute, it is returned as-is.
    - If the path is relative, it is resolved as 'output/<path>'.
    """
    p = Path(path)
    if p.is_absolute():
        return p
    return Path("output") / p


def _with_timestamp_if_exists(path: Path) -> Path:
    """
    If the given path already exists, append a human-readable timestamp
    to the filename (before the extension).

    Example:
        output/result.sql      -> exists
        output/result_2025-11-20_15-42-10.sql (new path)
    """
    if not path.exists():
        return path

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")


def resolve_input_path(path: str | Path) -> Path:
    """
    Public helper to map a relative path to the 'input' folder.
    """
    return _to_input_path(path)


def resolve_output_path(path: str | Path, with_timestamp: bool = True) -> Path:
    """
    Public helper to map a relative path to the 'output' folder.

    If with_timestamp is True and the file exists, a timestamp is appended
    to avoid overwriting the existing file.
    """
    resolved = _to_output_path(path)
    if with_timestamp:
        return _with_timestamp_if_exists(resolved)
    return resolved


def read_json(path: str | Path):
    """
    Read a JSON file from disk and return the parsed content.
    The file is read from the 'input' folder unless an absolute path is provided.
    """
    path = _to_input_path(path)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data, indent: int = 2) -> Path:
    """
    Write a Python object as JSON to disk.
    The file is written to the 'output' folder unless an absolute path is provided.
    If the target file already exists, a human-readable timestamp is appended
    to the filename.

    Returns:
        The final Path used to write the file.
    """
    path = _to_output_path(path)
    path = _with_timestamp_if_exists(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    return path


def read_csv(path: str | Path) -> list[dict]:
    """
    Read a CSV file and return a list of dictionaries (one per row).
    The file is read from the 'input' folder unless an absolute path is provided.
    """
    path = _to_input_path(path)
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: str | Path, rows: list[dict], fieldnames: list[str]) -> Path:
    """
    Write a list of dictionaries to a CSV file.
    The file is written to the 'output' folder unless an absolute path is provided.
    If the target file already exists, a human-readable timestamp is appended
    to the filename.

    Returns:
        The final Path used to write the file.
    """
    path = _to_output_path(path)
    path = _with_timestamp_if_exists(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_text(path: str | Path, content: str) -> Path:
    """
    Write plain text to a file.
    The file is written to the 'output' folder unless an absolute path is provided.
    If the target file already exists, a human-readable timestamp is appended
    to the filename.

    Returns:
        The final Path used to write the file.
    """
    path = _to_output_path(path)
    path = _with_timestamp_if_exists(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def escape_sql_literal(text: str) -> str:
    """
    Escape single quotes in a string so it can be safely used
    as a SQL literal value.
    """
    return text.replace("'", "''")


def load_dhis_env_config(
    default_base_url: str,
    default_jsessionid: str,
    env_path: str | Path | None = None,
) -> tuple[str, str]:
    """
    Look for a .env file and try to read DHIS2 configuration from it.
    If a valid BASE_URL and JSESSIONID are found, show them to the user
    (masking the JSESSIONID) and ask for confirmation.

    If the user presses ENTER, the values from .env are used.
    If the user types 'n' or 'N' and presses ENTER, the defaults are kept.

    Args:
        default_base_url: Fallback base URL if .env is not used or not found.
        default_jsessionid: Fallback JSESSIONID if .env is not used or not found.
        env_path: Optional explicit path to the .env file. If None, "./.env" is used.

    Returns:
        (base_url, jsessionid) either from .env (if confirmed) or the defaults.
    """
    if env_path is None:
        env_path = Path(".") / ".env"
    else:
        env_path = Path(env_path)

    if not env_path.is_file():
        return default_base_url, default_jsessionid

    base_url_env: str | None = None
    jsessionid_env: str | None = None

    try:
        with env_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                key_upper = key.upper()
                if key_upper == "BASE_URL":
                    base_url_env = value
                elif key_upper == "JSESSIONID":
                    jsessionid_env = value
    except Exception as e:
        print(f"[WARN] Failed to read .env file at {env_path}: {e}")
        return default_base_url, default_jsessionid

    if not base_url_env or not jsessionid_env:
        return default_base_url, default_jsessionid

    masked_jsessionid = (
        jsessionid_env[:6] + "..." if len(jsessionid_env) > 6 else jsessionid_env
    )

    print("Found .env configuration:")
    print(f"  Base URL   : {base_url_env}")
    print(f"  JSESSIONID : {masked_jsessionid}")
    print()
    answer = input(
        "Press ENTER to use this configuration, or type 'n' and press ENTER to ignore it: "
    ).strip()

    if answer.lower() == "n":
        print("Using default configuration (ignoring .env).")
        return default_base_url, default_jsessionid

    print("Using configuration from .env.")
    return base_url_env, jsessionid_env

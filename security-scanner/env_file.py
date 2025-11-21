from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class EnvFile:
    """Small helper to read/write key=value pairs in a .env-style file."""

    def __init__(self, env_dir: Path, filename: str = ".env") -> None:
        self.path = Path(env_dir) / filename

    def load_to_environ(self, overwrite: bool = False) -> None:
        """
        Load all variables from this .env file into os.environ.

        If overwrite is False, existing environment variables are not replaced.
        """
        if not self.path.is_file():
            return

        for raw_line in self.path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if overwrite or key not in os.environ:
                os.environ[key] = value

    def read_key(self, key: str) -> Optional[str]:
        """
        Read the value for a given key from this .env file, if present.
        Returns None if the key is not found.
        """
        if not self.path.is_file():
            return None

        for raw_line in self.path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            raw_key, raw_value = line.split("=", 1)
            if raw_key.strip() == key:
                value = raw_value.strip()
                return value or None
        return None

    def write_key(self, key: str, value: str) -> None:
        """
        Ensure this .env file contains a line 'key=value'.
        Existing lines are preserved; the key line is added or updated.
        """
        lines: list[str] = []
        if self.path.is_file():
            lines = self.path.read_text(encoding="utf-8").splitlines()

        found = False
        new_lines: list[str] = []

        for raw_line in lines:
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if "=" in stripped:
                existing_key = stripped.split("=", 1)[0].strip()
            else:
                existing_key = ""

            if existing_key == key:
                new_lines.append(f"{key}={value}")
                found = True
            else:
                new_lines.append(line)

        if not found:
            if new_lines and new_lines[-1].strip() != "":
                new_lines.append("")
            new_lines.append(f"{key}={value}")

        self.path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

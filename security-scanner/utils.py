from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class ConsoleUtils:
    """Common utilities for console interaction and helper functions."""

    def __init__(self, interactive: bool = True) -> None:
        self.interactive = interactive

    def print_header(self, title: str) -> None:
        border = "=" * 80
        print(f"\n{border}\n{title}\n{border}\n")

    def print_step(self, message: str) -> None:
        print(f"\n▶ {message}\n")

    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """
        Ask for a yes/no answer on the terminal.
        default=True  -> [Y/n]
        default=False -> [y/N]
        """
        if not self.interactive:
            return default

        while True:
            suffix = " [Y/n]: " if default else " [y/N]: "
            answer = input(question + suffix).strip().lower()

            if answer == "" and default is not None:
                return default
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False
            print("Please answer 'y' or 'n'.")

    def run_command(self, command: list[str], cwd: Optional[str] = None, confirm: bool = True) -> int:
        """
        Run a command showing clearly what will be executed.
        Pause before running so the user can see it.
        """
        print("-" * 60)
        print("About to run:")
        print("  " + " ".join(command))
        if cwd:
            print(f"Working directory: {cwd}")
        print("-" * 60)
        if self.interactive and confirm:
            input("Press Enter to continue... (Ctrl+C to abort) ")

        try:
            result = subprocess.run(command, cwd=cwd)
        except FileNotFoundError:
            print("❌ Command not found. Is it installed and in your PATH?")
            return 127

        if result.returncode == 0:
            print("✅ Command finished successfully.")
        else:
            print(f"⚠️ Command exited with code {result.returncode}. Check the output above.")
        return result.returncode

    @staticmethod
    def find_executable(name: str) -> Optional[str]:
        """Return the path to an executable or None if not found."""
        return shutil.which(name)

    @staticmethod
    def load_env_file(path: str) -> None:
        """
        Load a simple .env file (KEY=VALUE per line) into the current environment.
        Lines starting with '#' or without '=' are ignored.
        """
        env_path = Path(path)
        if not env_path.is_file():
            print(f"⚠️ .env file not found: {env_path}")
            return

        print(f"\n▶ Loading environment variables from {env_path}\n")
        with env_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value
        print("✅ .env variables loaded into the current process.")

    @staticmethod
    def read_package_metadata(app_root: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Try to read name and version from package.json.
        Returns (name, version) or (None, None).
        """
        pkg_path = Path(app_root) / "package.json"
        if not pkg_path.is_file():
            return None, None

        try:
            with pkg_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("name"), data.get("version")
        except Exception:
            return None, None

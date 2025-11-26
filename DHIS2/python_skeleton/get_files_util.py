import os
from pathlib import Path

# === CONFIGURATION ===
# Used to get all the files in one file to check in chatgpt
BASE_DIR = Path(__file__).resolve().parent
MAX_BYTES = 200_000  # maximum file size to read


def main():
    for root, dirs, files in os.walk(BASE_DIR):
        for name in files:
            path = os.path.join(root, name)

            # Skip hidden files and folders (e.g. .git, .idea, .venv, etc.)
            if any(part.startswith(".") for part in path.split(os.sep)):
                continue

            # Skip common binary / large formats
            if any(
                path.endswith(ext)
                for ext in (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pyc", ".sql", ".csv")
            ):
                continue

            try:
                # Skip very large files
                if os.path.getsize(path) > MAX_BYTES:
                    continue

                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, OSError):
                # Binary or unreadable files -> skip
                continue

            rel_path = os.path.relpath(path, BASE_DIR)

            print("\n" + "=" * 80)
            print(f"FILE: {rel_path}")
            print("=" * 80 + "\n")
            print(content)
            print("\n")  # extra separation


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path
from typing import Optional

from utils import ConsoleUtils


class BomTool:
    """Generates a CycloneDX BOM (bom.json) for a Node-based project."""

    def __init__(self, utils: ConsoleUtils) -> None:
        self.u = utils
        self.node_version: Optional[str] = None  # Node version to use via nvm (optional)

    def run(
        self,
        app_root: str,
        node_version: Optional[str] = None,
        interactive: bool = True,
    ) -> Optional[Path]:
        """
        Orchestrates BOM generation:
        - Ask (optional) Node.js version (via nvm)
        - Run npm install + CycloneDX BOM generation
        """
        self.u.print_header("Step 2 - CycloneDX BOM generation")

        if interactive and node_version is None:
            self._ask_node_version()
        else:
            self.node_version = node_version

        return self._generate_bom(app_root)

    # ------------------------------------------------------------------
    # Node.js version (optional, via nvm)
    # ------------------------------------------------------------------

    def _ask_node_version(self) -> None:
        self.u.print_step("Node.js version (optional)")

        print(
            "By default this step will use whatever 'node' is in your PATH.\n"
            "If you know a specific Node.js version (managed by nvm) that should be used\n"
            "for this project (for example 20.19.0), you can enter it here.\n"
            "If you later see 'npm WARN EBADENGINE Unsupported engine', you can cancel\n"
            "with Ctrl+C and rerun this assistant with another Node version.\n"
        )

        version = input("Node.js version to use with nvm (leave empty to use current): ").strip()
        self.node_version = version or None
        if self.node_version:
            print(f"Will try to use Node.js {self.node_version} via nvm.")
        else:
            print("Using current Node.js from PATH (no nvm override).")

    # ------------------------------------------------------------------
    # BOM generation (single shell command)
    # ------------------------------------------------------------------

    def _generate_bom(self, app_root: str) -> Optional[Path]:
        """
        Generate a CycloneDX BOM (bom.json) using npm + npx in a single shell command.
        This will:
        - Print node -v
        - Run npm install
        - Run npx @cyclonedx/cyclonedx-npm to produce bom.json
        Optionally, it will switch Node.js version using nvm first.
        """

        if not self.u.find_executable("npm"):
            print("❌ npm is not available in PATH. Cannot generate BOM.")
            return None

        print(
            "\nℹ️ If you see 'npm WARN EBADENGINE Unsupported engine', it means the project\n"
            "   expects a different Node.js version (for example ^20.19.0).\n"
            "   In that case, you can cancel with Ctrl+C and rerun this assistant with\n"
            "   a different Node version when prompted.\n"
        )

        self.u.print_step("Installing dependencies and generating CycloneDX BOM (npm install + npx)")

        if self.node_version:
            # Single shell command:
            # - Load nvm (if available)
            # - nvm install <version>
            # - nvm use <version>
            # - node -v
            # - npm install
            # - npx @cyclonedx/cyclonedx-npm ...
            shell_cmd = (
                "source ~/.nvm/nvm.sh 2>/dev/null || "
                "source /usr/share/nvm/nvm.sh 2>/dev/null || "
                "source /usr/local/opt/nvm/nvm.sh 2>/dev/null || true; "
                f"nvm install {self.node_version}; "
                f"nvm use {self.node_version}; "
                "node -v; "
                "npm install; "
                "npx @cyclonedx/cyclonedx-npm "
                "--output-file bom.json "
                "--output-format json"
            )
            rc = self.u.run_command(["bash", "-lc", shell_cmd], cwd=app_root)
        else:
            # No nvm: use whatever Node.js is in PATH
            shell_cmd = (
                "node -v; "
                "npm install; "
                "npx @cyclonedx/cyclonedx-npm "
                "--output-file bom.json "
                "--output-format json"
            )
            rc = self.u.run_command(["bash", "-lc", shell_cmd], cwd=app_root)

        if rc != 0:
            print("❌ Failed to generate bom.json (npm install or npx failed).")
            return None

        bom_path = Path(app_root) / "bom.json"
        if not bom_path.is_file():
            print("❌ bom.json not found after generation.")
            return None

        print(f"✅ BOM generated at: {bom_path}")
        return bom_path

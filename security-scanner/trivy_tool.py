from __future__ import annotations

import shutil
from pathlib import Path

from utils import ConsoleUtils


class TrivyTool:
    """Encapsulates Trivy SBOM scanning."""

    def __init__(self, utils: ConsoleUtils) -> None:
        self.u = utils

    def run(self, bom_path: Path) -> bool:
        self.u.print_header("Step 3 - Trivy (scan BOM)")

        if not self.u.find_executable("docker"):
            print("❌ 'docker' is not in PATH. Cannot run Trivy in a container.")
            return False

        if not bom_path.is_file():
            print(f"❌ BOM file not found: {bom_path}. Generate bom.json before running Trivy.")
            return False

        home = Path.home()
        base_dir = home / "docker" / "trivy"
        input_dir = base_dir / "input"
        cache_dir = base_dir / "cache-scan"

        self.u.print_step(f"Preparing directories for Trivy under {base_dir}")
        input_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)

        target_bom = input_dir / "bom.json"
        self.u.print_step(f"Copying {bom_path} to {target_bom}")
        shutil.copy2(bom_path, target_bom)

        self.u.print_step("Running Trivy on bom.json")
        cmd = [
            "docker",
            "run",
            "--rm",
            "--name",
            "trivy",
            "-v",
            f"{cache_dir}:/root/.cache/",
            "-v",
            f"{input_dir}:/project",
            "-w",
            "/project",
            "aquasec/trivy:latest",
            "sbom",
            "./bom.json",
        ]
        rc = self.u.run_command(cmd)
        return rc == 0


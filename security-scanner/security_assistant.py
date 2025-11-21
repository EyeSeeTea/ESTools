from __future__ import annotations

import sys
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from utils import ConsoleUtils
from snyk_tool import SnykTool
from bom_tool import BomTool
from dependency_track_tool import DependencyTrackTool
from trivy_tool import TrivyTool


@dataclass
class SecurityConfig:
    app_root: Optional[Path]
    forced: bool
    run_snyk: bool
    run_bom: bool
    run_trivy: bool
    run_dtrack: bool
    node_version: Optional[str]
    dtrack_api_port: str
    dtrack_ui_port: str
    dtrack_api_url: Optional[str]
    project_name: Optional[str]
    project_version: Optional[str]


def build_config(args: argparse.Namespace) -> SecurityConfig:
    app_root = Path(args.app_root).resolve() if args.app_root else None

    return SecurityConfig(
        app_root=app_root,
        forced=args.forced,
        run_snyk=not args.no_snyk,
        run_bom=not args.no_bom,
        run_trivy=not args.no_trivy,
        run_dtrack=not args.no_dtrack,
        node_version=args.node_version,
        dtrack_api_port=args.dtrack_api_port or "8081",
        dtrack_ui_port=args.dtrack_ui_port or "8080",
        dtrack_api_url=args.dependency_track_server,
        project_name=args.project_name,
        project_version=args.project_version,
    )


class SecurityAssistant:
    """Coordinates Snyk, BOM generation, Trivy and Dependency-Track using modular tools."""

    def __init__(self, config: SecurityConfig) -> None:
        self.config = config
        self.utils = ConsoleUtils(interactive=not config.forced)
        self.snyk = SnykTool(self.utils)
        self.bom_tool = BomTool(self.utils)
        self.dependency_track = DependencyTrackTool(self.utils)
        self.trivy = TrivyTool(self.utils)

    def run(self) -> int:
        self.utils.print_header("Security Assistant - Snyk / BOM / Trivy / Dependency-Track")

        try:
            app_root = self._resolve_app_root()
            project_name, project_version = self._detect_project_metadata(
                app_root,
                require_name=self.config.project_name is None,
                require_version=self.config.project_version is None,
                allow_prompt=not self.config.forced,
            )
        except ValueError as exc:
            print(f"❌ {exc}")
            return 1

        if self.config.project_name:
            project_name = self.config.project_name
        if self.config.project_version:
            project_version = self.config.project_version

        bom_path: Optional[Path] = None
        trivy_was_run = False

        # 1) BOM generation
        if self._should_run_step(
            self.config.run_bom,
            "Do you want to generate a CycloneDX BOM (bom.json)?",
        ):
            bom_path = self.bom_tool.run(
                app_root,
                node_version=self.config.node_version,
                interactive=not self.config.forced,
            )
            if bom_path is None and self.config.forced:
                print("❌ Failed to generate bom.json in forced mode.")
                return 1
        else:
            print("ℹ️ Skipping BOM generation.")

        # Fallback: if BOM already exists from previous runs
        if bom_path is None:
            candidate = Path(app_root) / "bom.json"
            if candidate.is_file():
                bom_path = candidate

        # 2) Trivy (CLI scan of the BOM)
        if self._should_run_step(
            self.config.run_trivy,
            "Do you want to scan the BOM with Trivy?",
        ):
            if bom_path is None:
                print("❌ No BOM found (bom.json). Generate it before running Trivy.")
                if self.config.forced:
                    return 1
            else:
                trivy_ok = self.trivy.run(bom_path)
                if not trivy_ok and self.config.forced:
                    print("❌ Trivy scan failed in forced mode.")
                    return 1
                trivy_was_run = trivy_ok
        else:
            print("ℹ️ Skipping Trivy.")

        # 4) Dependency-Track (UI + analyzers)
        if self._should_run_step(
            self.config.run_dtrack,
            "Do you want to start Dependency-Track and upload the BOM?",
        ):
            if bom_path is None:
                print("❌ No BOM found (bom.json). Generate it before using Dependency-Track.")
                if self.config.forced:
                    return 1
            else:
                dtrack_ok = self.dependency_track.run(
                    bom_path=bom_path,
                    project_name=project_name,
                    project_version=project_version,
                    enable_trivy_analyzer=trivy_was_run,
                    api_port=self.config.dtrack_api_port,
                    ui_port=self.config.dtrack_ui_port,
                    api_url=self.config.dtrack_api_url,
                    api_key=None,
                    interactive=not self.config.forced,
                )
                if not dtrack_ok and self.config.forced:
                    return 1
        else:
            print("ℹ️ Skipping Dependency-Track.")

        # 4) Snyk (run last so its output stays visible)
        if self._should_run_step(
            self.config.run_snyk,
            "Do you want to run Snyk (snyk test)?",
        ):
            snyk_ok = self.snyk.run(app_root, non_interactive=self.config.forced)
            if not snyk_ok and self.config.forced:
                return 1
        else:
            print("ℹ️ Skipping Snyk.")

        self._print_summary()
        return 0

    # ---- internal helpers ----

    def _should_run_step(self, enabled: bool, question: str, default: bool = True) -> bool:
        if not enabled:
            return False
        if self.config.forced:
            return True
        return self.utils.ask_yes_no(question, default=default)

    def _resolve_app_root(self) -> str:
        if self.config.app_root:
            if self.config.app_root.is_dir():
                resolved = str(self.config.app_root)
                print(f"Using application root from CLI: {resolved}")
                return resolved
            if self.config.forced:
                raise ValueError(f"Provided app root is not a directory: {self.config.app_root}")
            print(f"❌ Provided app root is not a directory: {self.config.app_root}")
        if self.config.forced:
            raise ValueError("In forced mode you must provide --path pointing to a valid directory.")
        return self._ask_app_root()

    def _ask_app_root(self) -> str:
        while True:
            raw_path = input("Path to the application root ('.' for current directory): ").strip() or "."
            app_root = str(Path(raw_path).resolve())
            if Path(app_root).is_dir():
                print(f"Using application root: {app_root}")
                self.config.app_root = Path(app_root)
                return app_root
            print("❌ That path does not exist or is not a directory. Please try again.")

    def _detect_project_metadata(
        self,
        app_root: str,
        require_name: bool,
        require_version: bool,
        allow_prompt: bool,
    ) -> Tuple[str, str]:
        """
        Detect project name and version from package metadata (e.g. package.json),
        falling back to folder name and default version if not found.

        If the package metadata is missing and CLI overrides were not provided,
        interactively request the values when allowed. In forced mode, missing
        values will raise an error so the caller can abort early.
        """
        default_name = Path(app_root).name
        default_version = "1.0.0"
        pkg_name, pkg_version = self.utils.read_package_metadata(app_root)

        project_name = pkg_name or None
        project_version = pkg_version or None

        if project_name is None:
            if require_name:
                if allow_prompt:
                    prompt_default = default_name
                    user_name = input(
                        f"Project name for Dependency-Track [{prompt_default}]: "
                    ).strip()
                    project_name = user_name or prompt_default
                else:
                    raise ValueError(
                        "Project name not found in package metadata. "
                        "Provide it via --project-name when running in forced mode."
                    )
            else:
                project_name = default_name

        if project_version is None:
            if require_version:
                if allow_prompt:
                    prompt_default = default_version
                    user_version = input(
                        f"Project version for Dependency-Track [{prompt_default}]: "
                    ).strip()
                    project_version = user_version or prompt_default
                else:
                    raise ValueError(
                        "Project version not found in package metadata. "
                        "Provide it via --project-version when running in forced mode."
                    )
            else:
                project_version = default_version

        print(f"Detected project name: {project_name}")
        print(f"Detected project version (or default): {project_version}")
        return project_name, project_version

    def _print_summary(self) -> None:
        self.utils.print_header("All steps completed")
        dtrack_ui = self.config.dtrack_api_url or f"http://localhost:{self.config.dtrack_ui_port}"
        print("Check the results in:")
        print(" - Snyk: this terminal output")
        print(f" - Dependency-Track UI: {dtrack_ui}")
        print(" - Trivy: container output from 'aquasec/trivy:latest'")
        print("\n✅ Security assistant finished.\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Security Assistant - run Snyk, CycloneDX BOM, Trivy and Dependency-Track on a project"
    )
    parser.add_argument(
        "-p",
        "--path",
        dest="app_root",
        metavar="APP_ROOT",
        help="Path to the application root (if omitted, you'll be prompted interactively unless --forced is set).",
    )
    parser.add_argument(
        "--forced",
        action="store_true",
        help="Run in fully non-interactive mode (no prompts).",
    )
    parser.add_argument("--no-snyk", action="store_true", help="Skip Snyk step.")
    parser.add_argument("--no-bom", action="store_true", help="Skip BOM generation.")
    parser.add_argument("--no-trivy", action="store_true", help="Skip Trivy scan.")
    parser.add_argument("--no-dtrack", action="store_true", help="Skip Dependency-Track step.")
    parser.add_argument("--node-version", help="Node.js version to use via nvm (e.g. 20.19.0).")
    parser.add_argument(
        "--dtrack-api-port",
        help="Host port to expose the Dependency-Track API when running locally (default 8081).",
    )
    parser.add_argument(
        "--dtrack-ui-port",
        help="Host port to expose the Dependency-Track UI when running locally (default 8080).",
    )
    parser.add_argument(
        "--dependency-track-server",
        dest="dependency_track_server",
        metavar="URL",
        help=(
            "Dependency-Track API base URL to use without prompting (for example http://localhost:8081). "
            "If provided, the assistant will connect to that server instead of starting a local stack."
        ),
    )
    parser.add_argument("--project-name", help="Override project name for Dependency-Track.")
    parser.add_argument("--project-version", help="Override project version for Dependency-Track.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = build_config(args)
    assistant = SecurityAssistant(config)
    return assistant.run()


if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...\n")
        exit_code = 1
    sys.exit(exit_code)

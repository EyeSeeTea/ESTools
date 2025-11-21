from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

import requests

from utils import ConsoleUtils
from env_file import EnvFile


class DependencyTrackTool:
    """
    Handles Dependency-Track orchestration and BOM upload.

    It does NOT generate the BOM. It expects an existing bom.json path.

    Two main modes:
      1) Local mode: start Dependency-Track via docker compose on this machine.
      2) Remote mode: connect to an already running Dependency-Track instance.
    """

    def __init__(self, utils: ConsoleUtils) -> None:
        self.u = utils

        # Default host ports for a local instance started via docker compose.
        self.api_port: str = "8081"   # host port for API server
        self.ui_port: str = "8080"    # host port for Web UI

        # Optional Trivy analyzer support when running a local stack.
        self.enable_trivy_analyzer: bool = False
        self.trivy_token: Optional[str] = None  # Token used by the Trivy server (if enabled)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        bom_path: Path,
        project_name: str,
        project_version: str,
        enable_trivy_analyzer: bool = False,
        api_port: str = "8081",
        ui_port: str = "8080",
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        interactive: bool = True,
    ) -> bool:
        """
        Orchestrates Dependency-Track usage:

        - Ask whether to:
            a) Start a local Dependency-Track instance with docker compose.
            b) Connect to an already running Dependency-Track instance.
        - Local mode:
            - Ask ports
            - Start docker-compose (with or without Trivy server)
            - Use the local instance URL for the upload
        - Remote mode:
            - Ask for the Dependency-Track API base URL
            - If api_url is provided, remote mode is assumed automatically
        - Upload the given BOM to the chosen Dependency-Track instance.
        - If interactive=False, rely entirely on the provided parameters / env vars.
        """
        self.u.print_header("Step 4 - Dependency-Track (docker-compose / existing instance + upload)")

        if not bom_path.is_file():
            print(f"❌ BOM file not found: {bom_path}. Generate bom.json before using Dependency-Track.")
            return False

        self.enable_trivy_analyzer = enable_trivy_analyzer
        self.api_port = api_port or self.api_port
        self.ui_port = ui_port or self.ui_port

        # Decide whether to start a local instance or connect to an existing one
        script_dir = Path(__file__).resolve().parent
        docker_dir = script_dir / "docker" / "dependency-track"
        selected_mode = "local"

        if api_url:
            print("Using Dependency-Track server provided via CLI argument.")
            selected_mode = "remote"
        elif interactive:
            use_local_stack = self.u.ask_yes_no(
                "Do you want this assistant to start Dependency-Track locally with Docker?",
                default=True,
            )
            selected_mode = "local" if use_local_stack else "remote"
        else:
            selected_mode = "local"

        if selected_mode == "local":
            if not self._run_local_dependency_track(docker_dir, interactive=interactive):
                return False
        else:
            if not self._configure_existing_dependency_track_url(
                interactive=interactive,
                provided_url=api_url,
            ):
                return False

        # Upload the BOM using whatever URL configuration we ended up with.
        return self._upload_bom_to_dependency_track(
            bom_path=bom_path,
            project_name=project_name,
            project_version=project_version,
            api_url_override=api_url if not interactive else None,
            api_key_override=api_key,
            interactive=interactive,
        )

    # ------------------------------------------------------------------
    # Mode selection helpers
    # ------------------------------------------------------------------

    def _run_local_dependency_track(self, docker_dir: Path, interactive: bool) -> bool:
        """
        Start a local Dependency-Track stack using docker compose.

        This will:
          - Ask for host ports (API/UI).
          - Optionally resolve a Trivy token and configure the Trivy server.
          - Start docker compose in the provided docker_dir.

        It also sets a default DTRACK_API_URL pointing to the local API port,
        so the upload step can use it if the user has not defined one.
        """
        self._ask_ports(interactive=interactive)

        # If the Trivy analyzer is enabled, make sure we have a token ready
        if self.enable_trivy_analyzer:
            token = self._resolve_trivy_token(interactive=interactive)
            if not token:
                return False
            self.trivy_token = token
        else:
            self.trivy_token = None

        if not self._ensure_dependency_track_running(docker_dir):
            return False

        # If DTRACK_API_URL is not already defined, default to the local instance
        os.environ.setdefault("DTRACK_API_URL", f"http://localhost:{self.api_port}")
        return True

    def _configure_existing_dependency_track_url(
        self,
        interactive: bool,
        provided_url: Optional[str] = None,
    ) -> bool:
        """
        Configure connection to an already running Dependency-Track instance.

        This method:
          - Uses environment variable DTRACK_API_URL if present.
          - Otherwise tries to load a previously stored URL from assistant .env.
          - Falls back to 'http://localhost:8081' as a generic default.
          - Asks the user to confirm or override the URL.
          - Normalizes it so it represents the base URL (without /api/v1/bom).
          - Persists the chosen URL in the assistant .env file and in os.environ.
        """
        self.u.print_step("Connecting to an existing Dependency-Track instance")

        assistant_root = Path(__file__).resolve().parent
        env_file = EnvFile(assistant_root)

        # Load any existing .env variables without overriding real environment
        env_file.load_to_environ(overwrite=False)

        # Priority for default URL:
        #   1) DTRACK_API_URL environment variable
        #   2) dependency_tracker_url in assistant .env
        #   3) plain localhost default
        default_url = os.environ.get("DTRACK_API_URL") or env_file.read_key("dependency_tracker_url")
        normalized_url: Optional[str] = None

        if provided_url:
            normalized_url = self._normalize_api_base_url(provided_url.strip())
        elif interactive:
            fallback = default_url or "http://localhost:8081"
            print(
                "\nYou chose to connect to an already running Dependency-Track instance.\n"
                "Please provide the base URL of its API server, for example:\n"
                "  http://dtrack.example.com:8080\n"
                "  http://localhost:8081\n"
            )
            user_url = input(f"Dependency-Track API base URL [{fallback}]: ").strip() or fallback
            normalized_url = self._normalize_api_base_url(user_url)
        else:
            if not default_url:
                print(
                    "❌ DTRACK_API_URL (or dependency_tracker_url in the assistant .env) "
                    "is required in forced mode when using a remote server."
                )
                return False
            normalized_url = self._normalize_api_base_url(default_url)

        normalized_url = self._maybe_fix_ui_port(normalized_url)

        # Store in environment and .env for future runs.
        os.environ["DTRACK_API_URL"] = normalized_url
        if interactive or provided_url:
            env_file.write_key("dependency_tracker_url", normalized_url)

        print(f"Using Dependency-Track API base URL: {normalized_url}")
        return True

    @staticmethod
    def _normalize_api_base_url(url: str) -> str:
        """
        Normalize a Dependency-Track URL so it is a base API URL (no /api/v1/bom).

        Examples:
          - 'http://host:8081/api/v1/bom' -> 'http://host:8081'
          - 'http://host:8081/api/v1'     -> 'http://host:8081'
          - 'http://host:8081/api'        -> 'http://host:8081'
          - 'http://host:8081/'           -> 'http://host:8081'
        """
        # Strip trailing slash to simplify processing
        stripped = url.rstrip("/")

        # Remove any known API suffixes if present
        for suffix in ("/api/v1/bom", "/api/v1", "/api"):
            if stripped.endswith(suffix):
                stripped = stripped[: -len(suffix)]
                break

        return stripped

    def _maybe_fix_ui_port(self, url: str) -> str:
        """
        If the provided URL looks like the Dependency-Track UI port (8080) without an API
        path, automatically switch to the default API port (8081) and warn the user.
        """
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return url

        if parsed.port == 8080 and (parsed.path in ("", "/")):
            fixed = parsed._replace(netloc=f"{parsed.hostname}:8081")
            new_url = urlunparse(fixed)
            print(
                "Provided URL appears to point to the UI port (8080). "
                "Using the default API port instead: "
                f"{new_url}"
            )
            return new_url

        return url

    # ------------------------------------------------------------------
    # Ports (local mode only)
    # ------------------------------------------------------------------

    def _ask_ports(self, interactive: bool) -> None:
        """Ask the user which host ports to use for the API and UI containers."""
        self.u.print_step("Dependency-Track ports")

        print(
            "Default ports are:\n"
            f"  - API: {self.api_port} (host) → 8080 (container)\n"
            f"  - UI : {self.ui_port} (host) → 8080 (container)\n"
            "\nIf those ports are already in use, you can choose different ones.\n"
        )

        if interactive:
            api = input(f"API host port [{self.api_port}]: ").strip()
            ui = input(f"UI  host port [{self.ui_port}]: ").strip()

            if api:
                self.api_port = api
            if ui:
                self.ui_port = ui
        else:
            print(
                "Using provided ports without prompting "
                f"(API={self.api_port}, UI={self.ui_port}) due to forced mode."
            )

        print(f"Using API port: {self.api_port}")
        print(f"Using UI  port: {self.ui_port}")

    # ------------------------------------------------------------------
    # Trivy token resolution (local + Trivy mode)
    # ------------------------------------------------------------------

    def _resolve_trivy_token(self, interactive: bool) -> Optional[str]:
        """
        Resolve the token used by the Trivy server.

        Resolution order:
          1) Environment variable TRIVY_SERVER_TOKEN (if set).
          2) .env file next to this assistant (key: trivy_server_token).
          3) Interactive prompt:
             - If user enters a value, use it.
             - If left empty, fall back to default 'SECRETTOKEN123'.

        In cases (2) and (3), the token is stored in the assistant's .env file
        so it can be reused on future runs.
        """
        assistant_root = Path(__file__).resolve().parent
        env_file = EnvFile(assistant_root)

        # 1) Try environment variable
        env_token = os.environ.get("TRIVY_SERVER_TOKEN")
        if env_token:
            print("Using Trivy server token from environment variable TRIVY_SERVER_TOKEN.")
            print("Remember to configure the same token in the Trivy analyzer in Dependency-Track.")
            return env_token

        # 2) Try token from assistant .env
        file_token = env_file.read_key("trivy_server_token")
        if file_token:
            print("Using Trivy server token from assistant .env (trivy_server_token).")
            print("Remember to configure the same token in the Trivy analyzer in Dependency-Track.")
            return file_token

        # 3) Ask the user; allow an empty value to mean 'use the default'
        if not interactive:
            print(
                "❌ TRIVY_SERVER_TOKEN is required in forced mode. "
                "Set it via environment variable or trivy_server_token in the assistant .env."
            )
            return None

        default_token = "SECRETTOKEN123"
        user_input = input(
            f"Enter Trivy server token (leave empty to use default '{default_token}'): "
        ).strip()

        token = user_input or default_token

        # Persist in assistant .env for future runs
        env_file.write_key("trivy_server_token", token)

        if user_input:
            print(
                "Using Trivy server token provided by user and storing it in assistant .env "
                "(key: trivy_server_token)."
            )
        else:
            print(
                f"Using default Trivy server token '{default_token}' and storing it in assistant .env "
                "(key: trivy_server_token)."
            )

        print("You will need to configure the same token in the Trivy analyzer settings in Dependency-Track.")
        return token

    # ------------------------------------------------------------------
    # docker-compose helper (.env for ports + Trivy)
    # ------------------------------------------------------------------

    def _write_compose_env(self, docker_dir: Path) -> None:
        """
        Write a .env file in the docker-compose directory with the selected ports
        and, if enabled, the Trivy configuration (port and token).

        docker-compose.*.yml will use these variables.
        """
        env_path = docker_dir / ".env"
        lines: list[str] = [
            f"DTRACK_API_PORT={self.api_port}",
            f"DTRACK_UI_PORT={self.ui_port}",
        ]
        # Trivy-related environment variables are only written when the analyzer is enabled
        if self.enable_trivy_analyzer:
            lines.append("TRIVY_PORT=4954")
            if self.trivy_token:
                lines.append(f"TRIVY_TOKEN={self.trivy_token}")

        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # Ensure Dependency-Track is running (local mode only)
    # ------------------------------------------------------------------

    def _ensure_dependency_track_running(self, docker_dir: Path) -> bool:
        """
        Ensure Dependency-Track is running via docker compose in docker_dir.

        Expects:
          - docker-compose.base.yml (always)
          - docker-compose.trivy.yml (optional, used when enable_trivy_analyzer=True)
        """
        if not self.u.find_executable("docker"):
            print("❌ 'docker' is not in PATH. Cannot start Dependency-Track.")
            return False

        docker_dir.mkdir(parents=True, exist_ok=True)

        base_compose = docker_dir / "docker-compose.base.yml"
        trivy_compose = docker_dir / "docker-compose.trivy.yml"

        if not base_compose.is_file():
            print(f"❌ Missing docker-compose.base.yml in {docker_dir}")
            print("   Expected dependency-track docker-compose configuration to be present on disk.")
            return False

        # Write .env with selected ports (and Trivy settings) so docker-compose can use them
        self._write_compose_env(docker_dir)

        cmd = ["docker", "compose", "-f", str(base_compose)]

        if self.enable_trivy_analyzer and trivy_compose.is_file():
            cmd += ["-f", str(trivy_compose)]

        cmd += ["up", "-d"]

        self.u.print_step("Starting Dependency-Track with 'docker compose up -d'")
        rc = self.u.run_command(cmd, cwd=str(docker_dir))
        if rc == 0:
            ui_url = f"http://localhost:{self.ui_port}"

            trivy_note = ""
            if self.enable_trivy_analyzer and trivy_compose.is_file():
                # Build the API token line depending on whether we actually have a token
                if self.trivy_token:
                    api_token_line = (
                        f"  API token: {self.trivy_token} "
                        "(must match the token configured for the Trivy server)\n"
                    )
                else:
                    api_token_line = (
                        "  API token: (none; no token configured for the Trivy server)\n"
                    )

                trivy_note = (
                    "\nIf this assistant started a Trivy server (trivy-server service), you can configure it in "
                    "Dependency-Track under:\n"
                    "  Administration → Analyzers → Trivy\n"
                    "Use the following settings:\n"
                    "  Base URL : http://trivy-server:4954\n"
                    f"{api_token_line}"
                )

            print(
                f"""\nℹ️ Dependency-Track UI: {ui_url}
Initial login for a brand new instance:
  username: admin
  password: admin

You will be forced to change the admin password on first login.
Please store the new password in a password manager.

Recommended next step for automation:
  1) Go to: Administration → Access Management → Teams
  2) Create or select a team (for example "Automation")
  3) Generate an API key for that team
  4) Enter it once in this assistant when asked for "Dependency-Track API Key"
This assistant will store that token in a local .env file next to these scripts and reuse it for future BOM uploads.
{trivy_note}"""
            )
        else:
            print("⚠️ Failed to start Dependency-Track. Check Docker and docker compose.")
            return False
        return True

    # ------------------------------------------------------------------
    # BOM upload to Dependency-Track (shared by both modes)
    # ------------------------------------------------------------------

    def _upload_bom_to_dependency_track(
        self,
        bom_path: Path,
        project_name: str,
        project_version: str,
        api_url_override: Optional[str],
        api_key_override: Optional[str],
        interactive: bool,
    ) -> bool:
        """
        Upload the generated BOM to Dependency-Track using the requests library.

        The API key is resolved in this order:
          1) Environment variable DTRACK_API_KEY (if set).
          2) Local .env file next to this assistant (key: dependency_tracker_token).
          3) Interactive prompt; if provided, it is persisted in that .env file.

        The API URL is resolved as follows:
          - Environment variable DTRACK_API_URL (if set; can be a base URL).
          - If not set, defaults to http://localhost:<self.api_port>.
          - If the URL does not already end with '/api/v1/bom', this method
            will append '/api/v1/bom' to construct the final endpoint.
        """
        # Assistant root directory: where this script (and the rest of the assistant) lives.
        # We store a reusable .env file here so the API key is global for the assistant,
        # not per scanned project.
        assistant_root = Path(__file__).resolve().parent
        env_file = EnvFile(assistant_root)

        # Load variables from the assistant's .env into the current environment,
        # but do not override existing environment variables.
        env_file.load_to_environ(overwrite=False)

        self.u.print_step("Preparing BOM upload to Dependency-Track")

        # Resolve API base URL (can come from parameters, environment or be the local default)
        api_url = api_url_override or os.environ.get("DTRACK_API_URL")
        if not api_url:
            if interactive:
                api_url = f"http://localhost:{self.api_port}"
            else:
                print(
                    "❌ DTRACK_API_URL is required in forced mode. "
                    "Set it in the environment or dependency_tracker_url in the assistant .env."
                )
                return False
        api_url = self._maybe_fix_ui_port(api_url)
        print(f"Using Dependency-Track API base URL: {api_url}")
        if not api_url.endswith("/api/v1/bom"):
            api_url = api_url.rstrip("/") + "/api/v1/bom"
        print(f"Full BOM endpoint: {api_url}")

        # 1) Try user-provided API key or environment variable
        api_key: Optional[str] = api_key_override or os.environ.get("DTRACK_API_KEY")

        # 2) Try token from the assistant's .env under a reusable key
        if not api_key:
            token_from_file = env_file.read_key("dependency_tracker_token")
            if token_from_file:
                print("Loading Dependency-Track API token from assistant .env (dependency_tracker_token)")
                api_key = token_from_file

        # 3) Ask user as last resort and persist in the assistant's .env for future runs
        if not api_key and interactive:
            api_key = input("Enter Dependency-Track API Key (leave empty to skip upload): ").strip()
            if api_key:
                env_file.write_key("dependency_tracker_token", api_key)

        if not api_key:
            print(
                "❌ Dependency-Track API key is required. "
                "In forced mode configure DTRACK_API_KEY or dependency_tracker_token in the assistant .env."
            )
            return False

        self.u.print_step("Project details for Dependency-Track")
        print(f"Detected project name: {project_name}")
        print(f"Detected project version: {project_version}")
        if interactive:
            project_name = input(f"Project name in Dependency-Track [{project_name}]: ").strip() or project_name
            project_version = input(f"Project version [{project_version}]: ").strip() or project_version

        print(f"Using projectName='{project_name}', projectVersion='{project_version}'")

        data = {
            "autoCreate": "true",
            "projectName": project_name,
            "projectVersion": project_version,
        }

        headers = {"X-Api-Key": api_key}

        self.u.print_step("Uploading BOM to Dependency-Track via HTTP request")
        try:
            with bom_path.open("rb") as bom_file:
                files = {"bom": (bom_path.name, bom_file, "application/json")}
                response = requests.post(
                    api_url,
                    data=data,
                    headers=headers,
                    files=files,
                    timeout=120,
                )
        except requests.RequestException as exc:
            print(f"⚠️ Failed to upload BOM: {exc}")
            return False

        if response.ok:
            print("✅ BOM uploaded successfully.")
            return True

        print(
            f"⚠️ Dependency-Track responded with status {response.status_code}: "
            f"{response.text}"
        )
        return False

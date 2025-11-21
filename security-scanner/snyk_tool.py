from __future__ import annotations

import os
from pathlib import Path

from env_file import EnvFile
from utils import ConsoleUtils


class SnykTool:
    """
    Best-effort Snyk runner:
    1) Try 'snyk test' immediately.
    2) If it fails, ensure the CLI is installed.
    3) Try to authenticate (non-interactive uses SNYK_TOKEN if present, otherwise skips).
    4) Run 'snyk test' again and return the result.
    """

    def __init__(self, utils: ConsoleUtils) -> None:
        self.u = utils

    def run(self, app_root: str, non_interactive: bool = False) -> bool:
        self.u.print_header("Step 1 - Snyk")

        if non_interactive:
            assistant_root = Path(__file__).resolve().parent
            EnvFile(assistant_root).load_to_environ(overwrite=False)

        # First attempt: run snyk test straight away
        if self._run_snyk_test(app_root):
            return True

        # Ensure CLI exists before retrying
        if not self.u.find_executable("snyk"):
            self.u.print_step("Snyk CLI not found. Trying to install via npm.")
            if not self._install_snyk():
                print("❌ Could not install Snyk with 'npm install -g snyk'.")
                return False

        # Attempt authentication if possible (skipped in forced mode without token)
        auth_ok = True
        if non_interactive:
            snyk_token = os.environ.get("SNYK_TOKEN")
            if snyk_token:
                auth_ok = self._auth(token=snyk_token, interactive=False)
            else:
                print(
                    "Skipping 'snyk auth' in forced mode because SNYK_TOKEN is not set. "
                    "If the CLI is not already authenticated, 'snyk test' may still fail."
                )
        else:
            auth_ok = self._auth()
            if not auth_ok:
                print("❌ 'snyk auth' failed. Fix authentication and try again.")
                return False

        if not auth_ok:
            return False

        # Final attempt: run snyk test again
        return self._run_snyk_test(app_root)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth(self, token: str | None = None, interactive: bool = True) -> bool:
        """
        Run `snyk auth`. If a token is provided, use non-interactive auth; otherwise
        perform the interactive login flow.
        """
        if token:
            self.u.print_step("Running 'snyk auth' with SNYK_TOKEN")
            rc = self.u.run_command(["snyk", "auth", token])
            if rc != 0:
                print("⚠️ 'snyk auth <token>' failed. Check the output above for details.")
                return False
            print("✅ 'snyk auth' completed successfully with provided token.")
            return True

        self.u.print_step("Running 'snyk auth'")
        if interactive:
            print(
                "This will open a browser or show a URL so you can log in to your Snyk account.\n"
                "You usually only need to do this once per machine.\n"
            )
        rc = self.u.run_command(["snyk", "auth"])
        if rc != 0:
            print("⚠️ 'snyk auth' failed. Check the output above for details.")
            return False
        print("✅ 'snyk auth' completed successfully.")
        return True

    def _install_snyk(self) -> bool:
        """Try to install Snyk globally with npm; return True on success."""
        self.u.print_step("Installing Snyk with 'npm install -g snyk'")
        rc = self.u.run_command(["npm", "install", "-g", "snyk"])
        if rc != 0:
            print("⚠️ 'npm install -g snyk' failed. Check the output above for details.")
            return False
        print("✅ Snyk installation command finished (npm install -g snyk).")
        return True

    def _run_snyk_test(self, app_root: str) -> bool:
        """Run `snyk test` from the project root and report success/failure."""
        self.u.print_step("Running 'snyk test' from the project root")
        rc = self.u.run_command(["snyk", "test"], cwd=app_root)

        if rc != 0:
            print("⚠️ 'snyk test' finished with errors. Check the output above for details.")
            return False
        else:
            print("✅ 'snyk test' completed successfully.")
            return True

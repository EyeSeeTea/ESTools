#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import time
from datetime import datetime

# === CONSTANTS (same across all environments) ===
CHECK_INTERVAL_SECONDS = 2
RECOVERY_LOG_INTERVAL_SECONDS = 30
STOP_TIMEOUT_SECONDS = 30
# How long to wait for RAM to settle after stopping a tier before escalating
SETTLE_SECONDS = 20
STATE_FILE = "/run/stopram/state.json"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "RAM Sentinel: stops services managed by Monit when available RAM "
            "drops critically low. Services are stopped in --tier order and "
            "restored in reverse order once RAM recovers."
        )
    )
    parser.add_argument(
        "--emergency-trigger",
        type=int,
        required=True,
        metavar="MB",
        help="Available RAM (MB) that triggers emergency actions",
    )
    parser.add_argument(
        "--safe-recovery",
        type=int,
        required=True,
        metavar="MB",
        help="Available RAM (MB) required before handing services back to Monit",
    )
    parser.add_argument(
        "--tier",
        action="append",
        dest="tiers",
        metavar="TYPE:MONIT_NAME",
        help=(
            "Service to stop, in escalation order. Format: TYPE:MONIT_NAME. "
            "TYPE must be 'kill' (SIGKILL the monitored PID) or "
            "'stop' (monit stop — uses the service's stop program). "
            "Repeat --tier for multiple services. Example: "
            "--tier kill:dhis_tomcat --tier stop:postgres"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Simulate all actions without executing them. Reads RAM, Monit status "
            "and PIDs for real — only skips the destructive commands "
            "(unmonitor, kill, stop, monitor)."
        ),
    )
    cfg = parser.parse_args()

    if not cfg.tiers:
        parser.error("At least one --tier is required.")

    cfg.tiers = [_parse_tier(t, parser) for t in cfg.tiers]
    return cfg


def _parse_tier(raw, parser):
    parts = raw.split(":", 1)
    if len(parts) != 2:
        parser.error(f"Invalid --tier format '{raw}'. Expected TYPE:MONIT_NAME.")
    tier_type, monit_name = parts
    if tier_type not in ("kill", "stop"):
        parser.error(f"Unknown tier type '{tier_type}'. Must be 'kill' or 'stop'.")
    if not monit_name:
        parser.error(f"Missing monit name in --tier '{raw}'.")
    return {"type": tier_type, "name": monit_name}


def info(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}", flush=True)


def run_cmd(cmd, shell=False, timeout=None):
    try:
        if isinstance(cmd, str) and not shell:
            cmd = cmd.split()
        return subprocess.check_output(
            cmd, shell=shell, text=True, timeout=timeout
        ).strip()
    except subprocess.TimeoutExpired:
        info(f"WARNING: command timed out after {timeout}s: {cmd}")
        return None
    except subprocess.CalledProcessError as e:
        info(f"Error executing '{cmd}': {e}")
        return None


def get_available_memory_mb():
    try:
        output = run_cmd("free -m")
        if output:
            for line in output.split("\n"):
                if line.startswith("Mem:"):
                    parts = line.split()
                    return int(parts[6])
    except Exception as e:
        info(f"Failed to query available memory: {e}")
    return 0


def get_monit_names():
    """Returns the set of service names known to Monit."""
    output = run_cmd("monit summary -B") or run_cmd("monit summary")
    if not output:
        return set()
    names = set()
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            # Cover both formats: 'name status ...' and "Process 'name' status ..."
            names.add(parts[0].strip("'\""))
            names.add(parts[1].strip("'\""))
    return names


def validate_tiers(tiers):
    """Logs a WARNING for any tier whose monit name is not in 'monit summary'.
    Keeps running — a misconfigured tier should not leave the host unprotected."""
    known = get_monit_names()
    if not known:
        info("WARNING: could not retrieve Monit service list — skipping tier validation.")
        return
    for tier in tiers:
        if tier["name"] not in known:
            info(
                f"WARNING: tier '{tier['type']}:{tier['name']}' — "
                f"'{tier['name']}' not found in 'monit summary'. "
                f"Check the service name or update --tier."
            )


def get_monit_pid(monit_name):
    """Returns the PID reported by Monit for a service, or None."""
    output = run_cmd(f"monit status {monit_name}")
    if not output:
        return None
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("pid"):
            parts = stripped.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])
    return None


def pid_is_alive(pid):
    return os.path.exists(f"/proc/{pid}")


def wait_for_ram_settle(threshold_mb, max_seconds=SETTLE_SECONDS):
    """Polls RAM for up to max_seconds. Returns available RAM when stable or timeout."""
    deadline = time.monotonic() + max_seconds
    while time.monotonic() < deadline:
        ram = get_available_memory_mb()
        if ram > 0 and ram >= threshold_mb:
            return ram
        time.sleep(CHECK_INTERVAL_SECONDS)
    return get_available_memory_mb()


def log_system_snapshot():
    try:
        snapshot = run_cmd("free -m")
        info(f"Memory snapshot (free -m):\n{snapshot}")
        top_procs = run_cmd(
            "ps -eo pid,%mem,rss,comm --sort=-%mem | head -11", shell=True
        )
        info(f"Top processes by memory:\n{top_procs}")
    except Exception as e:
        info(f"WARNING: system snapshot failed (non-fatal): {e}")


def stop_tier(tier, dry_run=False):
    """Stops a single tier. Returns the monit name."""
    name = tier["name"]
    tier_type = tier["type"]

    if tier_type == "kill":
        # Read PID before unmonitoring — monit status is unreliable after unmonitor
        pid = get_monit_pid(name)
        if pid is None:
            info(
                f"Tier kill:{name} — no PID found in monit status. "
                f"Process may already be dead. Unmonitoring anyway."
            )
        elif not pid_is_alive(pid):
            info(
                f"Tier kill:{name} — PID {pid} no longer alive. Unmonitoring anyway."
            )
            pid = None
        else:
            info(f"Tier kill:{name} — PID {pid} found and alive.")

        info(f"Tier kill:{name} — unmonitoring...")
        maybe_run(f"monit unmonitor {name}", dry_run)

        if pid is not None:
            info(f"Tier kill:{name} — sending SIGKILL to PID {pid}...")
            if dry_run:
                info(f"[DRY-RUN] would os.kill({pid}, 9)")
            else:
                try:
                    os.kill(pid, 9)
                    info(f"Tier kill:{name} — PID {pid} killed.")
                except Exception as e:
                    info(f"Tier kill:{name} — SIGKILL failed: {e}")

    elif tier_type == "stop":
        info(f"Tier stop:{name} — unmonitoring...")
        maybe_run(f"monit unmonitor {name}", dry_run)
        info(f"Tier stop:{name} — running monit stop...")
        maybe_run(f"monit stop {name}", dry_run, timeout=STOP_TIMEOUT_SECONDS)

    if dry_run:
        info(f"[DRY-RUN] would sleep 3s for OS to reclaim memory.")
    else:
        time.sleep(3)

    return name


def save_state(stopped_names, dry_run=False):
    if dry_run:
        info(f"[DRY-RUN] would persist state: {stopped_names}")
        return
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        tmp_file = STATE_FILE + ".tmp"
        with open(tmp_file, "w") as f:
            json.dump(
                {
                    "stopped_services": stopped_names,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
            )
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, STATE_FILE)
    except Exception as e:
        info(f"WARNING: failed to write state file {STATE_FILE}: {e}")


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f).get("stopped_services", [])
    except FileNotFoundError:
        return []
    except Exception as e:
        info(f"WARNING: failed to read state file {STATE_FILE}: {e}")
        return []


def clear_state():
    try:
        os.remove(STATE_FILE)
    except FileNotFoundError:
        pass
    except Exception as e:
        info(f"WARNING: failed to remove state file {STATE_FILE}: {e}")


def maybe_run(cmd, dry_run, shell=False, timeout=None):
    """Runs cmd unless dry_run is True, in which case just logs it."""
    if dry_run:
        info(f"[DRY-RUN] would run: {cmd}")
        return None
    return run_cmd(cmd, shell=shell, timeout=timeout)


def enable_monit_service(name, dry_run=False):
    info(f"Re-enabling Monit tracking for '{name}'...")
    maybe_run(f"monit monitor {name}", dry_run)


def stop_tier_and_settle(cfg, tier, stopped_names):
    """Stops a tier, persists state, waits for RAM to settle. Returns updated available RAM."""
    name = tier["name"]

    save_state(stopped_names + [name], dry_run=cfg.dry_run)
    stop_tier(tier, dry_run=cfg.dry_run)
    stopped_names.append(name)
    save_state(stopped_names, dry_run=cfg.dry_run)

    info(f"Waiting up to {SETTLE_SECONDS}s for RAM to settle after stopping '{name}'...")
    if cfg.dry_run:
        available_ram = get_available_memory_mb()
    else:
        available_ram = wait_for_ram_settle(cfg.emergency_trigger)
    info(f"Available RAM after stopping '{name}': {available_ram} MB.")
    return available_ram


def run_recovery_routine(cfg):
    available_ram = get_available_memory_mb()
    info(
        f"CRITICAL ALERT: Available RAM ({available_ram} MB) < "
        f"Emergency Threshold ({cfg.emergency_trigger} MB)!"
    )

    log_system_snapshot()

    stopped_names = []

    for tier in cfg.tiers:
        available_ram = stop_tier_and_settle(cfg, tier, stopped_names)
        if available_ram > 0 and available_ram >= cfg.emergency_trigger:
            break

    wait_and_restore(cfg, stopped_names)


def wait_and_restore(cfg, stopped_names):
    remaining_tiers = [t for t in cfg.tiers if t["name"] not in stopped_names]

    available_ram = get_available_memory_mb()
    last_log = 0.0

    while available_ram < cfg.safe_recovery:
        if 0 < available_ram < cfg.emergency_trigger and remaining_tiers:
            tier = remaining_tiers.pop(0)
            info(
                f"RAM still critical ({available_ram} MB). "
                f"Escalating to next tier: {tier['type']}:{tier['name']}..."
            )
            available_ram = stop_tier_and_settle(cfg, tier, stopped_names)
            continue

        now = time.monotonic()
        if now - last_log >= RECOVERY_LOG_INTERVAL_SECONDS:
            info(
                f"Waiting for recovery: {available_ram} MB available "
                f"(target: >= {cfg.safe_recovery} MB, stopped: {stopped_names})"
            )
            last_log = now

        time.sleep(CHECK_INTERVAL_SECONDS)
        available_ram = get_available_memory_mb()

    info(
        f"RAM recovered: {available_ram} MB (>= {cfg.safe_recovery} MB). "
        f"Restoring services in reverse order: {list(reversed(stopped_names))}"
    )
    for name in reversed(stopped_names):
        enable_monit_service(name, dry_run=cfg.dry_run)
    if cfg.dry_run:
        info("[DRY-RUN] would clear state file.")
    else:
        clear_state()

    info("Emergency recovery completed. Monit will restart the services.")


def main():
    cfg = parse_args()

    tier_summary = ", ".join(f"{t['type']}:{t['name']}" for t in cfg.tiers)
    mode = "DRY-RUN (no destructive actions will be taken)" if cfg.dry_run else "LIVE"
    info(
        f"RAM Sentinel started [{mode}] | "
        f"Interval: {CHECK_INTERVAL_SECONDS}s | "
        f"Emergency Trigger: < {cfg.emergency_trigger} MB | "
        f"Safe Target: >= {cfg.safe_recovery} MB | "
        f"Tiers: [{tier_summary}]"
    )

    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    except Exception as e:
        info(f"WARNING: cannot create state dir for {STATE_FILE}: {e}")

    validate_tiers(cfg.tiers)

    # Resume an interrupted recovery (skipped in dry-run: state file is live-mode-only)
    if cfg.dry_run:
        info("[DRY-RUN] skipping state file load.")
    else:
        pending = load_state()
        if pending:
            info(f"Found pending state from a previous run: {pending}. Resuming recovery...")
            wait_and_restore(cfg, pending)

    while True:
        try:
            available_ram = get_available_memory_mb()
            if 0 < available_ram < cfg.emergency_trigger:
                run_recovery_routine(cfg)
        except Exception as e:
            info(f"Unexpected error in sentinel loop: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

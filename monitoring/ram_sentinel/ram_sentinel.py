#!/usr/bin/env python3

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime

# === CONSTANTS (same across all environments) ===
CHECK_INTERVAL_SECONDS = 2
RECOVERY_LOG_INTERVAL_SECONDS = 30
STOP_TIMEOUT_SECONDS = 30
# How long to wait for RAM to settle after stopping a tier before escalating
SETTLE_SECONDS = 20
STATE_FILE = "/run/stopram/state.json"

# === NOTIFICATION (populated from CLI args) ===
# "critical" fires on kill/stop actions; "info" also fires on recovery.
_NOTIFY_SCRIPT = ""
_NOTIFY_SERVER_NAME = ""
_NOTIFY_LEVEL = "critical"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "RAM Sentinel: stops services when available RAM drops critically low. "
            "Services are stopped in --tier order and restored in reverse order once RAM recovers."
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
        help="Available RAM (MB) required before restoring services",
    )
    parser.add_argument(
        "--tier",
        action="append",
        dest="tiers",
        metavar="TYPE:NAME",
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
            "and PIDs for real — only skips the destructive commands."
        ),
    )
    parser.add_argument(
        "--notify-script",
        default="",
        metavar="PATH",
        help=(
            "Path to the centralized notification script (empty = disabled). "
            "It is executed directly, so it needs a shebang and execute permission."
        ),
    )
    parser.add_argument(
        "--server-name",
        default="",
        metavar="NAME",
        help="Server label used as MONIT_HOST in notifications (defaults to hostname)",
    )
    parser.add_argument(
        "--notify-level",
        choices=["critical", "all"],
        default="critical",
        help="'critical': only kill/stop events (default). 'all': also recovery events.",
    )

    cfg = parser.parse_args()

    if not cfg.tiers:
        parser.error("At least one --tier is required.")

    cfg.tiers = [_parse_tier(t, parser) for t in cfg.tiers]

    # Notifications were explicitly requested: fail at deploy time rather than
    # running with alerts silently broken.
    if cfg.notify_script and not (
        os.path.isfile(cfg.notify_script) and os.access(cfg.notify_script, os.X_OK)
    ):
        parser.error(
            f"--notify-script '{cfg.notify_script}' does not exist or is not executable "
            f"(it is run directly, so it needs a shebang and execute permission)."
        )
    return cfg


def _parse_tier(raw, parser):
    parts = raw.split(":", 1)
    if len(parts) != 2:
        parser.error(f"Invalid --tier format '{raw}'. Expected TYPE:NAME.")
    tier_type, name = parts
    if tier_type not in ("kill", "stop"):
        parser.error(f"Unknown tier type '{tier_type}'. Must be 'kill' or 'stop'.")
    if not name:
        parser.error(f"Missing name in --tier '{raw}'.")
    return {"type": tier_type, "name": name}


def info(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}", flush=True)


def notify(description, level="critical"):
    """Calls the centralized notification script with MONIT_* env vars, non-fatal.
    level='critical' always fires; level='info' only fires when --notify-level all."""
    if not _NOTIFY_SCRIPT:
        return
    if level == "info" and _NOTIFY_LEVEL != "all":
        return
    try:
        env = os.environ.copy()
        env["MONIT_HOST"] = _NOTIFY_SERVER_NAME
        env["MONIT_SERVICE"] = "RAM-SENTINEL"
        env["MONIT_DESCRIPTION"] = f"[{level.upper()}] {description}"
        # Executed directly: the script must have a shebang and execute permission
        result = subprocess.run(
            [_NOTIFY_SCRIPT],
            env=env,
            timeout=15,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            info(
                f"WARNING: notification script exited with code {result.returncode} "
                f"(non-fatal): {result.stderr.strip()}"
            )
    except Exception as e:
        info(f"WARNING: notification failed (non-fatal): {e}")


def run_cmd(cmd, shell=False, timeout=None):
    try:
        if isinstance(cmd, str) and not shell:
            # shlex keeps quoted arguments together (see shlex.quote at call sites).
            # Monit names shouldn't contain spaces, but this makes it robust anyway.
            cmd = shlex.split(cmd)
        return subprocess.check_output(
            cmd, shell=shell, text=True, timeout=timeout
        ).strip()
    except subprocess.TimeoutExpired:
        info(f"WARNING: command timed out after {timeout}s: {cmd}")
        return None
    except subprocess.CalledProcessError as e:
        info(f"Error executing '{cmd}': {e}")
        return None


def read_mem_available_mb():
    """Reads MemAvailable from /proc/meminfo (no subprocess, so it still works under
    memory pressure). Raises if the value cannot be read."""
    with open("/proc/meminfo", "r") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                # meminfo reports kB
                return int(line.split()[1]) // 1024
    raise RuntimeError("MemAvailable couldn't be found in /proc/meminfo")


def get_available_memory_mb():
    """Same as read_mem_available_mb() but returns 0 on failure, which callers
    treat as critical."""
    try:
        return read_mem_available_mb()
    except Exception as e:
        info(f"Failed to read available memory: {e}")
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
            names.add(parts[0].strip("'\""))
            names.add(parts[1].strip("'\""))
    return names


def validate_tiers(tiers):
    """Returns only the tiers whose name is known to Monit, logging a WARNING for
    each one dropped. Raises RuntimeError if Monit can't be queried, since every
    action goes through Monit and the sentinel would be unable to do anything."""
    known = get_monit_names()
    if not known:
        raise RuntimeError("could not retrieve the service list from 'monit summary'")
    valid = []
    for tier in tiers:
        if tier["name"] in known:
            valid.append(tier)
        else:
            info(
                f"WARNING: tier '{tier['type']}:{tier['name']}' — "
                f"'{tier['name']}' not found in 'monit summary'. Ignoring it; "
                f"check the service name or update --tier."
            )
    return valid


def get_monit_pid(monit_name):
    """Returns the PID reported by Monit for a service, or None."""
    output = run_cmd(f"monit status {shlex.quote(monit_name)}")
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
    while True:
        ram = get_available_memory_mb()
        if ram >= threshold_mb or time.monotonic() >= deadline:
            return ram
        time.sleep(CHECK_INTERVAL_SECONDS)


SNAPSHOT_MEMINFO_KEYS = (
    "MemTotal", "MemFree", "MemAvailable", "Buffers", "Cached", "SwapTotal", "SwapFree",
)


def get_top_processes_by_rss(limit=10):
    """Returns [(pid, rss_kb, name)] sorted by RSS, read from /proc/<pid>/status."""
    procs = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            name, rss_kb = "?", 0
            with open(f"/proc/{entry}/status") as f:
                for line in f:
                    if line.startswith("Name:"):
                        name = line.split(None, 1)[1].strip()
                    elif line.startswith("VmRSS:"):
                        rss_kb = int(line.split()[1])
                        break
            if rss_kb:
                procs.append((int(entry), rss_kb, name))
        except (OSError, ValueError, IndexError):
            # process exited while reading, or kernel thread without VmRSS
            continue
    procs.sort(key=lambda p: p[1], reverse=True)
    return procs[:limit]


def log_system_snapshot():
    """Logs memory stats and top processes reading /proc directly (no subprocess,
    since forking may fail or hang under memory pressure)."""
    try:
        meminfo = {}
        with open("/proc/meminfo") as f:
            for line in f:
                key, _, value = line.partition(":")
                if key in SNAPSHOT_MEMINFO_KEYS:
                    meminfo[key] = int(value.split()[0]) // 1024
        info("Memory snapshot (MB): " + ", ".join(
            f"{k}={meminfo[k]}" for k in SNAPSHOT_MEMINFO_KEYS if k in meminfo
        ))
        lines = [f"{pid:>8} {rss_kb // 1024:>8} MB  {name}"
                 for pid, rss_kb, name in get_top_processes_by_rss()]
        info("Top processes by RSS:\n" + "\n".join(lines))
    except Exception as e:
        info(f"WARNING: system snapshot failed (non-fatal): {e}")


def stop_tier(tier, dry_run=False):
    """Sends the stop/kill action for a single tier.

    Returns (sent, action): sent is True if the signal/request could be delivered.
    It does not mean the service is already down (monit stop is asynchronous)."""
    name = tier["name"]
    quoted_name = shlex.quote(name)
    tier_type = tier["type"]
    sent = False
    action = ""

    if tier_type == "kill":
        pid = get_monit_pid(name)
        if pid is None:
            info(f"Tier kill:{name} — no PID found in monit status. Unmonitoring anyway.")
        elif not pid_is_alive(pid):
            info(f"Tier kill:{name} — PID {pid} no longer alive. Unmonitoring anyway.")
            pid = None
        else:
            info(f"Tier kill:{name} — PID {pid} found and alive.")

        info(f"Tier kill:{name} — unmonitoring...")
        maybe_run(f"monit unmonitor {quoted_name}", dry_run)

        if pid is None:
            action = "no live PID found in monit status, nothing killed"
        else:
            info(f"Tier kill:{name} — sending SIGKILL to PID {pid}...")
            if dry_run:
                info(f"[DRY-RUN] would os.kill({pid}, 9)")
                sent = True
            else:
                try:
                    os.kill(pid, 9)
                    info(f"Tier kill:{name} — SIGKILL sent to PID {pid}.")
                    sent = True
                except Exception as e:
                    info(f"Tier kill:{name} — SIGKILL failed: {e}")
            action = f"SIGKILL sent to PID {pid}" if sent else f"SIGKILL to PID {pid} failed"

    elif tier_type == "stop":
        info(f"Tier stop:{name} — unmonitoring...")
        maybe_run(f"monit unmonitor {quoted_name}", dry_run)
        info(f"Tier stop:{name} — running monit stop...")
        result = maybe_run(f"monit stop {quoted_name}", dry_run, timeout=STOP_TIMEOUT_SECONDS)
        # run_cmd returns None on error/timeout; in dry-run we simulate success
        sent = dry_run or result is not None
        action = "stop request sent to Monit" if sent else "monit stop failed"

    if dry_run:
        info(f"[DRY-RUN] would sleep 3s for OS to reclaim memory.")
    else:
        time.sleep(3)

    return sent, action


def restore_tier(tier, dry_run=False):
    """Re-enables Monit tracking so Monit restarts the service."""
    name = tier["name"]
    info(f"Re-enabling Monit tracking for '{name}'...")
    maybe_run(f"monit monitor {shlex.quote(name)}", dry_run)


def save_state(stopped_tiers, dry_run=False):
    if dry_run:
        info(f"[DRY-RUN] would persist state: {[t['type']+':'+t['name'] for t in stopped_tiers]}")
        return
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        tmp_file = STATE_FILE + ".tmp"
        with open(tmp_file, "w") as f:
            json.dump(
                {
                    "stopped_tiers": stopped_tiers,
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
            data = json.load(f)
        # New format: list of {"type": ..., "name": ...} dicts
        if "stopped_tiers" in data:
            return data["stopped_tiers"]
        # Old format: list of name strings under "stopped_services"
        return [{"type": "stop", "name": n} for n in data.get("stopped_services", [])]
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


def stop_tier_and_settle(cfg, tier, stopped_tiers, trigger_ram=None):
    """Stops a tier, persists state, waits for RAM to settle. Returns updated available RAM."""
    name = tier["name"]

    save_state(stopped_tiers + [tier], dry_run=cfg.dry_run)
    sent, action = stop_tier(tier, dry_run=cfg.dry_run)
    # Recorded even if it failed: it was unmonitored, so it must be re-monitored on restore
    stopped_tiers.append(tier)
    save_state(stopped_tiers, dry_run=cfg.dry_run)

    ram_after = get_available_memory_mb()
    ram_info = (
        f"RAM at trigger: {trigger_ram} MB → after stop: {ram_after} MB."
        if trigger_ram is not None
        else f"RAM after stop: {ram_after} MB."
    )
    status = action if sent else f"FAILED: {action}"
    notify(f"{tier['type'].upper()} {name}: {status}. {ram_info}")

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

    stopped_tiers = []

    for tier in cfg.tiers:
        available_ram = stop_tier_and_settle(cfg, tier, stopped_tiers, trigger_ram=available_ram)
        if available_ram >= cfg.emergency_trigger:
            break

    wait_and_restore(cfg, stopped_tiers)


def wait_and_restore(cfg, stopped_tiers):
    stopped_names = {t["name"] for t in stopped_tiers}
    remaining_tiers = [t for t in cfg.tiers if t["name"] not in stopped_names]

    available_ram = get_available_memory_mb()
    last_log = 0.0

    while available_ram < cfg.safe_recovery:
        if available_ram < cfg.emergency_trigger and remaining_tiers:
            tier = remaining_tiers.pop(0)
            info(
                f"RAM still critical ({available_ram} MB). "
                f"Escalating to next tier: {tier['type']}:{tier['name']}..."
            )
            available_ram = stop_tier_and_settle(cfg, tier, stopped_tiers, trigger_ram=available_ram)
            stopped_names.add(tier["name"])
            continue

        now = time.monotonic()
        if now - last_log >= RECOVERY_LOG_INTERVAL_SECONDS:
            info(
                f"Waiting for recovery: {available_ram} MB available "
                f"(target: >= {cfg.safe_recovery} MB, "
                f"stopped: {[t['type']+':'+t['name'] for t in stopped_tiers]})"
            )
            last_log = now

        time.sleep(CHECK_INTERVAL_SECONDS)
        available_ram = get_available_memory_mb()

    restored = [f"{t['type']}:{t['name']}" for t in reversed(stopped_tiers)]
    info(
        f"RAM recovered: {available_ram} MB (>= {cfg.safe_recovery} MB). "
        f"Restoring services in reverse order: {restored}"
    )
    for tier in reversed(stopped_tiers):
        restore_tier(tier, dry_run=cfg.dry_run)
    if cfg.dry_run:
        info("[DRY-RUN] would clear state file.")
    else:
        clear_state()

    info("Emergency recovery completed.")
    notify(
        f"RAM recovered to {available_ram} MB. Services restored: {', '.join(restored)}.",
        level="info",
    )


def main():
    global _NOTIFY_SCRIPT, _NOTIFY_SERVER_NAME, _NOTIFY_LEVEL

    cfg = parse_args()
    _NOTIFY_SCRIPT = cfg.notify_script
    _NOTIFY_SERVER_NAME = cfg.server_name or os.uname().nodename
    _NOTIFY_LEVEL = cfg.notify_level

    tier_summary = ", ".join(f"{t['type']}:{t['name']}" for t in cfg.tiers)
    mode = "DRY-RUN (no destructive actions will be taken)" if cfg.dry_run else "LIVE"
    notify_status = "disabled" if not _NOTIFY_SCRIPT else f"enabled (level={_NOTIFY_LEVEL})"
    info(
        f"RAM Sentinel started [{mode}] | "
        f"Interval: {CHECK_INTERVAL_SECONDS}s | "
        f"Emergency Trigger: < {cfg.emergency_trigger} MB | "
        f"Safe Target: >= {cfg.safe_recovery} MB | "
        f"Tiers: [{tier_summary}] | "
        f"Notifications: {notify_status}"
    )

    # A failed read is treated as 0 MB (critical) at runtime. If it already fails
    # at startup it is a platform problem (no /proc, kernel < 3.14 without
    # MemAvailable), and running would stop every tier and never restore them.
    try:
        read_mem_available_mb()
    except Exception as e:
        info(f"FATAL: cannot read available memory from /proc/meminfo: {e}. Refusing to start.")
        sys.exit(1)

    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    except Exception as e:
        info(f"WARNING: cannot create state dir for {STATE_FILE}: {e}")

    # Drop unknown tiers so recovery doesn't waste time on them, and refuse to
    # start if nothing is left: a sentinel that can't act would give false confidence.
    try:
        cfg.tiers = validate_tiers(cfg.tiers)
    except Exception as e:
        info(f"FATAL: cannot validate tiers against Monit: {e}. Refusing to start.")
        sys.exit(1)
    if not cfg.tiers:
        info("FATAL: none of the configured tiers exist in Monit. Refusing to start.")
        sys.exit(1)
    info(f"Active tiers: [{', '.join(t['type'] + ':' + t['name'] for t in cfg.tiers)}]")

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
            if available_ram < cfg.emergency_trigger:
                run_recovery_routine(cfg)
        except Exception as e:
            info(f"Unexpected error in sentinel loop: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

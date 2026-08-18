# RAM Sentinel

A daemon that monitors available RAM and stops Monit-managed services when memory drops critically low, then restores them once RAM recovers. Designed to prevent OOM kills on servers running Java/Tomcat and PostgreSQL.

## How it works

1. Polls available RAM every 2 seconds via `free -m`.
2. When RAM drops below `--emergency-trigger`, stops services in the order defined by `--tier`.
3. Waits up to 20 seconds after each tier for RAM to settle before escalating to the next one.
4. Once all necessary services are stopped, waits for RAM to reach `--safe-recovery`.
5. Restores services in reverse order by handing them back to Monit (`monit monitor`).
6. Persists state to `/run/stopram/state.json` so an interrupted recovery is resumed on restart.

## Tier types

| Type | Behaviour |
|------|-----------|
| `kill` | Reads the PID from `monit status`, unmonitors the service, then sends SIGKILL. Fast — use for Java/Tomcat. |
| `stop` | Unmonitors the service, then runs `monit stop`. Clean shutdown — use for PostgreSQL or any service with a stop program defined in monitrc. |

## Usage

```
ram_sentinel.py --emergency-trigger MB --safe-recovery MB --tier TYPE:MONIT_NAME [--tier ...] [--dry-run]
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--emergency-trigger MB` | yes | Available RAM (MB) that triggers emergency actions |
| `--safe-recovery MB` | yes | Available RAM (MB) required before restoring services |
| `--tier TYPE:MONIT_NAME` | yes (repeat) | Service to stop, in escalation order |
| `--dry-run` | no | Simulate all actions — reads RAM and PIDs for real, skips destructive commands |

## Dry-run mode

Use `--dry-run` to validate config before deploying:

```bash
python3 ram_sentinel.py \
  --emergency-trigger 4000 \
  --safe-recovery 8000 \
  --tier kill:my_tomcat_service \
  --tier stop:my_postgres_service \
  --dry-run
```

Since nothing actually stops, RAM never recovers — the sentinel cycles repeatedly. Ctrl-C when satisfied. This validates argument parsing, Monit name resolution, and PID reads, but not the actual stop/restore flow.

## Deployment

### 1. Copy the script

```bash
cp ram_sentinel.py /usr/local/bin/ram_sentinel.py
chmod +x /usr/local/bin/ram_sentinel.py
```

### 2. Create the systemd service

Copy `ram_sentinel_example.service` to `/etc/systemd/system/ram-sentinel.service` and adjust the `ExecStart` line for your environment:

```ini
ExecStart=/usr/bin/python3 /usr/local/bin/ram_sentinel.py \
  --emergency-trigger 4000 \
  --safe-recovery 8000 \
  --tier kill:my_tomcat_service \
  --tier stop:my_postgres_service
```

Set thresholds based on your server's total RAM. A reasonable rule of thumb:
- `--emergency-trigger`: ~12–15% of total RAM
- `--safe-recovery`: ~25–30% of total RAM

### 3. Enable and start

```bash
systemctl daemon-reload
systemctl enable ram-sentinel
systemctl start ram-sentinel
journalctl -u ram-sentinel -f
```

## Verifying Monit service names

Service names passed to `--tier` must match exactly what `monit summary` shows:

```bash
monit summary
```

At startup, the sentinel logs a WARNING for any tier name not found in Monit — check `journalctl -u ram-sentinel` after the first start.

## Prerequisites

- Python 3
- Monit running and managing the target services
- Services must have a `stop program` defined in monitrc to use the `stop` tier type
- Root privileges (required for SIGKILL and monit commands)

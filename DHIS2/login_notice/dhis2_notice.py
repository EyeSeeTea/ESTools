#!/usr/bin/env python3
"""Put a maintenance notice on top of the DHIS2 login notice, and remove it later.

The notice lives in the system setting `keyApplicationNotification`.

    dhis2_notice.py apply notices/2026-11-13-dev.json   # validate, show summary, ask y/N, publish
    dhis2_notice.py check dev                           # read-only: credentials + current values
    dhis2_notice.py status                              # list jobs
    dhis2_notice.py restore [job]                       # restore now (all open jobs if no id)
    dhis2_notice.py tick                                # for cron (hourly): restore expired jobs

`apply` prepends the notice file's HTML to the message on each server (default text and
the `en` translation). When the notice's `end` has passed, `tick` removes exactly that
block again. Standard library only. Files: servers.json, credentials file (tokens),
notices/*.json (+ .html).
"""
import argparse
import base64
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import error, parse, request
from zoneinfo import ZoneInfo

SETTING = "keyApplicationNotification"
HERE = Path(__file__).resolve().parent
HOME = Path(os.environ.get("DHIS2_NOTICE_HOME", HERE / "state")).expanduser()  # jobs + log live next to the script
JOBS = HOME / "jobs"
OPEN_STATUSES = ("active", "restore_failed")
LOCALES = ("en",)  # translations written besides the default text; "locales" in servers.json overrides


def log(msg):
    """Print and append to the log file with a timestamp. Only actions, never credentials."""
    print(msg)
    try:
        HOME.mkdir(parents=True, exist_ok=True)
        with open(HOME / "notice.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg.strip()}\n")
    except OSError as e:
        print(f"warning: cannot write log: {e}", file=sys.stderr)


def log_change(verb, srv, targets):
    """Log which URL changed and the exact text added/removed, one line per distinct text.

    targets: [(where, message)], where is "default" or a language code."""
    by_text = {}
    for where, message in targets:
        by_text.setdefault(" ".join(message.split()), []).append(where)
    for text, places in by_text.items():
        log(f"{srv.key} {srv.url} {verb} [{', '.join(places)}]: {text}")


def die(msg):
    sys.exit(f"error: {msg}")


# ---------- configuration ----------

def load_json(path, what):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        die(f"cannot read {what} {path}: {e}")


def load_passwords(args, cfg):
    """Credentials file: --passwords, else "passwords_file" in servers.json, else ./.passwords.

    Lines are KEY=VALUE (quotes optional, `export ` allowed), parsed here instead of
    sourced by the shell, so $ ! and quotes in values are safe.
    """
    explicit = args.passwords or cfg.get("passwords_file")
    p = Path(explicit).expanduser() if explicit else HERE / ".passwords"
    if not p.exists():
        die(f"passwords file {p} not found")
    if p.stat().st_mode & 0o007:  # readable by "others"
        print(f"warning: {p} is readable by everyone, run: chmod 600 {p}", file=sys.stderr)
    out = {}
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            die(f"{p}:{n}: expected KEY=VALUE")
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        out[k.strip()] = v
    return out


def resolve_servers(cfg, names):
    """Expand group names into server keys, validating each one."""
    keys = []
    for n in names:
        for k in cfg.get("groups", {}).get(n, [n]):
            if k not in cfg["servers"]:
                die(f"unknown server or group '{n}'")
            keys.append(k)
    return list(dict.fromkeys(keys))


# ---------- DHIS2 API ----------

class Server:
    def __init__(self, key, spec, passwords):
        self.key = key
        self.url = spec["url"].rstrip("/")
        self.base = self.url + "/api"
        if spec.get("api_version"):
            self.base += f"/{spec['api_version']}"
        # Credentials come from the passwords file. "credentials_key" (default: the server key)
        # names one entry whose value is detected: "d2pat_..." is a token, "user:password" is
        # basic auth. "userVar;passwordVar" names two entries (user and password) instead.
        ck = spec.get("credentials_key", key)
        if ";" in ck:
            u, p = (x.strip() for x in ck.split(";", 1))
            if not (passwords.get(u) and passwords.get(p)):
                die(f"{key}: '{u}' and '{p}' must both be in the passwords file")
            self.kind, self.source, self.secret = "basic", f"{u};{p}", f"{passwords[u]}:{passwords[p]}"
        else:
            name = next((n for n in (ck, f"{ck}_PAT", f"{ck}_BASIC") if passwords.get(n)), None)
            if not name:
                die(f"{key}: '{ck}' not found in the passwords file "
                    f"(value: a d2pat_ token or user:password, or set \"credentials_key\")")
            value = passwords[name]
            self.kind = "pat" if value.startswith("d2pat_") or ":" not in value else "basic"
            self.source, self.secret = name, value

    def headers(self):
        h = {"Accept": "*/*", "X-Requested-With": "XMLHttpRequest"}
        if self.kind == "pat":
            h["Authorization"] = "ApiToken " + self.secret
        else:
            h["Authorization"] = "Basic " + base64.b64encode(self.secret.encode()).decode()
        return h

    def call(self, method, path, params=None, body=None):
        url = self.base + path
        if params:
            url += "?" + parse.urlencode(params, quote_via=parse.quote)
        data = None
        headers = self.headers()
        if body is not None:
            data = body.encode("utf-8")
            headers["Content-Type"] = "text/plain"
        elif method == "POST":
            data = b""
        req = request.Request(url, data=data, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
        except error.URLError as e:
            raise RuntimeError(f"{self.key}: {e.reason}")

    def get_setting(self, locale=None):
        """Stored text, or "" when the setting is empty or missing."""
        status, text = self.call("GET", f"/systemSettings/{SETTING}",
                                 {"locale": locale} if locale else None)
        if status == 404:
            return ""
        if status != 200:
            raise RuntimeError(f"{self.key}: GET {SETTING} -> HTTP {status}: {text[:200]}")
        # some DHIS2 versions answer {"keyApplicationNotification": "<text>"}, others the bare text
        try:
            data = json.loads(text)
        except ValueError:
            return text
        if isinstance(data, dict) and isinstance(data.get(SETTING), str):
            return data[SETTING]
        return text

    def set_setting(self, value, locale=None):
        if locale:
            status, text = self.call("POST", f"/systemSettings/{SETTING}",
                                     {"value": value, "locale": locale})
        else:
            status, text = self.call("POST", f"/systemSettings/{SETTING}", body=value)
        if status not in (200, 201):
            raise RuntimeError(f"{self.key}: set {SETTING} locale={locale or 'default'} -> HTTP {status}: {text[:200]}")

    def read_all(self, locales=None):
        return {"default": self.get_setting(),
                "locales": {l: self.get_setting(l) for l in (LOCALES if locales is None else locales)}}


def make_server(cfg, key, passwords):
    return Server(key, cfg["servers"][key], passwords)


# ---------- jobs / state ----------

def job_path(job_id):
    return JOBS / f"{job_id}.json"


def load_job(job_id):
    try:
        return json.loads(job_path(job_id).read_text())
    except OSError:
        die(f"job '{job_id}' not found (see: status)")


def save_job(job):
    JOBS.mkdir(parents=True, exist_ok=True)
    tmp = job_path(job["id"]).with_suffix(".tmp")
    tmp.write_text(json.dumps(job, indent=2, ensure_ascii=False))
    tmp.replace(job_path(job["id"]))


def all_jobs():
    return [json.loads(p.read_text()) for p in sorted(JOBS.glob("*.json"))] if JOBS.exists() else []


def preview(text, n=160):
    flat = " ".join(text.split())
    return (flat[:n] + "...") if len(flat) > n else (flat or "(empty)")


# ---------- notice validation ----------

def parse_time(text, tz, field):
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    except (ValueError, TypeError):
        die(f"'{field}' must look like 'YYYY-MM-DD HH:MM', got {text!r}")


def load_notice(path, cfg, minutes=None):
    path = Path(path)
    n = load_json(path, "notice")
    for field in ("servers", "end", "message_file"):
        if not n.get(field):
            die(f"notice is missing '{field}'")
    if not isinstance(n["servers"], list):
        die("'servers' must be a list of server keys or group names")
    tz = ZoneInfo(cfg.get("timezone", "Europe/Madrid"))
    end = parse_time(n["end"], tz, "end")
    if minutes:  # test mode: ignore the file's date, end N minutes from now
        end = (datetime.now(tz) + timedelta(minutes=minutes)).replace(second=0, microsecond=0)
    if end <= datetime.now(timezone.utc):
        die("'end' is already in the past")
    def read_message(name):
        f = path.parent / name
        try:
            text = f.read_text(encoding="utf-8").strip()
        except OSError as e:
            die(f"cannot read message file {f}: {e}")
        if not text:
            die(f"message file {f} is empty")
        return text + "\n\n"  # published as written, blank line before the existing text

    text = read_message(n["message_file"])
    if n.get("locale"):  # a notice for one language only: its own text, default text untouched
        message, by_locale = None, {n["locale"]: text}
    else:  # default text, plus the languages in servers.json "locales" with the same text
        message, by_locale = text, {l: text for l in LOCALES}
    return {"servers": resolve_servers(cfg, n["servers"]), "end": end, "message": message,
            "by_locale": by_locale, "tz": str(tz), "path": path}


# ---------- actions ----------

def remove_block(current, message):
    """Remove our notice from a stored text, tolerating whitespace changes made by the server.

    Returns the new text, or None when the notice is not there.
    """
    core = message.strip()
    i = current.find(core)
    if i < 0:
        return None
    j = i + len(core)
    while j < len(current) and current[j] in " \t\r\n":  # the blank line we added after it
        j += 1
    return current[:i] + current[j:]


def unwrap(text):
    """Undo a JSON envelope {"keyApplicationNotification": "<text>"} stored as the message
    by an earlier version that did not parse the API response. Plain text is returned as is."""
    try:
        data = json.loads(text)
    except ValueError:
        return text
    if isinstance(data, dict) and set(data) == {SETTING} and isinstance(data[SETTING], str):
        return data[SETTING]
    return text


def publish(job, cfg, passwords):
    failed = 0
    for key, entry in job["servers"].items():
        if entry["state"] != "pending":
            continue
        written = False
        try:
            srv = make_server(cfg, key, passwords)
            by_locale = job.get("by_locale", {})
            current = srv.read_all(by_locale)
            entry["state"] = "applying"
            save_job(job)
            if job["message"]:
                srv.set_setting(job["message"] + current["default"])
                written = True
            for l, msg in by_locale.items():
                srv.set_setting(msg + (current["locales"][l] or current["default"]), l)
                written = True
            checked = job["message"] or next(iter(by_locale.values()))
            where = None if job["message"] else next(iter(by_locale))
            if checked.strip() not in srv.get_setting(where):
                raise RuntimeError(f"{key}: published text was not read back")
            entry["state"] = "applied"
            log_change("ADDED", srv, ([("default", job["message"])] if job["message"] else [])
                       + list(by_locale.items()))
        except Exception as e:
            entry["error"] = str(e)
            if not written:
                entry["state"] = "failed"  # nothing was written, nothing to undo
            failed += 1
            log(f"{key}: FAILED {e}")
        save_job(job)
    touched = any(e["state"] in ("applied", "applying") for e in job["servers"].values())
    job["status"] = "active" if touched else "failed"
    save_job(job)
    return 1 if failed else 0


def restore(job, cfg, passwords):
    failed = 0
    for key, entry in job["servers"].items():
        if entry["state"] not in ("applied", "applying"):
            continue
        try:
            srv = make_server(cfg, key, passwords)
            # remove exactly the block we added; anything else on the server is left alone
            targets = [(None, job["message"])] if job["message"] else []
            removed = []
            for locale, message in targets + list(job.get("by_locale", {}).items()):
                current = srv.get_setting(locale)
                cleaned = remove_block(current, message)
                if cleaned is not None:
                    srv.set_setting(unwrap(cleaned), locale)
                    removed.append((locale or "default", message))
                else:
                    log(f"{key}: notice block not found ({locale or 'default'}), left untouched")
            entry["state"] = "restored"
            entry.pop("error", None)
            if removed:
                log_change("REMOVED", srv, removed)
            else:
                log(f"{srv.key} {srv.url} restored: nothing to remove")
        except Exception as e:
            entry["error"] = str(e)
            failed += 1
            log(f"{key}: RESTORE FAILED {e}")
        save_job(job)
    job["status"] = "restore_failed" if failed else "finished"
    save_job(job)
    return 1 if failed else 0


# ---------- commands ----------

def cmd_apply(args, cfg):
    notice = load_notice(args.notice, cfg, args.minutes)
    passwords = load_passwords(args, cfg)
    servers = {k: make_server(cfg, k, passwords) for k in notice["servers"]}  # checks credentials exist

    def targets(msg, by_locale):  # what a notice writes: the default text and/or languages
        return ({"default"} if msg else set()) | set(by_locale)

    mine = targets(notice["message"], notice["by_locale"])
    clash = sorted({k for j in all_jobs() if j["status"] in OPEN_STATUSES for k in j["servers"]
                    if k in servers and targets(j["message"], j.get("by_locale", {})) & mine})
    if clash:
        die(f"these servers already have an active notice for the same text/language: "
            f"{', '.join(clash)} (restore it first: status / restore <job>)")

    print(f"Ends: {notice['end']:%Y-%m-%d %H:%M} ({notice['tz']})")
    print("New message (goes on top of the current one):")
    if notice["message"]:
        print(f"  default: {preview(notice['message'], 400)}")
    for l, m in notice["by_locale"].items():
        print(f"  {l}: {'(same as default)' if m == notice['message'] else preview(m, 400)}")
    print()
    print("Reading current messages...")
    current = {}
    for k, srv in servers.items():
        try:
            current[k] = srv.read_all()
        except Exception as e:
            die(f"{e}")
        print(f"  {k} ({srv.base}): {preview(current[k]['default'])}")

    if args.dry_run:
        print("\ndry run: nothing changed")
        return 0
    if not args.yes and input(f"\nPublish on {len(servers)} server(s)? [y/N] ").strip().lower() != "y":
        log("apply aborted by user")
        return 1

    job = {"id": f"{notice['end']:%Y%m%d-%H%M}-{uuid.uuid4().hex[:4]}", "status": "pending",
           "notice_file": str(notice["path"]), "message": notice["message"],
           "end": notice["end"].isoformat(),
           "by_locale": notice["by_locale"], "servers": {k: {"state": "pending"} for k in servers}}
    save_job(job)
    log(f"job {job['id']}: publishing on {', '.join(servers)}, ends {notice['end']:%Y-%m-%d %H:%M}")
    rc = publish(job, cfg, passwords)
    if job["status"] == "failed":
        print("nothing was published")
        return rc
    print(f"The notice file stays in place. It will be reverted by 'tick' after {notice['end']:%Y-%m-%d %H:%M}.")
    return rc


def cmd_tick(args, cfg):
    now = datetime.now(timezone.utc)
    due = [j for j in all_jobs()
           if j["status"] in OPEN_STATUSES and datetime.fromisoformat(j["end"]) <= now]
    if not due:
        return 0
    passwords = load_passwords(args, cfg)
    rc = 0
    for j in due:
        log(f"job {j['id']}: ended, restoring")
        rc |= restore(j, cfg, passwords)
    return rc


def cmd_restore(args, cfg):
    jobs = [load_job(args.job)] if args.job else [j for j in all_jobs() if j["status"] in OPEN_STATUSES]
    if not jobs:
        print("no open jobs, nothing to restore")
        return 0
    passwords = load_passwords(args, cfg)
    rc = 0
    for job in jobs:
        if job["status"] not in OPEN_STATUSES:
            die(f"job is '{job['status']}', nothing to restore")
        log(f"job {job['id']}: manual restore")
        rc |= restore(job, cfg, passwords)
    return rc


def cmd_status(args, cfg):
    for j in all_jobs():
        states = ", ".join(f"{k}={e['state']}" for k, e in j["servers"].items())
        print(f"{j['id']}  {j['status']:<15} ends {j['end']}\n    {states}")
    return 0


def cmd_check(args, cfg):
    """Read-only: verify credentials and show the current values."""
    passwords = load_passwords(args, cfg)
    rc = 0
    for key in resolve_servers(cfg, args.servers):
        try:
            srv = make_server(cfg, key, passwords)
            print(f"{key}: using {srv.kind} from '{srv.source}' ({len(srv.secret)} chars)")
            data = srv.read_all()
            print(f"{key}: OK\n    default: {preview(data['default'])}")
            print(f"    apply writes: default{''.join(', ' + l for l in LOCALES)}")
        except Exception as e:
            rc = 1
            print(f"{key}: FAILED {e}")
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", default=str(HERE / "servers.json"))
    ap.add_argument("--passwords", help="credentials file (default: \"passwords_file\" in servers.json, else ./.passwords)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("apply", help="validate a notice file, confirm, publish")
    p.add_argument("notice")
    p.add_argument("--dry-run", action="store_true", help="validate and read, change nothing")
    p.add_argument("--minutes", type=int, help="test: end N minutes from now (ignores the file's end)")
    p.add_argument("--yes", action="store_true", help="skip the y/N question")
    p.set_defaults(fn=cmd_apply)

    p = sub.add_parser("check", help="read-only: test credentials, show current messages")
    p.add_argument("servers", nargs="+", help="server keys or group names")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("tick", help="for cron: restore jobs whose end has passed")
    p.set_defaults(fn=cmd_tick)

    p = sub.add_parser("restore", help="restore now, before the end (one job, or all open jobs if no id)")
    p.add_argument("job", nargs="?")
    p.set_defaults(fn=cmd_restore)

    p = sub.add_parser("status", help="list jobs")
    p.set_defaults(fn=cmd_status)

    args = ap.parse_args()
    cfg = load_json(args.config, "config")
    clash = set(cfg.get("groups", {})) & set(cfg.get("servers", {}))
    if clash:
        die(f"a group and a server share the name {', '.join(sorted(clash))}: rename one of them")
    global LOCALES
    LOCALES = tuple(cfg.get("locales", LOCALES))  # [] = write only the default text
    sys.exit(args.fn(args, cfg))


if __name__ == "__main__":
    main()

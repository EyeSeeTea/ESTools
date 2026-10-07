#!/usr/bin/env python3
"""
Copy DHIS2 events (with IMAGE / FILE_RESOURCE data values) from one instance to another.

Phases (each one resumable, nothing touches the destination until `upload` without --dry-run):

  1. events   Download events for every (program x orgUnit) pair, filtered by date, paginated.
              Only events. No files. This is the "dry run" of the download: it writes
              report.json and FAILS if any event is outside the allowed programs/orgUnits,
              or if a program has events in org units that are not in the list (--allow-partial
              to only warn).
  2. files    Download the files of the file-type data values of the events saved in phase 1.
  3. verify   Offline checks: server totals vs. events on disk, no duplicates, every file value
              has a non-empty file on disk.
  4. upload   --dry-run : checks that programs/orgUnits exist in destination and runs the tracker
                          import with importMode=VALIDATE (file values stripped, nothing stored).
              (no flag) : uploads files as fileResources (domain=DATA_VALUE), replaces the ids in
                          the dataValues and imports the events.

Auth: session cookie. Log in with the browser, copy the JSESSIONID cookie value and export
      SRC_JSESSIONID / DST_JSESSIONID. (Cookie scope: the cookie is for the DHIS2 context path.)

Assumes same UIDs for program / stages / data elements / org units in both instances.

Example:
  export SRC_JSESSIONID=... DST_JSESSIONID=...
  P="--programs-file programs.txt --org-units-file orgunits.txt --out ./dump"
  python sync_events_with_files.py events --src https://extranet.who.int/dhis2 $P --after 2020-01-01 --before 2026-10-02
  python sync_events_with_files.py files  --src https://extranet.who.int/dhis2 --out ./dump
  python sync_events_with_files.py verify --out ./dump
  python sync_events_with_files.py upload --dst https://dev.server/dhis2 --out ./dump --dry-run
  python sync_events_with_files.py upload --dst https://dev.server/dhis2 --out ./dump
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests

PAGE_SIZE = 250
CONFIG = {}
DEFAULT_CONFIG = Path(__file__).parent / "events_sync.config.json"
FILE_TYPES = ("IMAGE", "FILE_RESOURCE")


# ----------------------------------------------------------------------------- helpers
def session(prefix, base):
    s = requests.Session()
    jsid = os.environ.get(f"{prefix}_JSESSIONID") or CONFIG.get(prefix.lower(), {}).get("jsessionid")
    if not jsid or jsid.startswith("PUT_"):
        sys.exit(f"Set {prefix}_JSESSIONID or fill {prefix.lower()}.jsessionid in the config file")
    s.cookies.set("JSESSIONID", jsid)
    s.headers["Accept"] = "application/json"
    # fail fast if the session is not valid (an expired session returns the login page, not 401)
    r = s.get(f"{api(base)}/me", params={"fields": "username"}, allow_redirects=False)
    if r.status_code != 200 or "json" not in r.headers.get("Content-Type", ""):
        sys.exit(f"{prefix} session not valid (HTTP {r.status_code}). Refresh the JSESSIONID.")
    print(f"[{prefix}] logged in as {r.json()['username']}")
    return s


def api(base):
    return base.rstrip("/") + "/api"


def read_list(csv, path):
    items = []
    if csv:
        items += [x.strip() for x in csv.split(",")]
    if path:
        items += [l.strip() for l in Path(path).read_text().splitlines() if l.strip() and not l.startswith("#")]
    seen = []
    for i in items:
        if i and i not in seen:
            seen.append(i)
    return seen


def extract_events(page):
    return page.get("events") or page.get("instances") or []  # 2.41 / 2.40


def safe(name):
    return name.replace("/", "_")


def load_json(path, default):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def iter_events(out):
    for f in sorted((Path(out) / "events").glob("*.json")):
        for ev in json.loads(f.read_text()):
            yield f, ev


# ----------------------------------------------------------------------------- 1. events
def cmd_events(a):
    s = session("SRC", a.src)
    programs = read_list(a.programs, a.programs_file)
    org_units = read_list(a.org_units, a.org_units_file)
    if not programs or not org_units:
        sys.exit("Need at least one program and one org unit")

    out = Path(a.out)
    (out / "events").mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps({"programs": programs, "orgUnits": org_units}))
    report = load_json(out / "report.json", {})
    allowed_p, allowed_ou = set(programs), set(org_units)
    violations = []

    for program in programs:
        for ou in org_units:
            key = f"{program}__{ou}"
            if report.get(key, {}).get("done"):
                print(f"{key}: already done, skipping")
                continue
            params = {
                "program": program,
                "orgUnit": ou,
                "ouMode": a.ou_mode,  # SELECTED: exactly the org units given, no descendants
                "occurredAfter": a.after,
                "occurredBefore": a.before,
                "pageSize": PAGE_SIZE,
                "totalPages": "true",
                "fields": "*",
            }
            page, got, server_total, uids = 1, 0, None, set()
            while True:
                r = s.get(f"{api(a.src)}/tracker/events", params={**params, "page": page})
                r.raise_for_status()
                body = r.json()
                events = extract_events(body)
                if server_total is None:
                    server_total = body.get("total")
                if not events:
                    break
                for ev in events:
                    if ev.get("program") not in allowed_p or ev.get("orgUnit") not in allowed_ou:
                        violations.append((ev.get("event"), ev.get("program"), ev.get("orgUnit")))
                    uids.add(ev["event"])
                (out / "events" / f"{key}__p{page:05d}.json").write_text(json.dumps(events))
                got += len(events)
                print(f"{key} page {page}/{body.get('pageCount', '?')}: {len(events)} events", flush=True)
                if body.get("pageCount") and page >= body["pageCount"]:
                    break
                page += 1
            report[key] = {"done": True, "downloaded": got, "unique": len(uids), "serverTotal": server_total}
            (out / "report.json").write_text(json.dumps(report, indent=2))

    print("\n=== Report (program__orgUnit: downloaded / serverTotal) ===")
    for k, v in report.items():
        print(f"  {k}: {v['downloaded']} / {v['serverTotal']}")
    if violations:
        print(f"\n!!! {len(violations)} events OUTSIDE the allowed programs/orgUnits (first 10):")
        for v in violations[:10]:
            print("   ", v)
        sys.exit(1)
    print("\nOK: all events inside the allowed programs and org units.")

    missing = program_coverage(s, a, programs, out)
    if missing and not a.allow_partial:
        print("Add the org units of the missing events to orgUnits, or use --allow-partial if this is intended.")
        sys.exit(1)


def program_server_total(s, a, program):
    """Events of the program in the source, in every org unit the user can access, same date filter."""
    params = {
        "program": program,
        "ouMode": "ACCESSIBLE",
        "occurredAfter": a.after,
        "occurredBefore": a.before,
        "pageSize": 1,
        "totalPages": "true",
        "fields": "event",
    }
    r = s.get(f"{api(a.src)}/tracker/events", params=params)
    r.raise_for_status()
    body = r.json()
    return body.get("total", (body.get("pager") or {}).get("total"))  # 2.41 / 2.40


def program_coverage(s, a, programs, out):
    """
    The org unit list may leave out some of the org units where a program has events
    (e.g. org units outside the EUR branch). Those events are never requested, so the
    checks above cannot see them. Compare the program total in the source with the
    unique events on disk.
    """
    on_disk = {}
    for _, ev in iter_events(out):
        on_disk.setdefault(ev.get("program"), set()).add(ev["event"])

    print("\n=== Coverage (program: on disk / total in source for all accessible org units) ===")
    missing = []
    for program in programs:
        total = program_server_total(s, a, program)
        got = len(on_disk.get(program, set()))
        flag = "OK " if total is not None and got >= total else "BAD"
        print(f"  {flag} {program}: {got} / {total}")
        if flag == "BAD":
            missing.append((program, got, total))
    if missing:
        print(f"\n!!! {len(missing)} programs have events in org units that are not in orgUnits.")
    else:
        print("\nOK: every event of the programs was downloaded.")
    return missing


# ----------------------------------------------------------------------------- 2. files
def file_data_elements(s, base):
    r = s.get(
        f"{api(base)}/dataElements",
        params={"filter": f"valueType:in:[{','.join(FILE_TYPES)}]", "fields": "id", "paging": "false"},
    )
    r.raise_for_status()
    return {d["id"] for d in r.json()["dataElements"]}


def download_file(s, base, event_uid, de_uid, dest):
    urls = [
        f"{api(base)}/tracker/events/{event_uid}/dataValues/{de_uid}/file",  # >= 2.40
        f"{api(base)}/events/files?eventUid={event_uid}&dataElementUid={de_uid}",  # legacy
    ]
    for url in urls:
        r = s.get(url, stream=True, headers={"Accept": "*/*"})
        if r.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
            return r.headers.get("Content-Type", "application/octet-stream")
        if r.status_code != 404:
            r.raise_for_status()
    raise RuntimeError("file not found")


def cmd_files(a):
    s = session("SRC", a.src)
    out = Path(a.out)
    (out / "files").mkdir(exist_ok=True)
    file_des = file_data_elements(s, a.src)
    manifest = load_json(out / "files_manifest.json", {})
    failed = []

    for _, ev in iter_events(out):
        for dv in ev.get("dataValues", []):
            if dv["dataElement"] not in file_des or not dv.get("value"):
                continue
            key = f"{ev['event']}__{dv['dataElement']}"
            dest = out / "files" / safe(key)
            if key in manifest and dest.exists() and dest.stat().st_size > 0:
                continue
            try:
                ct = download_file(s, a.src, ev["event"], dv["dataElement"], dest)
                manifest[key] = {"contentType": ct, "size": dest.stat().st_size}
                print(f"{key}: {manifest[key]['size']} bytes ({ct})", flush=True)
            except Exception as e:  # keep going, report at the end
                failed.append((key, str(e)))
            (out / "files_manifest.json").write_text(json.dumps(manifest))

    print(f"\nFiles on disk: {len(manifest)}; failed: {len(failed)}")
    for k, e in failed:
        print("  FAILED", k, e)
    if failed:
        sys.exit(1)


# ----------------------------------------------------------------------------- 3. verify
def cmd_verify(a):
    out = Path(a.out)
    cfg = load_json(out / "config.json", None) or sys.exit("run `events` first")
    report = load_json(out / "report.json", {})
    manifest = load_json(out / "files_manifest.json", {})
    ok = True

    seen, per_pair, missing_files, file_values = {}, {}, [], 0
    file_des_in_events = set()
    for f, ev in iter_events(out):
        if ev["event"] in seen:
            print(f"DUPLICATE event {ev['event']}")
            ok = False
        seen[ev["event"]] = 1
        if ev.get("program") not in cfg["programs"] or ev.get("orgUnit") not in cfg["orgUnits"]:
            print(f"OUT OF SCOPE event {ev['event']}")
            ok = False
        per_pair[(ev["program"], ev["orgUnit"])] = per_pair.get((ev["program"], ev["orgUnit"]), 0) + 1
        for dv in ev.get("dataValues", []):
            key = f"{ev['event']}__{dv['dataElement']}"
            if key in manifest or (out / "files" / safe(key)).exists():
                file_values += 1
                file_des_in_events.add(dv["dataElement"])

    for k, v in report.items():
        p, ou = k.split("__")
        n = per_pair.get((p, ou), 0)
        flag = "OK " if n == v["serverTotal"] == v["downloaded"] else "BAD"
        ok &= flag == "OK "
        print(f"{flag} {k}: disk={n} downloaded={v['downloaded']} serverTotal={v['serverTotal']}")

    for key, m in manifest.items():
        p = out / "files" / safe(key)
        if not p.exists() or p.stat().st_size == 0:
            missing_files.append(key)
    print(f"events on disk: {len(seen)}; file values: {file_values}; missing/empty files: {len(missing_files)}")
    print("Tip: if you expect files, `files` must have run; file values with no file are listed below.")
    for k in missing_files[:20]:
        print("  MISSING", k)
    ok &= not missing_files
    print("\nVERIFY:", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


# ----------------------------------------------------------------------------- 4. upload
def upload_file(s, base, path, content_type, name):
    with open(path, "rb") as f:
        r = s.post(
            f"{api(base)}/fileResources",
            files={"file": (name, f, content_type)},
            data={"domain": "DATA_VALUE"},
        )
    r.raise_for_status()
    return r.json()["response"]["fileResource"]["id"]


def post_events(s, base, events, mode):
    r = s.post(
        f"{api(base)}/tracker",
        params={
            "async": "false",
            "importMode": mode,
            "importStrategy": "CREATE_AND_UPDATE",
            "atomicMode": "OBJECT",
        },
        json={"events": events},
    )
    body = r.json()
    stats = body.get("stats") or body.get("response", {}).get("stats", {})
    errs = (body.get("validationReport") or {}).get("errorReports", [])
    return r.status_code, stats, errs


def _count(items):
    out = {}
    for i in items:
        out[i] = out.get(i, 0) + 1
    return out


def dst_stage_data_elements(s, base, programs):
    r = s.get(
        f"{api(base)}/programStages",
        params={
            "fields": "id,programStageDataElements[dataElement[id]]",
            "filter": f"program.id:in:[{','.join(programs)}]",
            "paging": "false",
        },
    )
    r.raise_for_status()
    return {
        st["id"]: {x["dataElement"]["id"] for x in st.get("programStageDataElements", [])}
        for st in r.json()["programStages"]
    }


def unknown_pairs(out, stage_des):
    """(stage, dataElement) pairs present in the downloaded events but not configured in destination."""
    pairs = {}
    for _, ev in iter_events(out):
        allowed = stage_des.get(ev.get("programStage"))
        for dv in ev.get("dataValues", []):
            if allowed is None or dv["dataElement"] not in allowed:
                k = (ev.get("programStage"), dv["dataElement"])
                pairs[k] = pairs.get(k, 0) + 1
    return pairs


def cmd_upload(a):
    s = session("DST", a.dst)
    out = Path(a.out)
    cfg = load_json(out / "config.json", None) or sys.exit("run `events` first")
    manifest = load_json(out / "files_manifest.json", {})
    id_map_path = out / "uploaded_files.json"  # idempotent re-runs: no duplicated fileResources
    id_map = load_json(id_map_path, {})

    if a.dry_run:
        for kind, ids in (("programs", cfg["programs"]), ("organisationUnits", cfg["orgUnits"])):
            for i in ids:
                r = s.get(f"{api(a.dst)}/{kind}/{i}", params={"fields": "id"})
                print(f"{'OK     ' if r.status_code == 200 else 'MISSING'} {kind}/{i} in destination")

    stage_des = dst_stage_data_elements(s, a.dst, cfg["programs"])
    unknown = unknown_pairs(out, stage_des)
    if unknown:
        print("\n!!! dataValues whose data element is NOT in that program stage in destination (stage, dataElement: values):")
        for (st, de), n in sorted(unknown.items(), key=lambda x: -x[1]):
            print(f"    {st} / {de}: {n}")
        if a.drop_unknown_datavalues:
            print("--drop-unknown-datavalues: these values will be DROPPED (not imported).\n")
        else:
            print("Their events will be rejected. Fix the metadata in destination, or use --drop-unknown-datavalues.\n")
    else:
        print("Metadata check OK: every data element exists in its stage in destination.")

    totals = {"sent": 0, "created": 0, "updated": 0, "ignored": 0, "events_with_errors": 0, "dropped_values": 0}
    imported_path = out / "imported_events.json"  # uids really imported in destination (for audit / rollback)
    imported = load_json(imported_path, {})
    only = set(a.only_event or [])
    for page_file in sorted((out / "events").glob("*.json")):
        events = json.loads(page_file.read_text())
        if only:
            events = [e for e in events if e["event"] in only]
            if not events:
                continue
        for ev in events:
            ev["notes"] = []  # same workaround as metadata-sync
            kept = []
            for dv in ev.get("dataValues", []):
                if a.drop_unknown_datavalues and (ev.get("programStage"), dv["dataElement"]) in unknown:
                    totals["dropped_values"] += 1
                    continue
                key = f"{ev['event']}__{dv['dataElement']}"
                if key in manifest:
                    if a.dry_run:
                        continue  # VALIDATE can't reference a not-yet-uploaded fileResource
                    if key not in id_map:
                        id_map[key] = upload_file(
                            s, a.dst, out / "files" / safe(key), manifest[key]["contentType"], key.split("__")[-1]
                        )
                        id_map_path.write_text(json.dumps(id_map))
                    dv["value"] = id_map[key]
                kept.append(dv)
            ev["dataValues"] = kept

        code, stats, errs = post_events(s, a.dst, events, "VALIDATE" if a.dry_run else "COMMIT")
        for k in ("created", "updated", "ignored"):
            totals[k] += stats.get(k, 0)
        bad = {e.get("uid") for e in errs}
        if not a.dry_run:
            for ev in events:
                if ev["event"] not in bad and code in (200, 409):
                    imported[ev["event"]] = {
                        "program": ev.get("program"),
                        "orgUnit": ev.get("orgUnit"),
                        "files": {
                            dv["dataElement"]: dv["value"]
                            for dv in ev["dataValues"]
                            if f"{ev['event']}__{dv['dataElement']}" in manifest
                        },
                    }
            imported_path.write_text(json.dumps(imported, indent=1))
        totals["sent"] += len(events)
        totals["events_with_errors"] += len(bad)
        # In VALIDATE mode DHIS2 reports no created/updated, so "valid" is derived: sent - events with errors
        print(
            f"{page_file.name}: HTTP {code} sent={len(events)} valid={len(events) - len(bad)} "
            f"with_errors={len(bad)} stats={stats}"
        )
        for msg, n in sorted(_count(e.get("message") for e in errs).items(), key=lambda x: -x[1])[:5]:
            print(f"   {n}x {msg}")

    print("\nTotals:", totals, "(VALIDATE only, nothing stored)" if a.dry_run else "")
    if a.dry_run:
        print("Ready to import" if totals["events_with_errors"] == 0 else "NOT ready: fix errors above first")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(DEFAULT_CONFIG))
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("events")
    e.add_argument("--src", required=True)
    e.add_argument("--programs", help="comma separated UIDs")
    e.add_argument("--programs-file", help="one UID per line")
    e.add_argument("--org-units", help="comma separated UIDs")
    e.add_argument("--org-units-file", help="one UID per line")
    e.add_argument("--ou-mode", default="SELECTED", choices=["SELECTED", "CHILDREN", "DESCENDANTS"])
    e.add_argument("--after", required=True, help="occurredAfter YYYY-MM-DD")
    e.add_argument("--before", required=True, help="occurredBefore YYYY-MM-DD")
    e.add_argument("--out", required=True)
    e.add_argument(
        "--allow-partial",
        action="store_true",
        help="do not fail when a program has events in org units that are not in the list",
    )
    e.set_defaults(fn=cmd_events)

    f = sub.add_parser("files")
    f.add_argument("--src", required=True)
    f.add_argument("--out", required=True)
    f.set_defaults(fn=cmd_files)

    v = sub.add_parser("verify")
    v.add_argument("--out", required=True)
    v.set_defaults(fn=cmd_verify)

    u = sub.add_parser("upload")
    u.add_argument("--dst", required=True)
    u.add_argument("--out", required=True)
    u.add_argument("--dry-run", action="store_true")
    u.add_argument("--only-event", action="append", help="import only this event UID (repeatable)")
    u.add_argument(
        "--drop-unknown-datavalues",
        action="store_true",
        help="drop dataValues whose data element is not in the destination stage (DATA LOSS, logged)",
    )
    u.set_defaults(fn=cmd_upload)

    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    pre, _ = pre_parser.parse_known_args()
    if Path(pre.config).exists():
        CONFIG.update(json.loads(Path(pre.config).read_text()))
    # make CLI-required args optional when present in config
    for sp in sub.choices.values():
        for act in sp._actions:
            if act.required and act.dest in ("src", "dst", "after", "before", "out"):
                act.required = False
    a = p.parse_args()
    cfg_map = {
        "src": CONFIG.get("src", {}).get("url"),
        "dst": CONFIG.get("dst", {}).get("url"),
        "after": CONFIG.get("occurredAfter"),
        "before": CONFIG.get("occurredBefore"),
        "out": CONFIG.get("outDir"),
    }
    for k, v in cfg_map.items():
        if hasattr(a, k) and getattr(a, k) is None:
            setattr(a, k, v)
    if hasattr(a, "programs") and not (a.programs or a.programs_file):
        a.programs = ",".join(x["id"] for x in CONFIG.get("programs", []))
    if hasattr(a, "org_units") and not (a.org_units or a.org_units_file):
        a.org_units = ",".join(CONFIG.get("orgUnits", []))
    for k in ("src", "dst", "out"):
        if hasattr(a, k) and not getattr(a, k):
            sys.exit(f"Missing --{k} (or set it in the config file)")
    if hasattr(a, "src") and a.src and "PUT_" in a.src or hasattr(a, "dst") and a.dst and "PUT_" in a.dst:
        sys.exit("Fill the URLs in the config file")
    a.fn(a)


if __name__ == "__main__":
    main()


# dhis2_app_audit.py

Lists the DHIS2 apps installed in an apps directory, warns about duplicated apps
and keeps a history of when each app/version was detected or removed.

```bash
python3 dhis2_app_audit.py --apps-dir /app/files/apps [--data-dir .]
```

- `--apps-dir` (required): DHIS2 apps directory. It is only read, never modified.
- `--data-dir` (default: current directory): where `history.csv` and `duplicates.csv` are kept.

## How it works

- For each folder it reads `name` and `version` from `manifest.webapp`
  (or `manifest.json` if there is no `manifest.webapp`).
- **Duplicates**: if two folders contain an app with the same `name`
  (case-insensitive), it logs `DUPLICATE '<name>' in: <folders>` on every run
  and writes them to `duplicates.csv` (`name, folder, version`).
  `duplicates.csv` always holds the current duplicates (header only if there are
  none) and is rewritten **only when the duplicates change**, so any change in
  that file means a new duplicate appeared or one was resolved.
- **History** (`history.csv`, append-only): a row is added only when something
  changes.

  | column        | meaning                                       |
  |---------------|-----------------------------------------------|
  | `date`        | when the script saw the change                |
  | `event`       | `DETECTED` or `REMOVED`                       |
  | `folder`      | app folder                                    |
  | `name`        | app name from the manifest                    |
  | `version`     | app version from the manifest                 |
  | `folder_date` | folder modification date (≈ install date)     |

  A version upgrade in the same folder shows up as `REMOVED` (old version) +
  `DETECTED` (new version).
- If the apps directory is empty but the history has apps (e.g. during a
  redeploy), it does not touch the history and exits with code 1.

Log lines go to stderr with the format `[YYYY-MM-DD HH:MM:SS+02:00] message`
(`Europe/Madrid`, like `date --rfc-3339=seconds`).

Standard library only, Python 3.6+.



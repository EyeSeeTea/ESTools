# dhis2_notice

Put a maintenance notice on top of the login-page message of one or more DHIS2
instances, and remove it automatically when the maintenance window is over.

The notice is stored in the system setting `keyApplicationNotification`. The script
**prepends** your HTML to the current message (default text and the `en` translation)
and later removes exactly that block, so the original message is left untouched.

- Python 3.9+, standard library only (no `pip install`).
- One notice file per announcement; you can reuse and edit them.
- Every change is confirmed by hand (`y/N`); only the revert is automatic (cron).

> Open `readme.html` in a browser for a visual guide (diagram, step-by-step for adding a notice), in English and Spanish.

## How it works

1. You write a notice: a small JSON file (which servers, when it ends) and an HTML file (the text).
2. You run `apply`. The script validates everything, shows what it is going to do and asks `y/N`.
3. On `y` it publishes the notice and records a job in `state/jobs/`.
4. Cron runs `tick` every hour. When a job's `end` has passed, `tick` removes the notice.
   The revert can therefore be up to one hour late.

## Files

```
dhis2_notice.py        the script
servers.json           your servers (no secrets)
notices/               your announcements (name.json + name.html)
state/                 created automatically: jobs/ and notice.log
~/.dhis2_tokens        credentials file (any path, see below)
```

## Configuration

### 1. `servers.json`

Copy `servers.example.json` to `servers.json`:

```json
{
  "timezone": "Europe/Madrid",
  "passwords_file": "~/.dhis2_tokens",
  "servers": {
    "dev-1":  {"url": "https://dhis2-dev-1.example.org", "api_version": "41", "credentials_key": "dev_token"},
    "prod-1": {"url": "https://dhis2.example.org/prod-1"}
  },
  "groups": {
    "dev":  ["dev-1"],
    "prod": ["prod-1"]
  }
}
```

| Field | Required | Meaning |
|---|---|---|
| `timezone` | no (default `Europe/Madrid`) | Timezone of the `end` dates you write in notices |
| `locales` | no (default `["en"]`) | Languages that get the **same** HTML as the default text. `[]` = default only. A language with its own text uses a notice with `locale` instead |
| `passwords_file` | no | Credentials file. Default: `.passwords` next to the script. Can be overridden with `--passwords` |
| `servers.<key>.url` | yes | Base URL of the instance (without `/api`) |
| `servers.<key>.api_version` | no | e.g. `"41"`, adds `/api/41`. Without it `/api` is used |
| `servers.<key>.credentials_key` | no | Name of the credentials entry. Default: the server key |
| `groups` | no | Names that expand to several servers (e.g. all dev servers) |

### 2. Credentials file

Never put secrets in `servers.json`. Use a separate file and protect it:

```bash
chmod 600 ~/.dhis2_tokens
```

Each line is `NAME=value` (quotes optional, `export ` allowed, `#` comments).
A server uses the entry named by its `credentials_key`. The **value decides the type**:

```
dev_token='d2pat_xxxxxxxxxxxxxxxx'    # personal access token (PAT)
prod-1='admin:the:password'           # user:password (basic auth; the password may contain ':')
```

Or keep user and password in two entries and reference both with `;`:

```
demo_user=admin
demo_pass=the-password
```
```json
"demo": {"url": "https://...", "credentials_key": "demo_user;demo_pass"}
```

Notes:
- A PAT only works on the instance that issued it. The PAT needs permission for
  **`GET` and `POST`** (do not restrict its allowed HTTP methods) and, if it has IP/referrer
  restrictions, the IP of this server must be allowed.
- The user needs permission to edit system settings (`F_SYSTEM_SETTING`).
- Basic auth does not work for users with two-factor authentication.
- Names are case sensitive.

### 3. A notice

Two files in `notices/`:

`notices/2026-11-13-dev.json`
```json
{
  "servers": ["dev"],
  "end": "2026-11-13 13:00",
  "message_file": "2026-11-13-dev.html"
}
```
- `servers`: server keys and/or group names from `servers.json`.
- `end`: when the notice is removed, `YYYY-MM-DD HH:MM` in the configured timezone.
- `message_file`: HTML file, relative to the JSON file.
- `locale` (optional): write this notice **only** to that language, e.g. `"fr"`. Without it the notice
  goes to the default text and to the languages in `locales` (`servers.json`), all with the same HTML.

For a language with its own message, create a separate notice per language:

`notices/2026-11-13-dev-fr.json`
```json
{"servers": ["dev"], "end": "2026-11-13 13:00", "message_file": "2026-11-13-dev-fr.html", "locale": "fr"}
```
Run `apply` for each file. Notices for different languages can be active at the same time on the
same server; two notices for the same language cannot.

`notices/2026-11-13-dev.html` is published **exactly as written**, so put the formatting in it:

```html
<center><span style="color:red"><b>
Scheduled update: this instance will be upgraded on 13 November 2026 from 09:00 to 13:00 CET.<br/>
The system may be unavailable during this period. Sorry for the inconvenience.
</b></span></center>
```

If red does not render in your DHIS2 version, try `<font color="red">...</font>`.
Use one notice per environment when dev and prod need different texts.

## Usage

```bash
cd /path/to/dhis2_notice

./dhis2_notice.py check dev                         # read-only: which credentials are used, current message
./dhis2_notice.py apply notices/2026-11-13-dev.json --dry-run   # validate and show, change nothing
./dhis2_notice.py apply notices/2026-11-13-dev.json             # show summary, ask y/N, publish
./dhis2_notice.py status                            # list jobs and their state
./dhis2_notice.py restore                           # remove all active notices now
./dhis2_notice.py restore <job-id>                  # remove one job's notice now
./dhis2_notice.py tick                              # remove notices whose end has passed (cron runs this)
```

`apply` options: `--dry-run`, `--yes` (skip the question), `--minutes N` (testing: ignore the
file's `end` and end N minutes from now).
Global options (before the command): `--config servers.json`, `--passwords file`.

`apply` refuses a server that already has an active notice. A failed `apply` that wrote
nothing leaves no active job, so you can simply run it again.

### Quick test (5 minutes)

```bash
./dhis2_notice.py check dev
./dhis2_notice.py apply notices/example.json --minutes 5
# open the login page, the notice should be on top
./dhis2_notice.py tick          # after 5 minutes: removes it
```

## Cron

```bash
mkdir -p state
crontab -e
```
```cron
0 * * * * cd /path/to/dhis2_notice && python3 dhis2_notice.py tick >> state/tick.log 2>&1
```

`tick` does nothing (and prints nothing) when no job has expired. Run `apply` and cron as
the same user, because jobs live in `state/` next to the script (override with the
`DHIS2_NOTICE_HOME` environment variable).

## Logs and state

- `state/notice.log`: one line per action with a timestamp. Credentials are never written.
- `state/jobs/<id>.json`: one file per `apply`, with the exact text that was published.
  Do not delete the ones with status `active`: that text is what gets removed later.

## Troubleshooting

| Message | Cause |
|---|---|
| `HTTP 401 ... API token does not exists` | Wrong token, or a token from another instance |
| `HTTP 401 ... request http method is not allowed` | The PAT is restricted and `GET` or `POST` is not allowed |
| `HTTP 403 Access is denied` on set | The user/token cannot edit system settings |
| `'<name>' not found in the passwords file` | `credentials_key` does not match an entry; names are case sensitive |
| `these servers already have an active notice` | Run `status`, then `restore` |
| `notice block not found ... left untouched` | The text was already removed or edited by hand; nothing was changed |
| `'end' is already in the past` | Update `end` in the notice, or use `--minutes` to test |

## Good to know

- A notice without `locale` is written to the default text and to every language in `locales` (same HTML). Languages not listed are not touched; a language without its own text falls back to the default.
- If someone edits the message while a notice is active, the revert removes only the notice block.
- If the text of the notice is edited after `apply`, the revert still uses the text that was published.
- Keep real `servers.json`, credentials and notices out of version control (see `.gitignore`).

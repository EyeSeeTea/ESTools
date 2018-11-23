## cronwrap

Wrapper for crontab scripts. Features:

- Save output of scripts (stdin and stderr) to a log file, with line timestamps.
- Manages stderr for crontab. Note that crontab sends an email (variable `MAILTO`) whenever a command outputs something to stderr, even if it finished successfully. This wrapper makes sure nothing is written to stderr on success, to avoid this.

Example:

```
15 22 * * * /usr/local/bin/cronwrap /tmp/output.log ls /etc
```

This runs `ls /etc` at 22:15 every day and saves its stdout/stderr output to `/tmp/output.log`.

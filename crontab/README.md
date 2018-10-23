## cronwrap

Wrapper for crontab scripts: add logs and manages stderr for crontab. Example:

```
$ cronwrap output.log my-script arg1 arg2
```

This runs "my-script arg1 arg2" and saves its stdout/stderr output (with timestamp) to output.log. Note that crontab sends an email (variable `MAILTO`) whenever a command outputs to the stderr, even if it finishes successfully. So the wrapper makes sure nothing is written to stderr on success.

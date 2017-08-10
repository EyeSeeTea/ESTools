#!/usr/bin/python
import sys
import urllib.parse
import subprocess
import re
import shlex
import itertools

import yaml

def int_or_float(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

def debug(s):
    print("[DEBUG] " + s, file=sys.stderr)

def output(s):
    print(s, file=sys.stdout)

def flatten(foo):
    for x in foo:
        if hasattr(x, '__iter__') and not isinstance(x, str):
            for y in flatten(x):
                yield y
        else:
            yield x

def get_metrics_from_ab(body):
    metrics = {}
    data_lines = itertools.dropwhile(lambda line: "Document Length" not in line, body.splitlines())
    for line in data_lines:
        # Skip aggregated by-request entries
        if "cross all concurrent requests" in line:
            continue
        elif ":" in line:
            key = line.split(":", 1)[0].replace(" ", "_").lower()
            matches = [int_or_float(s) for s in re.findall(r"[\d.]+", line)]
            if len(matches) == 1:
                metrics[key] = matches[0]
            elif len(matches) > 1:
                metrics[key] = matches
    return metrics

def benchmark(url, method="GET", concurrent_users=1, nrequests=100, auth=None, data_path=None):
    cmd = list(flatten([
        "ab",
        "-q",
        "-A", ":".join((auth or [])),
        "-n", str(nrequests),
        (["-p", data_path] if method == "POST" and data_path else []),
        "-c", str(concurrent_users),
        "-m", method,
        url,
    ]))
    debug("Benchmarking: {}".format(" ".join(shlex.quote(s) for s in cmd)))
    stdout = subprocess.check_output(cmd)
    return get_metrics_from_ab(stdout.decode("utf8"))

def to_tabs(objs):
    return "\t".join([str(obj) for obj in objs])

def run_benchmark(yaml_path, concurrent_users):
    config = yaml.load(open(yaml_path))
    server_url = config["server"]["url"]
    auth = config["server"]["auth"].split(":")
    nrequests = concurrent_users * 2

    for service in config["services"]:
        url = urllib.parse.urljoin(server_url, service["url"].lstrip("/"))
        data_path = service.get("body-file")
        metrics = benchmark(url,
            method=service["method"],
            auth=auth,
            nrequests=concurrent_users * 2,
            concurrent_users=concurrent_users,
            data_path=data_path,
        )
        metrics_info = to_tabs([
            #metrics["requests_per_second"],
            int(metrics["time_per_request"]),
            "%.2f" % ((metrics["failed_requests"] / nrequests) * 100),
            service["method"],
            url,
        ])
        output(" " + metrics_info)

def main(args):
    yaml_path = args[0]
    concurrent_users = int(args[1])
    run_benchmark(yaml_path, concurrent_users)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

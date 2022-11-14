#!/usr/bin/env python3

"""
Read data from columns in dhis2 databases that are encoded as gzipped json.

(For example, the "data" column of the "audit" table.)
"""

import sys
import gzip
import json


def main():
    try:
        data = bytes.fromhex(read().strip().lstrip('\\').lstrip('x'))

        decoded = gzip.decompress(data)

        print(json.dumps(json.loads(decoded), indent=4))
    except (ValueError, EOFError, gzip.BadGzipFile,
            json.decoder.JSONDecodeError) as e:
        sys.exit(e)
    except KeyboardInterrupt as e:
        sys.exit()


def read():
    if not sys.stdin.isatty():
        return sys.stdin.read()
    elif len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return input('Data string: ')



if __name__ == '__main__':
    main()

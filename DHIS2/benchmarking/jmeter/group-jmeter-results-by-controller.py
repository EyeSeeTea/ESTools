#!/usr/bin/python
#
# Group controllers in JMeter JML file and show mean time by user
#
import itertools
import sys
import re

def atoi(text):
    return (int(text) if text.isdigit() else text)

def natural_keys(text):
    return [atoi(c) for c in re.split('(\d+)', text)]

def get_pairs(lines):
    for line in lines:
        fields = line.split(",")
        if len(fields) < 10:
            continue
        elapsed, name = fields[1], fields[2]
        if "Controller" in name:
            yield name, int(elapsed)

def main(args):
    for jtl_file_path in sorted(args, key=natural_keys):
        lines = open(jtl_file_path)
        groups = itertools.groupby(sorted(get_pairs(lines)), key=lambda pair: pair[0])
        print(jtl_file_path)

        for key, values in groups:
            elapseds = [elapsed for (name, elapsed) in values]
            print("  " + "{controller} ({count}) - mean elapsed by user: {mean} secs".format(
              controller=key,
              count=len(elapseds),
              mean=int(sum(elapseds) / len(elapseds) / 1000.0))
          )

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
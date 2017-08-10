#!/usr/bin/python
#
# Group controllers in JMeter JML file and show mean time by user
#
import itertools
import sys
import re
import csv

import numpy as np
import matplotlib
matplotlib.use('Agg') # this way X is not required
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

def get_jtl_entries(jtl_path):
    for row in csv.reader(open(jtl_path)):
        if len(row) < 10:
            continue
        elapsed, name, success_info = row[1], row[2], row[4]
        if "Controller" in name:
            match = re.search("in transaction : (\d+), number of failing samples : (\d+)", success_info)
            success_rate = ((int(match[1]), int(match[2])) if match else 100)
            yield dict(controller=name, elapsed=int(elapsed), success_rate=success_rate)

def group_by(xs, mapper = None):
    output = {}
    for x in xs:
        key = (mapper(x) if mapper else x)
        group = output.setdefault(key, [])
        group.append(x)
    return output

def main(args):
    output_name = args[0]
    jtl_file_paths = args[1:]

    colormap = plt.cm.gist_ncar
    colors = [colormap(i) for i in np.linspace(0, 1, 10)]
    plt.xlabel('# Users')
    plt.ylabel('Mean time by user (secs)')
    ax = plt.axes()
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    entries = []
    for jtl_file_path in sorted(jtl_file_paths):
        groups = group_by(get_jtl_entries(jtl_file_path), lambda jentry: jentry["controller"])

        for controller, jentries in groups.items():
            elapseds = [jentry["elapsed"] for jentry in jentries]
            samples_total, samples_failed = zip(*[jentry["success_rate"] for jentry in jentries])
            success_rate = 100.0 * (1.0 - (sum(samples_failed) / sum(samples_total)))
            entry = dict(
                controller=controller,
                count=len(elapseds),
                mean=int(sum(elapseds) / len(elapseds) / 1000.0),
                success_rate=int(success_rate),
            )
            entries.append(entry)

    for entry in entries:
        print(entry)
        print("  " + "{controller} ({count}) - mean elapsed by user: {mean} secs".format(**entry))

    grouped_by_controller = group_by(entries, lambda entry: entry["controller"])
    for coloridx, (controller, grouped_entries) in enumerate(grouped_by_controller.items()):
        counts, means, success_rates = \
            zip(*[(entry["count"], entry["mean"], entry["success_rate"]) for entry in grouped_entries])
        plt.plot(counts, means, 'ro', color=colors[coloridx], label=controller)

        for count, mean, success_rate in zip(counts, means, success_rates):
            plt.annotate("{}%".format(success_rate),
                xy=(count, mean), xycoords='data',
                xytext=(5, 0), textcoords='offset points',
                )

    plt.legend(loc="upper left")
    plt.savefig(output_name)
    #plt.show()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
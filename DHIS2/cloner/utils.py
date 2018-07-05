from __future__ import print_function

import sys

def flatten(xss):
    """Flatten a list of lists one level deep."""
    return [x for xs in xss for x in xs]

def merge(d1, d2):
    """Merge d2 into d1 and return a new dictionary."""
    d3 = d1.copy()
    d3.update(d2)
    return d3

def debug(*args, **kwargs):
    """Print debug info to stderr."""
    print(*args, file=sys.stderr, **kwargs)

def unique(sequence, mapper=None):
    """Return iteratable of unique elements in sequence with an optional identify mapper."""
    mapper = mapper or (lambda x: x)
    seen = set()
    for item in sequence:
        marker = mapper(item)
        if marker not in seen:
            seen.add(marker)
            yield item

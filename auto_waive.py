#!/usr/bin/env python3
"""Waive existing violations by inserting pragmas in source files.

Many lintworks derived tools support a "pragma" or "waiver" based rule system
to enable/disable rules dynamically in files. This is useful in a few
scenarios:

1. It allows the rule to be bypassed when it makes sense.
2. If the rule is not robust, it may flag false positives. False positives may
   be waived without requiring tools updates, preventing users from being
   blocked.
3. When writing a new rule, waive the existing violations. This lets the rule
   be put in place and prevents new violations from occurring. It is the least
   path of resistance for migration.

This script is intended to be used for case 3 above. Edit all files to waive
existing violations.

Example usage:

  <lintworks tool invocation> | python3 autowaive.py <lintworks tool name>

"""
import argparse
import re
import sys


def insert_at_line(filename, line_number, string):
    """This is wildly inefficient, but we our use case is pretty small."""
    with open(filename, "r") as f:
        contents = f.readlines()

    contents.insert(line_number, string)

    with open(filename, "w") as f:
        contents = "".join(contents)
        f.write(contents)


def main(tool_name):
    """Read stdin and waive all violations by editing source files with pragmas."""
    violate_re = re.compile(
        "^(?P<filename>.*?)(:(?P<line_number>[0-9]+)){0,1} violates (?P<rule>.*)"
    )

    lines = sys.stdin.readlines()

    re_matches = [violate_re.match(l) for l in lines]
    matches = [m for m in re_matches if m]

    errors = sorted([(m.group('filename'), int(m.group('line_number')),
                      m.group('rule')) for m in matches])

    for filename, line_number, error in reversed(errors):
        insert_at_line(filename, line_number + 1,
                       f"// {tool_name}: enable={error}\n")
        insert_at_line(filename, line_number,
                       f"// {tool_name}: disable={error}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("tool_name")
    args = parser.parse_args()
    main(args.tool_name)

import argparse
import importlib.util
import logging
import sys

from lw.base import glob_import_rules


class ReportServer(object):

    def __init__(self, display_motivation=True):
        self.log = self._setup_log()
        self.display_motivation = display_motivation

        self.error_count = 0

    @staticmethod
    def _setup_log():
        log = logging.getLogger("lw")
        handler = logging.StreamHandler(sys.stdout)
        log.addHandler(handler)
        return log

    def error(self, listener, line_no, line, message):
        self.error_count += 1
        if not line_no:
            line_no = ""
        else:
            line_no = ":{}".format(line_no)
        display_filename = "{}{}".format(listener.filename, line_no)
        subsequent_indent = "  "

        if line:
            line = "\n{0}Offending Code:\n{0}{0}>{1}".format(subsequent_indent, line.rstrip())
        else:
            line = ""

        if message:
            reason = "\n{0}Reason:\n{0}{0}{1}".format(subsequent_indent, message)
        else:
            reason = ""

        if self.display_motivation and listener.__class__.__doc__:
            motivation = "\n{0}Motivation:\n{0}{0}{1}".format(subsequent_indent, listener.__class__.__doc__)
        else:
            motivation = ""

        self.log.error("%s violates %s%s%s%s", display_filename, listener.__class__.__name__, reason, line, motivation)


class GlobalConfig(object):

    def __init__(self, argv):
        self.options = self.parse_args(argv)
        self.rs = ReportServer(display_motivation=self.options.display_motivation)

    @staticmethod
    def parse_args(argv):
        parser = argparse.ArgumentParser()
        parser.add_argument('files', nargs='+', help='Files to check')
        parser.add_argument('--rc',
                            dest='rule_config',
                            action='append',
                            default=[],
                            required=True,
                            help=("Path to python file containing rules."
                                  "May be specified multiple times."))
        parser.add_argument('--igr',
                            dest='ignored_rules',
                            action='append',
                            default=[],
                            required=False,
                            help=("Rule to be excluded"
                                  "May be specified multiple times."))
        parser.add_argument('--igrc',
                            dest='ignored_rule_config',
                            action='append',
                            default=[],
                            required=False,
                            help=("Path to file containing rules to be excluded."
                                  "May be specified multiple times."))
        parser.add_argument('-m',
                            dest='display_motivation',
                            action='store_true',
                            default=False,
                            help="Display motivation behind each violated rule.")
        return parser.parse_args()


def main(argv):
    gc = GlobalConfig(argv)

    ignored_rules = gc.options.ignored_rules

    for igrc in gc.options.ignored_rule_config:
        with open(igrc) as rfh:
            for line in rfh.read().splitlines():
                line = line.strip().split(" ")[0]
                if any([line.startswith("#"), line.startswith("//")]):
                    continue
                if line not in ignored_rules:
                    ignored_rules.append(line)

    top_broadcasters = []
    for rc in gc.options.rule_config:
        spec = importlib.util.spec_from_file_location(rc, rc)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # print(rc)
        glob_import_rules(rc, ignored_rules)

        try:
            top_broadcasters.append(mod.top_broadcaster)
        except AttributeError:
            raise AttributeError("file {} did not contain a variable 'top_broadcaster'".format(rc))

    for fname in gc.options.files:
        # Ignore temporary files
        if fname.endswith('~'):
            continue
        for top_broadcaster in top_broadcasters:
            with open(fname) as fstream:
                lbc = top_broadcaster(fname, fstream, parent=None, gc=gc)

    return gc.rs.error_count > 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

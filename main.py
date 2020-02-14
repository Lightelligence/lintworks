import argparse
import importlib.util
import logging
import sys

class ReportServer(object):

    def __init__(self, display_motivation=True):
        self.log = self._setup_log()
        self.display_motivation = display_motivation

        self.error_count = 0
    
    @staticmethod
    def _setup_log():
        log = logging.getLogger("lw")
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
        
        self.log.error("%s violates %s%s%s%s",
                       display_filename, listener.__class__.__name__,
                       reason,
                       line,
                       motivation)


class GlobalConfig(object):

    def __init__(self, argv):
        self.options = self.parse_args(argv)
        self.rs = ReportServer(display_motivation=self.options.display_motivation)

    @staticmethod
    def parse_args(argv):
        parser = argparse.ArgumentParser()
        parser.add_argument('files',
                            nargs='+',
                            help='Files to check')
        parser.add_argument('--rc',
                            dest='rule_config',
                            action='append',
                            default=[],
                            required=True,
                            help=("Path to python file containing rules."
                                  "May be specified multiple times."))
        parser.add_argument('-m',
                            dest='display_motivation',
                            action='store_true',
                            default=False,
                            help="Display motivation behind each violated rule.")
        return parser.parse_args()


def main(argv):
    gc = GlobalConfig(argv)

    top_broadcasters = []
    for rc in gc.options.rule_config:
        spec = importlib.util.spec_from_file_location(rc, rc)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            top_broadcasters.append(mod.top_broadcaster)
        except AttributeError:
            raise AttributeError("file {} did not contain a variable 'top_broadcaster'".format(rc))

    for fname in gc.options.files:
        for top_broadcaster in top_broadcasters:
            with open(fname) as fstream:
                lbc = top_broadcaster(fname, fstream, parent=None, gc=gc)

    return gc.rs.error_count > 0
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))

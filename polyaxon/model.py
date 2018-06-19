from __future__ import division, print_function, absolute_import

import sys


from cartpole.client.shell_cmd import main as cartpole_main
from polyaxon_helper import get_outputs_path, send_metrics, get_log_level


def main(argv=sys.argv[1:]):
    cartpole_main(argv)


if __name__ == '__main__':
    main(argv=sys.argv[1:])

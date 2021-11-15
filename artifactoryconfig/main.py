import sys
import logging

import lib.helper as helper
import lib.artifactory as artifactory
import lib.configreader as configreader

__author__ = "Klaus Wening"
__copyright__ = "Klaus Wening"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


def main(args):
    """Wrapper allowing :func:`apply_config` to be called with string arguments in a CLI fashion

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    config = helper.parse_args(args)
    helper.setup_logging(config.loglevel)
    config_objects = configreader.read_configuration(config)

    artifactory.init_connection(config.artifactory_url, config.artifactory_user, config.artifactory_token)
    artifactory.apply_configuration(config_objects, config.dry_run)


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

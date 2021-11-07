import sys
import logging

import lib.helper as helper
import lib.artifactory as artifactory
import lib.configreader as config

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
    args = helper.parse_args(args)
    helper.setup_logging(args.loglevel)
    config_objects = config.read_configuration(args.config_folder, args.vault_files, args.vault_secret)

    artifactory.init_connection(args.artifactory_url, args.artifactory_user, args.artifactory_token)
    artifactory.apply_configuration(config_objects, args.dry_run)


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

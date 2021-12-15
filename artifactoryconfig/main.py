import sys
import logging

import lib.helper as helper
import lib.artifactory as artifactory
import lib.configreader as configreader
import lib.namespaces as namespaces
import lib.linting as linting

__author__ = "Klaus Wening"
__copyright__ = "Klaus Wening"
__license__ = "MIT"


_logger = logging.getLogger(__name__)


def main(args):
    """Wrapper allowing :func:`command` to be called with string arguments in a CLI fashion
    """
    config = helper.parse_args(args)

    if config.command == 'deploy':
        logging.info("Deploying configuration to an Artifactory server")
        local_config = configreader.read_configuration(config)
        artifactory.init_connection(config.artifactory_url, config.artifactory_user, config.artifactory_token)
        artifactory.apply_configuration(local_config, config)
    elif config.command == 'namespaces':
        logging.info("Creating permissions for namespaces")
        namespaces.read_namespaces(config)
    elif config.command == 'lint':
        logging.info("Linting artifactory config")
        local_config = configreader.read_configuration(config)
        linting.lint_config(local_config)
        logging.warning("Not implemented yet")


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

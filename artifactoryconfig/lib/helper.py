import argparse
import logging
import os
import sys


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Artifactory config automation")

    parser.add_argument(
        '-q',
        '--quiet',
        dest='loglevel',
        action='store_const',
        default=logging.INFO,
        const=logging.ERROR,
        help='quiet logging')
    parser.add_argument(
        '-v',
        '--verbose',
        dest='loglevel',
        action='store_const',
        default=logging.INFO,
        const=logging.DEBUG,
        help='verbose logging')

    parser.add_argument(
        "--url",
        dest="artifactory_url",
        default=os.getenv("ARTIFACTORY_URL", ""),
        help="Artifactory base url",
    )
    parser.add_argument(
        "--user",
        dest="artifactory_user",
        default=os.getenv("ARTIFACTORY_USER", ""),
        help="Artifactory user to authenticate with token",
    )
    parser.add_argument(
        "--token",
        dest="artifactory_token",
        default=os.getenv("ARTIFACTORY_TOKEN", ""),
        help="Artifactory access token with admin permissions",
    )
    parser.add_argument(
        "-c",
        "--config-folder",
        dest="config_folder",
        default=os.getenv("CONFIG_FOLDER", "config"),
        help="path to folder containing configuration files",
    )
    parser.add_argument(
        "--vault-files",
        dest="vault_files",
        default=os.getenv("VAULT_FILES", ""),
        help="(comma-separated) list of paths to file(s) with ansible-vault encrypted secrets",
    )
    parser.add_argument(
        "--vault-secret",
        dest="vault_secret",
        default=os.getenv("VAULT_SECRET", ""),
        help="secret to decrypt vault files",
    )

    parser.add_argument(
        '--dry-run',
        dest='dry_run',
        action='store_true',
        default=os.getenv("DRY_RUN", ""),
        help='dry run - make no changes')

    args = parser.parse_args(args)

    if not args.artifactory_url:
        exit(parser.print_usage())

    args.config_folder = args.config_folder.rstrip(os.sep)

    return args


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )

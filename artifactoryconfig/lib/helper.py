import argparse
import logging
import os
import sys
from dataclasses import dataclass
from glob import glob

import yaml


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
        "-c",
        "--config-file",
        dest="config_file",
        default=os.getenv("CONFIG_FILE", ""),
        help="Path to a yaml file with configuration settings",
    )
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
        "-f",
        "--config-folder",
        dest="config_folder",
        default=os.getenv("CONFIG_FOLDER", ""),
        help="path to folder containing configuration files",
    )
    parser.add_argument(
        "--vault-files",
        dest="vault_files",
        default=os.getenv("VAULT_FILES", ""),
        help="(comma-separated) list of paths to file(s) with ansible-vault encrypted secrets",
    )
    parser.add_argument(
        "--vault-files-pattern",
        dest="vault_files_pattern",
        default=os.getenv("VAULT_FILES_PATTERN", ""),
        help="pattern to define vault secret files within config folder",
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

    args.config_folder = args.config_folder.rstrip(os.sep)
    config = Config()

    if args.config_file:
        # TODO logging not yet active here
        #logging.info(f"Reading configuration from yaml file '{args.config_file}'")
        config.from_yaml(args.config_file)

    # Override yaml settings with cli args or ENV
    config.from_args(args.__dict__)

    if not config.is_valid():
        exit(parser.print_usage())

    return config


def setup_logging(loglevel: int):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


@dataclass
class Config:
    """Class holds configuration settings defined by config yaml file or cli arguments
    """
    config_file: str = ""
    artifactory_url: str = ""
    artifactory_user: str = ""
    artifactory_token: str = ""
    config_folder: list = None
    vault_files: str = ""
    vault_files_pattern: str = ""
    vault_secret: str = ""
    loglevel: int = ""
    dry_run: bool = False

    def __init__(self, initial_data=None):
        if initial_data is None:
            initial_data = {}

        for key in initial_data:
            if key == "config_folder":
                self._init_config_folders(initial_data[key])
            else:
                setattr(self, key, initial_data[key])

    def from_yaml(self, config_file: str):
        if not os.path.isfile(config_file):
            print(f"Config file '{config_file}' doesn't exist")
            exit(0)

        with open(config_file) as yaml_file:
            yaml_config = yaml.safe_load(yaml_file)
            self.__init__(yaml_config)

    def from_args(self, args: dict):
        self.__init__({k: v for k, v in args.items() if not v == ""})

    def is_valid(self) -> bool:
        return not self.artifactory_url == ""

    def get_vault_files(self):
        if self.vault_files != "":
            return [x.strip() for x in self.vault_files.split(',')]
        else:
            files = []

            for folder in self.config_folder:
                # use glob pattern to detect vault files
                files.extend(glob(f'{folder}/{self.vault_files_pattern}', recursive=True))

            return files

    def _init_config_folders(self, config_folders):
        if isinstance(config_folders, list):
            self.config_folder = config_folders
        elif isinstance(config_folders, str):
            self.config_folder = config_folders.split(',')


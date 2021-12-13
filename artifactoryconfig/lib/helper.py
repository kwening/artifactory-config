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
    global_parser_args = argparse.ArgumentParser()

    global_parser_args.add_argument(
        '-q',
        '--quiet',
        dest='log_level',
        action='store_const',
        default=logging.INFO,
        const=logging.ERROR,
        help='quiet logging')
    global_parser_args.add_argument(
        '-v',
        '--verbose',
        dest='log_level',
        action='store_const',
        default=logging.INFO,
        const=logging.DEBUG,
        help='verbose logging')
    global_parser_args.add_argument(
        "-c",
        "--config-file",
        dest="config_file",
        default=os.getenv("CONFIG_FILE", ""),
        help="Path to a yaml file with configuration settings",
    )

    sub_parser = parser.add_subparsers(dest='command', required=True)
    deploy = sub_parser.add_parser('deploy', parents=[global_parser_args], add_help=False,
                                   help="Deploy config to Artifactory server")
    namespaces = sub_parser.add_parser('namespaces', parents=[global_parser_args], add_help=False,
                                       help="Create permissions for defined namespaces")
    lint = sub_parser.add_parser('lint', parents=[global_parser_args], add_help=False,
                                 help="Lint existing configuration")

    # Arguments specific for 'deploy' command
    deploy.add_argument(
        "--url",
        dest="artifactory_url",
        default=os.getenv("ARTIFACTORY_URL", ""),
        help="Artifactory base url",
    )
    deploy.add_argument(
        "--user",
        dest="artifactory_user",
        default=os.getenv("ARTIFACTORY_USER", ""),
        help="Artifactory user to authenticate with token",
    )
    deploy.add_argument(
        "--token",
        dest="artifactory_token",
        default=os.getenv("ARTIFACTORY_TOKEN", ""),
        help="Artifactory access token with admin permissions",
    )
    deploy.add_argument(
        "-f",
        "--config-folder",
        dest="config_folder",
        default=os.getenv("CONFIG_FOLDER", ""),
        help="path to folder containing configuration files",
    )
    deploy.add_argument(
        "--vault-files",
        dest="vault_files",
        default=os.getenv("VAULT_FILES", ""),
        help="(comma-separated) list of paths to file(s) with ansible-vault encrypted secrets",
    )
    deploy.add_argument(
        "--vault-files-pattern",
        dest="vault_files_pattern",
        default=os.getenv("VAULT_FILES_PATTERN", ""),
        help="pattern to define vault secret files within config folder",
    )
    deploy.add_argument(
        "--vault-secret",
        dest="vault_secret",
        default=os.getenv("VAULT_SECRET", ""),
        help="secret to decrypt vault files",
    )
    deploy.add_argument(
        '--dry-run',
        dest='dry_run',
        action='store_true',
        default=os.getenv("DRY_RUN", ""),
        help='dry run - make no changes')

    # Arguments specific for 'namespaces' command
    namespaces.add_argument(
        "-n",
        "--namespaces-file",
        dest="namespaces_file",
        default=os.getenv("NAMESPACES_FILE", ""),
        help="path to namespaces yaml file",
    )
    namespaces.add_argument(
        "-o",
        "--output-dir",
        dest="output_dir",
        default=os.getenv("OUTPUT_DIR", ""),
        help="target directory for generated files",
    )

    args = parser.parse_args(args)

    setup_logging(args.log_level)

    if args.command == 'deploy':
        config = DeployConfig()
        active_parser = deploy
    elif args.command == 'namespaces':
        config = NamespacesConfig()
        active_parser = namespaces
    elif args.command == 'lint':
        config = LintingConfig()
        active_parser = lint
    else:
        config = Config()
        active_parser = parser

    if args.config_file:
        logging.info(f"Reading configuration from yaml file '{args.config_file}'")
        config.from_yaml(args.config_file)

    # Override yaml settings with cli args or ENV
    config.from_args(args.__dict__)

    if not config.is_valid():
        sys.exit(active_parser.print_usage())

    return config


def setup_logging(log_level: int):
    """Setup basic logging

    Args:
      log_level (int): minimum log level for emitting messages
    """
    log_format = "[%(asctime)s] %(levelname)-7s %(name)-7s %(message)s"
    logging.basicConfig(
        level=log_level, stream=sys.stdout, format=log_format, datefmt="%Y-%m-%d %H:%M:%S"
    )


@dataclass
class Config:
    """
    Class for global configuration options defined by yaml config file or cli arguments
    """
    command: str = ""
    config_file: str = ""
    log_level: int = ""

    def __init__(self, initial_data=None):
        if initial_data is None:
            initial_data = {}

        for key in initial_data:
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
        return True


@dataclass
class DeployConfig(Config):
    """
    Extends Config class with specific options for 'deploy' command
    """
    artifactory_url: str = ""
    artifactory_user: str = ""
    artifactory_token: str = ""
    config_folder: list = None
    vault_files: str = ""
    vault_files_pattern: str = ""
    vault_file_list: list = None
    vault_secret: str = ""
    unmanaged_ignores: list = None
    dry_run: bool = False

    def __init__(self, initial_data=None):
        Config.__init__(self, initial_data)
        if initial_data is None:
            initial_data = {}

        list_members = ["config_folder", "unmanaged_ignores"]
        for key in initial_data:
            if key in list_members:
                setattr(self, key, as_list(initial_data[key]))
            else:
                setattr(self, key, initial_data[key])

        self._init_vault_files()
        if not self.unmanaged_ignores:
            self.unmanaged_ignores = []

    def is_valid(self) -> bool:
        return self.artifactory_url != "" and isinstance(self.config_folder, list)

    def _init_vault_files(self):
        if self.vault_file_list:
            return

        if self.vault_files:
            self.vault_file_list = [x.strip() for x in self.vault_files.split(',')]
        elif self.config_folder and self.vault_files_pattern:
            for folder in self.config_folder:
                # use glob pattern to detect vault files
                self.vault_file_list.extend(glob(f'{folder}/{self.vault_files_pattern}', recursive=True))
        else:
            self.vault_file_list = []


@dataclass
class NamespacesConfig(Config):
    """
    Extends Config class with specific options for 'namespaces' command
    """
    namespaces_file: str = ""
    internal_repos: list = None
    thirdparty_repos: list = None
    internal_users: list = None
    public_users: list = None
    internal_groups: list = None
    public_groups: list = None
    output_dir: str = "out"
    output_format: str = "json"

    def __init__(self, initial_data=None):
        Config.__init__(self, initial_data)
        if initial_data is None:
            initial_data = {}

        for key in initial_data:
            if key == "repos":
                self.internal_repos = as_list(initial_data[key].get('internal', None))
                self.thirdparty_repos = as_list(initial_data[key].get('thirdparty', None))
            if key == "users":
                self.public_users = as_list(initial_data[key].get('public', None))
                self.internal_users = as_list(initial_data[key].get('internal', None))
            if key == "groups":
                self.public_groups = as_list(initial_data[key].get('public', None))
                self.internal_groups = as_list(initial_data[key].get('internal', None))
            else:
                setattr(self, key, initial_data[key])

        self.output_dir = self.output_dir + '/' if not self.output_dir.endswith('/') else self.output_dir

    def is_valid(self) -> bool:
        return self.namespaces_file != ""


@dataclass
class LintingConfig(Config):
    """
    Extends Config class with specific options for 'lint' command
    """


def as_list(value):
    if value is None:
        return []
    elif isinstance(value, list):
        return value
    elif isinstance(value, str):
        return [x.strip() for x in value.split(',')]

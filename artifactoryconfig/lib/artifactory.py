"""
Integration with Artifactory server
Send api requests, process results,...
"""
import logging
import re
import requests

from pyartifactory import Artifactory
from pyartifactory.models import NewUser, User, Group, LocalRepository, RemoteRepository, \
    PermissionV2, VirtualRepository

from .helper import DeployConfig

ARTIFACTORY: Artifactory
APP_CONFIG: DeployConfig

# Debug requests
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True


def init_connection(url: str, username: str, token: str):
    """
    Init the connection to the Artifactory server
    :param url: url to the artifactory server
    :param username: (admin) username used for requests
    :param token: user token used for requests
    :return: None
    """
    global ARTIFACTORY
    api_version = 2

    if token is not None and username is not None:
        logging.info(f"Initialising connection to '{url}' with user '{username}' and token auth")
        ARTIFACTORY = Artifactory(url=url, auth=(username, token), api_version=api_version)
    else:
        logging.info(f"Initialising connection to '{url}' without auth")
        ARTIFACTORY = Artifactory(url=url, auth=None, api_version=api_version)

    # Try to list repos to force an exception on invalid connect configuration
    # art.repositories.list()


def _get_configuration() -> dict:
    global ARTIFACTORY
    logging.info("#####   Fetching current configuration from artifactory   #####")
    current_config = {'users': ARTIFACTORY.users.list(),
                      'groups': ARTIFACTORY.groups.list(),
                      'permissions': ARTIFACTORY.permissions.list(),
                      'localRepos': [repo for repo in ARTIFACTORY.repositories.list()
                                     if repo.type == 'LOCAL'],
                      'remoteRepos': [repo for repo in ARTIFACTORY.repositories.list()
                                      if repo.type == 'REMOTE'],
                      'virtualRepos': [repo for repo in ARTIFACTORY.repositories.list()
                                       if repo.type == 'VIRTUAL']
                      }

    logging.debug(f"Current configuration {current_config}")

    return current_config


def apply_configuration(config_objects: dict, config: DeployConfig):
    """
    Apply the given configuration to the Artifactory server
    :param config_objects: configurations created from local files
    :param config: configuration based on cli parameters
    :return: None
    """
    global ARTIFACTORY
    global APP_CONFIG
    current_config = _get_configuration()
    APP_CONFIG = config

    if config.dry_run:
        logging.info("Dry run enabled - no changes will be deployed")

    __apply_local_repo_config(config_objects['localRepositories'], current_config['localRepos'],
                              config.dry_run)
    __apply_remote_repo_config(config_objects['remoteRepositories'], current_config['remoteRepos'],
                               config.dry_run)
    __apply_virtual_repo_config(config_objects['virtualRepositories'],
                                current_config['virtualRepos'], config.dry_run)
    __apply_user_config(config_objects, current_config, config.dry_run)
    __apply_group_config(config_objects, current_config, config.dry_run)
    __apply_permission_config(config_objects, current_config, config.dry_run)


def __apply_user_config(config_objects, current_config, dry_run: bool):
    global ARTIFACTORY
    logging.info("#####   Applying user configs   #####")

    for key, value in config_objects['users'].items():
        logging.info(f"Processing user '{key}'")
        # value = map_fields(value, {'disableUIAccess': 'disable_ui',
        #                            'profileUpdatable': 'profile_updatable'})
        try:
            if any(x.name == key for x in current_config['users']):
                user = User(**value)

                if not dry_run:
                    ARTIFACTORY.users.update(user)
                action = 'updated'
                current_config['users'].remove(next((x for x in current_config['users']
                                                     if x.name == key), None))
            else:
                # TODO password via template or generated
                if 'password' not in value:
                    value['password'] = 'dfiököjwie394rkK'
                user = NewUser(**value)
                if not dry_run:
                    ARTIFACTORY.users.create(user)
                action = 'created'

            logging.info(f"User '{key}' successfully {action}")
        except requests.exceptions.HTTPError as error:
            __log_api_error(error)

    __log_unmanaged_items("user", [item.name for item in current_config['users']])


def __apply_group_config(config_objects, current_config, dry_run: bool):
    global ARTIFACTORY
    logging.info("#####   Applying group configs   #####")

    for key, value in config_objects['groups'].items():
        logging.info(f"Processing group '{key}'")
        group = Group(**value)

        try:
            if any(x.name == key for x in current_config['groups']):
                if not dry_run:
                    ARTIFACTORY.groups.update(group)
                action = 'updated'
                current_config['groups'].remove(next((x for x in current_config['groups']
                                                      if x.name == key), None))
            else:
                if not dry_run:
                    ARTIFACTORY.groups.create(group)
                    ARTIFACTORY.groups.update(group)
                action = 'created'

            logging.info(f"Group '{key}' successfully {action}")
        except requests.exceptions.HTTPError as error:
            __log_api_error(error)

    __log_unmanaged_items("group", [item.name for item in current_config['groups']])


def __apply_permission_config(config_objects, current_config, dry_run: bool):
    global ARTIFACTORY
    logging.info("#####   Applying permission configs   #####")

    for key, value in config_objects['permissions'].items():
        logging.info(f"Processing permission '{key}'")
        permission = PermissionV2(**value)

        try:
            if any(x.name == key for x in current_config['permissions']):
                if not dry_run:
                    ARTIFACTORY.permissions.update(permission)
                action = 'updated'
                current_config['permissions'].remove(
                    next((x for x in current_config['permissions'] if x.name == key), None))
            else:
                if not dry_run:
                    ARTIFACTORY.permissions.create(permission)
                action = 'created'
            logging.info(f"Permission '{key}' successfully {action}")
        except requests.exceptions.HTTPError as error:
            __log_api_error(error)

    __log_unmanaged_items("permission", [item.name for item in current_config['permissions']])


def __apply_local_repo_config(config_objects, current_config, dry_run: bool):
    global ARTIFACTORY
    logging.info("#####   Applying local repo configs   #####")

    for key, value in config_objects.items():
        logging.info(f"Processing local repo '{key}'")
        value['key'] = key
        value['packageType'] = value['type']
        value['repoLayoutRef'] = value['repoLayout']
        local_repo = LocalRepository(**value)

        try:
            if any(x.key == key for x in current_config):
                if not dry_run:
                    ARTIFACTORY.repositories.update_repo(local_repo)
                action = 'updated'
                current_config.remove(
                    next((x for x in current_config if x.key == key), None))
            else:
                if not dry_run:
                    ARTIFACTORY.repositories.create_repo(local_repo)
                action = 'created'
            logging.info(f"Local repo '{key}' successfully {action}")
        except requests.exceptions.HTTPError as error:
            __log_api_error(error)

    __log_unmanaged_items("local repo", [item.key for item in current_config])


def __apply_remote_repo_config(config_objects, current_config, dry_run: bool):
    global ARTIFACTORY
    logging.info("#####   Applying remote repo configs   #####")

    for key, value in config_objects.items():
        logging.info(f"Processing remote repo '{key}'")
        value['key'] = key
        value['packageType'] = value['type']
        value['repoLayoutRef'] = value['repoLayout']
        value['bypassHeadRequest'] = value['bypassHeadRequests']
        remote_repo = RemoteRepository(**value)

        try:
            if any(x.key == key for x in current_config):
                if not dry_run:
                    ARTIFACTORY.repositories.update_repo(remote_repo)
                action = 'updated'
                current_config.remove(
                    next((x for x in current_config if x.key == key), None))
            else:
                if not dry_run:
                    ARTIFACTORY.repositories.create_repo(remote_repo)
                action = 'created'
            logging.info(f"Remote repo '{key}' successfully {action}")
        except requests.exceptions.HTTPError as error:
            __log_api_error(error)

    __log_unmanaged_items("remote repo", [item.key for item in current_config])


def __apply_virtual_repo_config(config_objects, current_config, dry_run: bool):
    global ARTIFACTORY
    logging.info("#####   Applying virtual repo configs   #####")

    for key, value in config_objects.items():
        logging.info(f"Processing virtual repo '{key}'")
        value['key'] = key
        value['packageType'] = value['type']
        value['repoLayoutRef'] = value['repoLayout']
        repo = VirtualRepository(**value)

        try:
            if any(x.key == key for x in current_config):
                if not dry_run:
                    ARTIFACTORY.repositories.update_repo(repo)
                action = 'updated'
                current_config.remove(
                    next((x for x in current_config if x.key == key), None))
            else:
                if not dry_run:
                    ARTIFACTORY.repositories.create_repo(repo)
                action = 'created'
            logging.info(f"Virtual repo '{key}' successfully {action}")
        except requests.exceptions.HTTPError as error:
            __log_api_error(error)

    __log_unmanaged_items("virtual repo", [item.key for item in current_config])


def __log_api_error(error):
    logging.error(f"Request to {error.response.url} failed with status {error.response}")
    logging.error(f"Request body: {error.request.body}")
    logging.error(f"Response: {error.response.text}")


def __map_fields(obj, mapping):
    new_obj = {}

    for key in obj.keys():
        if key in mapping:
            new_key = mapping[key]
        else:
            new_key = key
        new_obj[new_key] = obj[key]

    return new_obj


def __log_unmanaged_items(item_type: str, items: list):
    global APP_CONFIG

    # Make a regex that matches if any of our regexes match.
    ignore_regex = "(" + ")|(".join(APP_CONFIG.unmanaged_ignores) + ")"

    for item in items:
        if not re.match(ignore_regex, item):
            logging.info(f"Unmanaged {item_type} '{item}' found")

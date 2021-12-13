import logging
import re

import requests

from pyartifactory import Artifactory
from pyartifactory.models import NewUser, User, Group, LocalRepository, RemoteRepository, PermissionV2, \
    VirtualRepository

from .helper import DeployConfig

art: Artifactory
app_config: DeployConfig


def init_connection(url: str, username: str, token: str):
    global art
    api_version = 2

    if token is not None and username is not None:
        logging.info(f"Initialising connection to '{url}' with user '{username}' and token auth")
        art = Artifactory(url=url, auth=(username, token), api_version=api_version)
    else:
        logging.info(f"Initialising connection to '{url}' without auth")
        art = Artifactory(url=url, api_version=api_version)

    # Try to list repos to force an exception on invalid connect configuration
    # art.repositories.list()


def get_configuration() -> dict:
    global art
    logging.info("#####   Fetching current configuration from artifactory   #####")
    current_config = {'users': art.users.list(),
                      'groups': art.groups.list(),
                      'permissions': art.permissions.list(),
                      'localRepos': [repo for repo in art.repositories.list() if repo.type == 'LOCAL'],
                      'remoteRepos': [repo for repo in art.repositories.list() if repo.type == 'REMOTE'],
                      'virtualRepos': [repo for repo in art.repositories.list() if repo.type == 'VIRTUAL']
                      }

    logging.debug(f"Current configuration {current_config}")

    return current_config


def apply_configuration(config_objects: dict, config: DeployConfig):
    global art
    global app_config
    current_config = get_configuration()
    app_config = config

    if config.dry_run:
        logging.info("Dry run enabled - no changes will be deployed")

    __apply_local_repo_config(config_objects['localRepositories'], current_config['localRepos'], config.dry_run)
    __apply_remote_repo_config(config_objects['remoteRepositories'], current_config['remoteRepos'], config.dry_run)
    __apply_virtual_repo_config(config_objects['virtualRepositories'], current_config['virtualRepos'],
                                config.dry_run)
    __apply_user_config(config_objects, current_config, config.dry_run)
    __apply_group_config(config_objects, current_config, config.dry_run)
    __apply_permission_config(config_objects, current_config, config.dry_run)


def __apply_user_config(config_objects, current_config, dry_run: bool):
    global art
    logging.info("#####   Applying user configs   #####")

    for key, value in config_objects['users'].items():
        logging.info(f"Processing user '{key}'")
        # value = map_fields(value, {'disableUIAccess': 'disable_ui',
        #                            'profileUpdatable': 'profile_updatable'})
        try:
            if any(x.name == key for x in current_config['users']):
                user = User(**value)

                if not dry_run:
                    art.users.update(user)
                action = 'updated'
                current_config['users'].remove(next((x for x in current_config['users'] if x.name == key), None))
            else:
                # TODO password via template or generated
                if 'password' not in value:
                    value['password'] = 'dfiököjwie394rkK'
                user = NewUser(**value)
                if not dry_run:
                    art.users.create(user)
                action = 'created'

            logging.info(f"User '{key}' successfully {action}")
        except requests.exceptions.HTTPError as e:
            __log_api_error(e)

    __log_unmanaged_items("user", [item.name for item in current_config['users']])


def __apply_group_config(config_objects, current_config, dry_run: bool):
    global art
    logging.info("#####   Applying group configs   #####")

    for key, value in config_objects['groups'].items():
        logging.info(f"Processing group '{key}'")
        group = Group(**value)

        try:
            if any(x.name == key for x in current_config['groups']):
                if not dry_run:
                    art.groups.update(group)
                action = 'updated'
                current_config['groups'].remove(next((x for x in current_config['groups'] if x.name == key), None))
            else:
                if not dry_run:
                    art.groups.create(group)
                    art.groups.update(group)
                action = 'created'

            logging.info(f"Group '{key}' successfully {action}")
        except requests.exceptions.HTTPError as e:
            __log_api_error(e)

    __log_unmanaged_items("group", [item.name for item in current_config['groups']])


def __apply_permission_config(config_objects, current_config, dry_run: bool):
    global art
    logging.info("#####   Applying permission configs   #####")

    for key, value in config_objects['permissions'].items():
        logging.info(f"Processing permission '{key}'")
        permission = PermissionV2(**value)

        try:
            if any(x.name == key for x in current_config['permissions']):
                if not dry_run:
                    art.permissions.update(permission)
                action = 'updated'
                current_config['permissions'].remove(
                    next((x for x in current_config['permissions'] if x.name == key), None))
            else:
                if not dry_run:
                    art.permissions.create(permission)
                action = 'created'
            logging.info(f"Permission '{key}' successfully {action}")
        except requests.exceptions.HTTPError as e:
            __log_api_error(e)

    __log_unmanaged_items("permission", [item.name for item in current_config['permissions']])


def __apply_local_repo_config(config_objects, current_config, dry_run: bool):
    global art
    logging.info("#####   Applying local repo configs   #####")

    for key, value in config_objects.items():
        logging.info(f"Processing local repo '{key}'")
        value['key'] = key
        local_repo = LocalRepository(**value)

        try:
            if any(x.key == key for x in current_config):
                if not dry_run:
                    art.repositories.update_repo(local_repo)
                action = 'updated'
                current_config.remove(
                    next((x for x in current_config if x.key == key), None))
            else:
                if not dry_run:
                    art.repositories.create_local_repo(local_repo)
                action = 'created'
            logging.info(f"Local repo '{key}' successfully {action}")
        except requests.exceptions.HTTPError as e:
            __log_api_error(e)

    __log_unmanaged_items("local repo", [item.key for item in current_config])


def __apply_remote_repo_config(config_objects, current_config, dry_run: bool):
    global art
    logging.info("#####   Applying remote repo configs   #####")

    for key, value in config_objects.items():
        logging.info(f"Processing remote repo '{key}'")
        value['key'] = key
        remote_repo = RemoteRepository(**value)

        try:
            if any(x.key == key for x in current_config):
                if not dry_run:
                    art.repositories.update_repo(remote_repo)
                action = 'updated'
                current_config.remove(
                    next((x for x in current_config if x.key == key), None))
            else:
                if not dry_run:
                    art.repositories.create_remote_repo(remote_repo)
                action = 'created'
            logging.info(f"Remote repo '{key}' successfully {action}")
        except requests.exceptions.HTTPError as e:
            __log_api_error(e)

    __log_unmanaged_items("remote repo", [item.key for item in current_config])


def __apply_virtual_repo_config(config_objects, current_config, dry_run: bool):
    global art
    logging.info("#####   Applying virtual repo configs   #####")

    for key, value in config_objects.items():
        logging.info(f"Processing virtual repo '{key}'")
        value['key'] = key
        repo = VirtualRepository(**value)

        try:
            if any(x.key == key for x in current_config):
                if not dry_run:
                    art.repositories.update_repo(repo)
                action = 'updated'
                current_config.remove(
                    next((x for x in current_config if x.key == key), None))
            else:
                if not dry_run:
                    art.repositories.create_virtual_repo(repo)
                action = 'created'
            logging.info(f"Virtual repo '{key}' successfully {action}")
        except requests.exceptions.HTTPError as e:
            __log_api_error(e)

    __log_unmanaged_items("virtual repo", [item.key for item in current_config])


def __log_api_error(e):
    logging.error(f"Request to {e.response.url} failed with status {e.response}")
    logging.error(f"Request body: {e.request.body}")
    logging.error(f"Response: {e.response.text}")


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
    global app_config

    # Make a regex that matches if any of our regexes match.
    ignore_regex = "(" + ")|(".join(app_config.unmanaged_ignores) + ")"

    for item in items:
        if not re.match(ignore_regex, item):
            logging.info(f"Unmanaged {item_type} '{item}' found")

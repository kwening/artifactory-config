"""
Functions to create permission target files from given namespace configurations
"""
import os
import json
import logging
from dataclasses import dataclass
from json import JSONDecodeError
import yaml
from jinja2 import Template
from .helper import as_list


def _write_group(group: str, config):
    """
    Write a group json file to the config folder
    :param group: group name
    :param config: tool config
    :return: None
    """
    logging.info(f"Creating group '{group}'")

    if config.groups_output_dir:
        groups_output_dir = config.groups_output_dir
    else:
        groups_output_dir = config.output_dir + "groups/"

    file_name = groups_output_dir + group + '.json'
    if os.path.exists(file_name):
        logging.debug(f"Group config file for '${group}' already exists")
        return

    group_obj = {'name': group}

    if not os.path.isdir(groups_output_dir):
        os.makedirs(groups_output_dir)

    with open(file_name, 'w+', encoding='utf-8') as group_file:
        with open(config.group_template, encoding='utf-8') as group_template_file:
            content = group_template_file.read()
            template = Template(content)
            try:
                data = json.loads(template.render(group_obj))
                json.dump(data, group_file, indent=4, sort_keys=True)
            except JSONDecodeError as error:
                logging.warning(f"Failed to read '{config.group_template}': {error.msg}")

    logging.info(f"Writing group '{group}' to '{file_name}'")


def process_namespaces(config, local_config):
    """
    Loop over a folder with namespace configurations and create related json/yaml files
    :param config: tool config
    :param local_config:
    :return:
    """
    logging.info(f"Reading namespace definitions from '{config.namespaces_file}'")
    with open(config.namespaces_file, encoding='utf-8') as yaml_file:
        namespace_definitions = yaml.safe_load(yaml_file) or {}

    if not os.path.exists(config.output_dir + 'permissions/'):
        os.makedirs(config.output_dir + 'permissions/')

    global_internal = PermissionTarget(name="global-internal", repositories=config.internal_repos,
                                       groups=config.internal_groups, users=config.internal_users)
    global_public = PermissionTarget(name="global-public", repositories=config.internal_repos,
                                     groups=config.public_groups, users=config.public_users)
    global_internal_thirdparty = ThirdpartyPermissionTarget(name="global-internal-thirdparty",
                                                            repositories=config.thirdparty_repos,
                                                            groups=config.internal_groups,
                                                            users=config.internal_users)
    global_public_thirdparty = ThirdpartyPermissionTarget(name="global-public-thirdparty",
                                                          repositories=config.thirdparty_repos,
                                                          groups=config.public_groups,
                                                          users=config.public_users)

    namespaces_markdown = ["| Namespace | Patterns | Thirdparty-Patterns | Zugriffsberechtigung",
                           "| :--- | :--- | :--- | :--- |"]

    for _ns in namespace_definitions.get('namespaces'):
        namespace = Namespace(_ns)

        # global permissions
        global_internal.exclude_patterns.extend(namespace.restricted_patterns)
        global_public.include_patterns.extend(namespace.public_patterns)
        global_internal_thirdparty.exclude_patterns.extend(namespace.thirdparty_restricted_patterns)
        global_public_thirdparty.include_patterns.extend(namespace.thirdparty_public_patterns)

        _write_permission_target(
            PermissionTarget(namespace, repositories=config.internal_repos), config)
        _write_permission_target(
            ThirdpartyPermissionTarget(namespace, repositories=config.thirdparty_repos), config)

        # Create markdown entries
        _add_markdown_row(namespace, namespaces_markdown)

        if os.path.exists(config.group_template):
            # Check for missing groups and create them
            for group in namespace.groups:
                group_name, *_b = group.split(":")
                logging.info(f"Group in namespace found: {group_name}")
                if not local_config.get('groups').get(group_name):
                    _write_group(group_name, config)
        else:
            logging.warning(f"Group template file '{config.group_template}' doesn't exist - "
                            f"skipping group auto creation")

    # Write public permission
    _write_permission_target(global_public, config)

    # Write internal permission
    _write_permission_target(global_public_thirdparty, config)

    # Write public thirdparty permission
    _write_permission_target(global_internal, config)

    # Write internal thirdparty permission
    _write_permission_target(global_internal_thirdparty, config)

    # Write markdown doc
    write_markdown_doc(namespaces_markdown, config)


def _get_item_with_permissions(item: str):
    """
    Splits an item by ':' (if exists) and returns its name and a list of permissions
    :param item: an item, i.e. 'user:rw' or 'user'
    :return: items name and list of permissions
    """
    permission = "rwad"
    item_name = item
    permissions = []
    if ":" in item:
        (item_name, permission) = item.split(':')

    if "r" in permission:
        permissions.append("read")
    if "w" in permission:
        permissions.append("write")
    if "a" in permission:
        permissions.append("annotate")
    if "d" in permission:
        permissions.append("delete")

    return item_name, permissions


def write_markdown_doc(namespaces: list, config):
    """
    Write a list of markdown entries to a file
    :param namespaces: list of markdown formatted entries
    :param config: tool config
    :return: None
    """
    file_name = config.output_dir + 'permissions/' + 'namespaces.md'
    logging.info(f"Writing markdown doc to '{file_name}'")

    with open(file_name, 'w+', encoding='utf-8') as markdown_file:
        for entry in namespaces:
            markdown_file.write(f"{entry}\n")


@dataclass
class Namespace:
    """
    Refers to a defined namespace in the configuration
    """
    name: str
    groups: list
    users: list
    public_patterns: list
    internal_patterns: list
    restricted_patterns: list
    thirdparty_public_patterns: list
    thirdparty_internal_patterns: list
    thirdparty_restricted_patterns: list
    additional_repos: list

    def __init__(self, initial_dict=None):
        if initial_dict is None:
            initial_dict = {}
        self.name = initial_dict.get('name', '')
        self.groups = as_list(initial_dict.get('groups'))
        self.users = as_list(initial_dict.get('users'))
        self.public_patterns = as_list(initial_dict.get('publicPattern'))
        self.internal_patterns = as_list(initial_dict.get('internalPattern'))
        self.restricted_patterns = as_list(initial_dict.get('restrictedPattern'))
        self.thirdparty_public_patterns = as_list(initial_dict.get('publicThirdpartyPattern'))
        self.thirdparty_internal_patterns = as_list(initial_dict.get('internalThirdpartyPattern'))
        self.thirdparty_restricted_patterns = as_list(
            initial_dict.get('restrictedThirdpartyPattern'))
        self.additional_repos = as_list(initial_dict.get('additionalRepos'))

    def get_all_patterns(self) -> list:
        """
        Get all namespace patterns for internal repos
        :return: list of patterns
        """
        patterns = []
        patterns.extend(self.public_patterns)
        patterns.extend(self.internal_patterns)
        patterns.extend(self.restricted_patterns)
        patterns.sort()
        return patterns

    def get_all_thirdparty_patterns(self) -> list:
        """
        Get all namespace patterns for thirdparty repos
        :return: list of patterns
        """
        patterns = []
        patterns.extend(self.thirdparty_public_patterns)
        patterns.extend(self.thirdparty_internal_patterns)
        patterns.extend(self.thirdparty_restricted_patterns)
        patterns.sort()
        return patterns


@dataclass
class PermissionTarget:
    """
    Permission target for internal repos
    """
    name: str
    include_patterns: list
    exclude_patterns: list
    repositories: list
    users: dict
    groups: dict

    def __init__(self, namespace: Namespace = None, name: str = None, repositories=None, users=None,
                 groups=None):
        self.repositories = []

        if repositories is not None:
            self.repositories = repositories.copy()

        if users is None:
            self.users = {}
        else:
            self.users = dict((_get_item_with_permissions(x)) for x in users)

        if groups is None:
            self.groups = {}
        else:
            self.groups = dict((_get_item_with_permissions(x)) for x in groups)

        self.include_patterns = []
        self.exclude_patterns = []

        if namespace is not None:
            self.name = "ns-" + namespace.name
            self.users = dict((_get_item_with_permissions(x)) for x in namespace.users)
            self.groups = dict((_get_item_with_permissions(x)) for x in namespace.groups)
            self.include_patterns = namespace.get_all_patterns()

            if namespace.additional_repos:
                self.repositories.extend(namespace.additional_repos)
        elif str is not None:
            self.name = name

    def as_dict(self) -> dict:
        """
        Return the current permission target as dict
        :return: a dict with the permission targets fields
        """
        add_build_info = False

        if 'artifactory-build-info' in self.repositories:
            self.repositories.remove('artifactory-build-info')
            add_build_info = True

        permission_target = {
            'name': self.name,
            'repo': {'include-patterns': self.include_patterns,
                     'exclude-patterns': self.exclude_patterns,
                     'repositories': self.repositories,
                     'actions': {'users': self.users, 'groups': self.groups}}
        }

        if add_build_info:
            permission_target['build'] = {'include-patterns': self.include_patterns,
                                          'exclude-patterns': self.exclude_patterns,
                                          'repositories': ['artifactory-build-info'],
                                          'actions': {'users': self.users, 'groups': self.groups}}

        return permission_target


@dataclass
class ThirdpartyPermissionTarget(PermissionTarget):
    """
    Permission target for thirdparty repos
    """
    def __init__(self, namespace: Namespace = None, name: str = None, repositories=None, users=None,
                 groups=None):
        PermissionTarget.__init__(self, namespace, name, repositories, users, groups)

        if namespace is not None:
            self.name = self.name + "-thirdparty"
            self.include_patterns = namespace.get_all_thirdparty_patterns()


def _write_permission_target(permission_target: PermissionTarget, config):
    """
    Create a config file for a permission target
    :param permission_target: the permission target object
    :param config: tool config
    :return: None
    """
    if not permission_target.include_patterns and not permission_target.exclude_patterns:
        logging.info(f"Skipping permission target '{permission_target.name}'")
        return

    if config.output_format == "yaml":
        file_name = config.output_dir + 'permissions/' + permission_target.name + '.yaml'
        with open(file_name, 'w+', encoding='utf-8') as permission_file:
            yaml.dump(permission_target.as_dict(), permission_file, default_flow_style=False)
    else:
        file_name = config.output_dir + 'permissions/' + permission_target.name + '.json'
        with open(file_name, 'w+', encoding='utf-8') as permission_file:
            json.dump(permission_target.as_dict(), permission_file, indent=4, sort_keys=True)

    logging.info(f"Writing permission target '{permission_target.name}' to '{file_name}'")


def _add_markdown_row(namespace: Namespace, markdown_entries):
    """
    Create a markdown entry from a namespace object and add it to the list of markdown entries
    :param namespace: the namespace to be added
    :param markdown_entries: list of markdown entries
    :return: None
    """
    include_patterns = list(set(namespace.get_all_patterns()))
    include_patterns.sort()
    patterns = ', '.join(e.replace('*', '\\*') for e in include_patterns)

    include_patterns = list(set(namespace.get_all_thirdparty_patterns()))
    include_patterns.sort()
    thirdparty_patterns = ', '.join(e.replace('*', '\\*') for e in include_patterns)

    permissions = []

    if namespace.groups:
        permissions.append('Gruppen: ' + ', '.join(namespace.groups))
    if namespace.users:
        permissions.append('User: ' + ', '.join(namespace.users))

    markdown_entries.append(
        f"| {namespace.name} | {patterns} | {thirdparty_patterns} | {', '.join(permissions)} |")

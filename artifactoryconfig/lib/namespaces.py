import json
import logging
from dataclasses import dataclass

import yaml
import os

from .helper import as_list


def read_namespaces(config):
    logging.info(f"Reading namespace definitions from '{config.namespaces_file}'")
    with open(config.namespaces_file) as yaml_file:
        namespace_definitions = yaml.safe_load(yaml_file) or {}

    if not os.path.exists(config.output_dir):
        os.makedirs(config.output_dir)

    global_internal = PermissionTarget(name="global-internal", repositories=config.internal_repos,
                                       groups=config.internal_groups, users=config.internal_users)
    global_public = PermissionTarget(name="global-public", repositories=config.internal_repos,
                                     groups=config.public_groups, users=config.public_users)
    global_internal_thirdparty = ThirdpartyPermissionTarget(name="global-internal-thirdparty",
                                                            repositories=config.thirdparty_repos,
                                                            groups=config.internal_groups, users=config.internal_users)
    global_public_thirdparty = ThirdpartyPermissionTarget(name="global-public-thirdparty",
                                                          repositories=config.thirdparty_repos,
                                                          groups=config.public_groups, users=config.public_users)

    namespaces_markdown = [f"| Namespace | Patterns |", f"| :--- | :--- |"]

    for ns in namespace_definitions.get('namespaces'):
        namespace = Namespace(ns)

        # global permissions
        global_internal.exclude_patterns.extend(namespace.restricted_patterns)
        global_public.include_patterns.extend(namespace.public_patterns)
        global_internal_thirdparty.exclude_patterns.extend(namespace.thirdparty_restricted_patterns)
        global_public_thirdparty.include_patterns.extend(namespace.thirdparty_public_patterns)

        write_permission_target(PermissionTarget(namespace, repositories=config.internal_repos), config)
        write_permission_target(ThirdpartyPermissionTarget(namespace, repositories=config.thirdparty_repos), config)

        # Create markdown entries
        add_markdown_row(namespace, namespaces_markdown)

    # Write public permission
    write_permission_target(global_public, config)

    # Write internal permission
    write_permission_target(global_public_thirdparty, config)

    # Write public thirdparty permission
    write_permission_target(global_internal, config)

    # Write internal thirdparty permission
    write_permission_target(global_internal_thirdparty, config)

    # Write markdown doc
    write_markdown_doc(namespaces_markdown, config)


def get_write_permissions() -> list:
    return ["read", "write", "annotate", "delete"]


def write_markdown_doc(namespaces: list, config):
    file_name = config.output_dir + 'namespaces.md'
    with open(file_name, 'w+') as markdown_file:
        for entry in namespaces:
            markdown_file.write(f"{entry}\n")

    logging.info(f"Writing markdown doc to '{file_name}'")


@dataclass
class Namespace:
    name: str
    groups: list
    users: list
    public_patterns: list
    internal_patterns: list
    restricted_patterns: list
    thirdparty_public_patterns: list
    thirdparty_internal_patterns: list
    thirdparty_restricted_patterns: list

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
        self.thirdparty_restricted_patterns = as_list(initial_dict.get('restrictedThirdpartyPattern'))

    def get_all_patterns(self) -> list:
        patterns = self.public_patterns
        patterns.extend(self.internal_patterns)
        patterns.extend(self.restricted_patterns)
        patterns.sort()
        return patterns

    def get_all_thirdparty_patterns(self) -> list:
        patterns = self.thirdparty_public_patterns
        patterns.extend(self.thirdparty_internal_patterns)
        patterns.extend(self.thirdparty_restricted_patterns)
        patterns.sort()
        return patterns


@dataclass
class PermissionTarget:
    name: str
    include_patterns: list
    exclude_patterns: list
    repositories: list
    users: dict
    groups: dict

    def __init__(self, namespace: Namespace = None, name: str = None, repositories=None, users=None, groups=None):
        if repositories is None:
            self.repositories = []
        else:
            self.repositories = repositories

        if users is None:
            self.users = {}
        else:
            self.users = dict((x, get_write_permissions()) for x in users)

        if groups is None:
            self.groups = {}
        else:
            self.groups = dict((x, get_write_permissions()) for x in groups)

        self.include_patterns = []
        self.exclude_patterns = []

        if namespace is not None:
            self.name = "ns-" + namespace.name
            self.users = dict((x, get_write_permissions()) for x in namespace.users)
            self.groups = dict((x, get_write_permissions()) for x in namespace.groups)
            self.include_patterns = namespace.get_all_patterns()
        elif str is not None:
            self.name = name

    def as_dict(self) -> dict:
        return {'name': self.name,
                'repo': {'include-patterns': self.include_patterns,
                         'exclude-patterns': self.exclude_patterns,
                         'repositories': self.repositories,
                         'actions': {'users': self.users, 'groups': self.groups}}}


@dataclass
class ThirdpartyPermissionTarget(PermissionTarget):
    def __init__(self, namespace: Namespace = None, name: str = None, repositories=None, users=None, groups=None):
        PermissionTarget.__init__(self, namespace, name, repositories, users, groups)

        if namespace is not None:
            self.name = self.name + "-thirdparty"
            self.include_patterns = namespace.get_all_thirdparty_patterns()


def write_permission_target(permission_target: PermissionTarget, config):
    if not permission_target.include_patterns and not permission_target.exclude_patterns:
        logging.info(f"Skipping permission target '{permission_target.name}'")
        return

    if config.output_format == "yaml":
        file_name = config.output_dir + permission_target.name + '.yaml'
        with open(file_name, 'w+') as permission_file:
            yaml.dump(permission_target.as_dict(), permission_file, default_flow_style=False)
    else:
        file_name = config.output_dir + permission_target.name + '.json'
        with open(file_name, 'w+') as permission_file:
            json.dump(permission_target.as_dict(), permission_file, indent=4, sort_keys=True)

    logging.info(f"Writing permission target '{permission_target.name}' to '{file_name}'")


def add_markdown_row(namespace: Namespace, markdown_entries):
    include_patterns: list = namespace.get_all_patterns()
    include_patterns.extend(namespace.get_all_thirdparty_patterns())
    patterns = ', '.join(e.replace('*', '\\*') for e in include_patterns)
    markdown_entries.append(f"| {namespace.name} | {patterns} |")

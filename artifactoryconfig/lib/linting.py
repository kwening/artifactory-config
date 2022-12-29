"""
Functions to lint artifactory configs within a defined folder
"""
import abc
import logging
import sys

from .helper import LintingConfig


def lint_config(local_config, config: LintingConfig):
    """
    Run linting rules against configurations within a folder
    :param local_config: dict, containing configs from a local folder
    :param config: tool config
    :return: None
    """
    rules: list = [HelmMirrorRule(), UnusedGroupRule()]
    failed: bool = False

    for rule in rules:
        rule.run_checks(local_config)

        if rule.has_failed(config.fail_level):
            rule.print_messages()
            failed = True

    if failed:
        logging.error("!!! Linting failed - see log messages above !!!")
        sys.exit(1)


class LintingRule(abc.ABC):
    """
    Base class for all linting rules
    """
    rule_id: str = ""
    messages: list = None
    severity: int = 0

    @abc.abstractmethod
    def has_failed(self, fail_level: int) -> bool:
        """
        Check if a rules has been failed
        :param fail_level: severity to fail rule
        :return: True when failed, otherwise False
        """

    @abc.abstractmethod
    def run_checks(self, config):
        """
        Run the rule's checks
        :param config: dict with config objects
        :return: None
        """

    def print_messages(self):
        """
        Print all messages created during run_checks
        :return: None
        """
        for message in self.messages:
            logging.info(f"[{self.rule_id}] {message}")


class HelmMirrorRule(LintingRule):
    """
    Linting rule checks that each helm proxy has a corresponding mirror
    """
    def __init__(self):
        self.rule_id = "hlm.001"
        self.severity = 10
        self.messages = []

    def run_checks(self, config):
        for key, repo in config['remoteRepositories'].items():
            if repo.get('type') != 'helm':
                continue

            virtual_key = key.replace("proxy", "mirror")

            if virtual_key not in config['virtualRepositories']:
                self.messages.append(f"Helm mirror '{virtual_key}' missing for proxy '{key}'")

    def has_failed(self, fail_level) -> bool:
        return bool(self.messages) and self.severity >= fail_level


class UnusedGroupRule(LintingRule):
    """
    Linting rule searches for groups that are not used in permissions
    """
    def __init__(self):
        self.rule_id = "sec.001"
        self.severity = 20
        self.messages = []

    def run_checks(self, config):
        groups_in_permissions: list = []

        for key, perm in config['permissions'].items():
            groups = perm.get('repo').get('actions').get('groups')
            for group in groups:
                groups_in_permissions.append(group)

        for key, group in config['groups'].items():
            if key not in groups_in_permissions:
                self.messages.append(f"Group '{key}' not used in any permission")

    def has_failed(self, fail_level: int) -> bool:
        return bool(self.messages) and self.severity >= fail_level

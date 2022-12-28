import abc
import logging
import sys

from .helper import LintingConfig


def lint_config(local_config, config):
    lint_rules(local_config, config)


def lint_rules(local_config, config: LintingConfig):
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
    rule_id: str = ""
    messages: list = None
    severity: int = 0

    @abc.abstractmethod
    def has_failed(self, fail_level: int) -> bool:
        pass

    @abc.abstractmethod
    def run_checks(self, config):
        pass

    def print_messages(self):
        for message in self.messages:
            logging.info(f"[{self.rule_id}] {message}")


class HelmMirrorRule(LintingRule):
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

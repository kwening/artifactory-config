import logging

import artifactoryconfig.lib.artifactory as artifactory
import artifactoryconfig.lib.helper as helper


def test_log_unmanaged_items(caplog):
    artifactory.app_config = helper.DeployConfig()
    artifactory.app_config.unmanaged_ignores = ["abcd", "exclude.*"]
    caplog.set_level(logging.INFO)
    items = ["test", "abcd", "valid", "exclude1", "exclude2"]

    artifactory.__log_unmanaged_items("testitem", items)

    assert "testitem" in caplog.text
    assert "valid" in caplog.text
    assert "abcd" not in caplog.text
    assert "exclude1" not in caplog.text


def test_check_group_config(caplog):
    artifactory.app_config = helper.DeployConfig()
    artifactory.app_config.unmanaged_ignores = ["abcd", "exclude.*"]
    caplog.set_level(logging.INFO)
    current_config = {'groups': [
        Group("my-group"), Group("my-other-group"), Group("My-Duplicate-Group"), Group("my-duplicate-group"),
    Group("My-Group-With-Uppercase")]}

    artifactory.__check_group_config(current_config)

    assert "Group 'my-duplicate-group' found multiple times" in caplog.text
    assert "Group 'My-Duplicate-Group' has uppercase characters" in caplog.text
    assert "Group 'My-Group-With-Uppercase' has uppercase characters" in caplog.text


class Group:
    def __init__(self, name):
        self.name = name

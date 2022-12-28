import logging

import artifactoryconfig.lib.artifactory as artifactory
import artifactoryconfig.lib.helper as helper


def test_log_unmanaged_items(caplog):
    artifactory.APP_CONFIG = helper.DeployConfig()
    artifactory.APP_CONFIG.unmanaged_ignores = ["abcd", "exclude.*"]
    caplog.set_level(logging.INFO)
    items = ["test", "abcd", "valid", "exclude1", "exclude2"]

    artifactory.__log_unmanaged_items("testitem", items)

    assert "testitem" in caplog.text
    assert "valid" in caplog.text
    assert "abcd" not in caplog.text
    assert "exclude1" not in caplog.text

import logging

import artifactoryconfig.lib.helper as helper
import artifactoryconfig.lib.configreader as configreader


def test_read_vault_files(caplog):
    app_config = helper.DeployConfig()
    app_config.vault_secret = "pass"
    app_config.vault_file_list = ["./tests/resources/vault-secrets.yaml"]
    caplog.set_level(logging.INFO)
    secrets = configreader.read_vault_files(app_config)

    assert secrets['plain_chars'] == 'abcd1234'
    assert secrets['special_chars'] == 'abc-12\\3!e?".\''

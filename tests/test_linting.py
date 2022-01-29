import logging

import artifactoryconfig.lib.linting as linting
# import artifactoryconfig.lib.helper as helper


def __get_valid_config():
    return {
        'remoteRepositories': {
            'helm-remote-proxy': {
                'name': 'helm-remote-proxy',
                'type': 'helm'
            }
        },
        'virtualRepositories': {
            'helm-remote-mirror': {
                'name': 'helm-remote-mirror',
                'type': 'helm'
            }
        },
        'permissions': {},
        'groups': {}
    }


def __get_invalid_config():
    return {
        'remoteRepositories': {
            'helm-remote-proxy': {
                'name': 'helm-remote-proxy',
                'type': 'helm'
            }
        },
        'virtualRepositories': {
        },
        'permissions': {},
        'groups': {
            'unused-group': {
                'name': 'unused-group'
            }
        }
    }


def test_lint_helm_mirror_rule(caplog):
    rule = linting.HelmMirrorRule()
    # caplog.set_level(logging.INFO)

    rule.run_checks(__get_valid_config())

    assert rule.has_failed(0) is False

    rule.run_checks(__get_invalid_config())

    assert rule.has_failed(0) is True
    assert rule.has_failed(11) is False


def test_lint_unused_group_rule(caplog):
    rule = linting.UnusedGroupRule()
    # caplog.set_level(logging.INFO)

    rule.run_checks(__get_valid_config())

    assert rule.has_failed(0) is False

    rule.run_checks(__get_invalid_config())

    assert rule.has_failed(0) is True
    assert rule.has_failed(21) is False

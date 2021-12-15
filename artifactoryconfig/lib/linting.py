import logging


def lint_config(local_config):
    lint_helm_proxies(local_config)


def lint_helm_proxies(local_config):
    for repo in local_config['remoteRepositories']:
        logging.info(f"{repo.key}")
        virtual_key = repo.key.replace("proxy", "mirror")

        if virtual_key not in local_config['virtualRepositories']:
            logging.error("FAILED")

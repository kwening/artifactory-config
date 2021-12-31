import json
import logging
import os
import re
from pprint import pformat

import yaml
from glob import glob
from json import JSONDecodeError
from jinja2 import Template
from ansible.parsing.vault import VaultLib, VaultSecret


def read_configuration(app_config) -> dict:

    secrets = read_vault_files(app_config)

    config_objects = {"users": {}, "groups": {}, "permissions": {},
                      "localRepositories": {},
                      "remoteRepositories": {},
                      "virtualRepositories": {},
                      }
    for folder in app_config.config_folder:
        config_objects = read_config_folder(folder, app_config, config_objects, secrets)

    logging.debug(f"Final configuration\n{pformat(config_objects)}")
    return config_objects


def read_config_folder(config_folder: str, app_config, config_objects, secrets) -> dict:
    if not os.path.isdir(config_folder):
        logging.error(f"Config folder '{config_folder}' doesn't exist")
        exit(0)

    config_objects = read_json_configs(config_folder, config_objects, secrets)
    config_objects = read_yaml_configs(config_folder, app_config, config_objects, secrets)
    return config_objects


def read_json_configs(config_folder: str, config_objects: dict, secrets: dict) -> dict:
    """Read all json based (old) configuration files from folders users, groups and permissions and return
    dict of all found config objects
    For json each config file may contain only one object
    :param config_folder: string pointing to folder with configuration files
    :param config_objects: a dict with pre-initialized config objects
    :param secrets: a dict holding the decrypted secrets
    :return: the merged dict with all config object
    """
    types = ["users", "groups", "permissions"]

    for config_type in types:
        logging.info(f"Processing json config '{config_type}' in folder '{config_folder}'")
        for f_name in glob(f"{config_folder}/**/{config_type}/*.json", recursive=True):
            logging.info(f"Reading config file '{f_name}'")
            with open(f_name) as json_file:
                content = json_file.read()
                template = Template(content)
                try:
                    data = json.loads(template.render(secrets))
                    name = data.get("name")
                    config_objects[config_type][name] = data
                except JSONDecodeError as e:
                    logging.warning(f"Failed to read '{f_name}': {e.msg}")

    return config_objects


def read_yaml_configs(config_folder: str, config, config_objects: dict, secrets: dict) -> dict:
    """
    Read all yaml based configuration files from config folder and subfolders and return
    dict of all found config objects
    :param config_folder: the folder to read from
    :param config: the config class holding config settings
    :param secrets: dict of decoded secret variables
    :param config_objects: a dict with pre-initialized config objects
    :return: the merged dict with all config object
    """
    logging.info(f"Processing yaml configs in folder '{config_folder}'")
    for f_name in glob(f'{config_folder}/**/*.yaml', recursive=True) + glob(f'{config_folder}/*.yaml'):
        # Skip config file and vault files
        if f_name == config.config_file or f_name in config.vault_file_list:
            continue

        logging.info(f"Reading config file '{f_name}'")
        with open(f_name) as yaml_file:
            content = yaml_file.read()
            template = Template(content)
            yaml_config = yaml.safe_load(template.render(secrets)) or {}
            combined_keys = config_objects.keys() | yaml_config.keys()
            # merge dicts with keys on first level
            config_objects = {key: {**yaml_config.get(key, {}), **config_objects.get(key, {})}
                              for key in combined_keys}

    return config_objects


def read_vault_files(config) -> dict:
    """
    Read ansible vault encrypted files from a comma separated list of files
    and decrypt them with given vault secret
    :param config: the config class holding config settings
    :return: a dict with the secrets from all files
    """
    if not config.vault_file_list:
        return {}

    logging.info("Decrypting vault encrypted files")

    vault_regex = re.compile(r'(^\s*(\S*):.*\n(\s*)(\$ANSIBLE_VAULT\S*\n(\s+[0-9a-f]+\n+)*))', re.MULTILINE)
    vault = VaultLib([('default', VaultSecret(str(config.vault_secret).encode()))])
    secrets = {}

    for file in config.vault_file_list:
        logging.info(f"Decrypting secrets from '{file}'")
        with open(file, 'r') as f:
            content = f.read()
            # append newline to content so our vault_regex matches on files missing newlines at end
            content = content + "\n"
            for match in vault_regex.findall(content):
                yaml_key = match[1]
                indentation = match[2]
                value = match[3]
                logging.debug(f"Decrypting key '{yaml_key}', value: {value}")

                if vault.is_encrypted(value):
                    plain_value = vault.decrypt(value.replace(indentation, '').strip()).decode('UTF-8')
                    value = value.replace("$", f"{indentation}$")
                    value = re.escape(value)
                    plain_value = re.escape(plain_value)
                    content = re.sub(fr"{yaml_key}:.*{value}", f"{yaml_key}: {plain_value}\n", content, flags=re.DOTALL)

            new_secrets = yaml.safe_load(content) or {}
            secrets = {**secrets, **new_secrets}

    return secrets

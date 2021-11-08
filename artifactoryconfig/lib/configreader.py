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


def read_configuration(config_folder: str, vault_files: str, vault_secret: str) -> dict:
    if not os.path.isdir(config_folder):
        raise RuntimeError("Config folder doesn't exist")

    secrets = read_vault_files(vault_files, vault_secret)

    config_objects = {"users": {}, "groups": {}, "permissions": {},
                      "localRepositories": {},
                      "remoteRepositories": {},
                      "virtualRepositories": {},
                      }
    config_objects = read_json_configs(config_folder, config_objects, secrets)
    config_objects = read_yaml_configs(config_folder, config_objects, secrets)
    logging.debug(f"Final configuration\n{pformat(config_objects)}")
    return config_objects


def read_json_configs(config_folder: str, config_objects: dict, secrets: dict) -> dict:
    """
    Read all json based (old) configuration files from folders users, groups and permissions and return
    dict of all found config objects
    For json each config file may contain only one object
    :param config_folder: string pointing to folder with configuration files
    :param config_objects: a dict with pre-initialized config objects
    :return: the merged dict with all config object
    """
    types = ["users", "groups", "permissions"]

    for config_type in types:
        logging.info(f"Processing json config '{config_type}'")
        for f_name in glob(f"{config_folder}/{config_type}/*.json"):
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


def read_yaml_configs(config_folder: str, config_objects: dict, secrets: dict) -> dict:
    """
    Read all yaml based configuration files from config folder and subfolders and return
    dict of all found config objects
    :param secrets: dict of decoded secret variables
    :param config_folder: string pointing to folder with configuration files
    :param config_objects: a dict with pre-initialized config objects
    :return: the merged dict with all config object
    """
    logging.info("Processing yaml configs")
    for f_name in glob(f'{config_folder}/**/*.yaml') + glob(f'{config_folder}/*.yaml'):
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


def read_vault_files(vault_files: str, vault_secret: str) -> dict:
    """
    Read ansible vault encrypted files from a comma separated list of files
    and decrypt them with given vault secret
    :param vault_files: comma separeted list of vault encrypted files
    :param vault_secret: secret to decrypt files
    :return: a dict with the secrets from all files
    """
    if vault_files == "" or vault_secret == "":
        return {}

    logging.info("Decrypting vault encrypted files")
    secrets = {}

    vault_file_list = [x.strip() for x in vault_files.split(',')]
    vault_regex = re.compile(r'(^(\S*):.*\n(\s*)(\$ANSIBLE_VAULT\S*\n(\s+\w*\n?)*))', re.MULTILINE)
    vault = VaultLib([('default', VaultSecret(vault_secret.encode()))])

    for file in vault_file_list:
        with open(file, 'r') as f:
            content = f.read()
            for match in vault_regex.findall(content):
                yaml_key = match[1]
                indentation = match[2]
                value = match[3]

                if vault.is_encrypted(value):
                    value = vault.decrypt(value.replace(indentation, '')).decode('UTF-8')
                secrets[yaml_key] = value

    return secrets

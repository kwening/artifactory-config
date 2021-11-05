import json
import logging
import os
from pprint import pformat

import yaml
from glob import glob
from json import JSONDecodeError


def read_configuration_from_folder(config_folder: str) -> dict:
    if not os.path.isdir(config_folder):
        raise RuntimeError("Config folder doesn't exist")

    config_objects = {"users": {}, "groups": {}, "permissions": {},
                      "localRepositories": {},
                      "remoteRepositories": {},
                      "virtualRepositories": {},
                      }
    config_objects = read_json_configs(config_folder, config_objects)
    config_objects = read_yaml_configs(config_folder, config_objects)
    logging.debug(f"Final configuration\n{pformat(config_objects)}")
    return config_objects


def read_json_configs(config_folder: str, config_objects: dict) -> dict:
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
                try:
                    data = json.load(json_file)
                    name = data.get("name")
                    config_objects[config_type][name] = data
                except JSONDecodeError as e:
                    logging.warning(f"Failed to read '{f_name}': {e.msg}")

    return config_objects


def read_yaml_configs(config_folder: str, config_objects: dict) -> dict:
    """
    Read all yaml based configuration files from config folder and subfolders and return
    dict of all found config objects
    :param config_folder: string pointing to folder with configuration files
    :param config_objects: a dict with pre-initialized config objects
    :return: the merged dict with all config object
    """
    logging.info("Processing yaml configs")
    for f_name in glob(f'{config_folder}/**/*.yaml') + glob(f'{config_folder}/*.yaml'):
        logging.info(f"Reading config file '{f_name}'")
        with open(f_name) as yaml_file:
            yaml_config = yaml.safe_load(yaml_file) or {}
            combined_keys = config_objects.keys() | yaml_config.keys()
            # merge dicts with keys on first level
            config_objects = {key: {**yaml_config.get(key, {}), **config_objects.get(key, {})}
                              for key in combined_keys}

    return config_objects

# Artifactory Config

A tool to sync a local configuration (yaml, json files) with a given JFrog
Artifactory instance.

* users
* groups
* permissions
* repos (local, remote, virtual)

Ansible vault encrypted files can be read and its values can be used in Jinja2 templated files.

This app comes packaged as a Docker image and is available in Docker Hub `kwening/artifactory-config`.   
Alternatively it can be run from source as a Python script.

## Running the app

**Run docker image**

```shell
docker run -it kwening/artifactory-config
docker run -v $(pwd)/data:/data --env-file .env.docker kwening/artifactoryconfig:latest
```

**Run Python cli app**

```shell
bin/artifactoryconfig
```

### Config file (yaml)

```yaml
config_folder: data
artifactory_url: https://my.artifactory.de/artifactory
artifactory_user: myuser
artifactory_token: token
vault_files: ""
vault_secret: mysecret
vault_files_pattern: "**/secrets*.yaml"
```

### Parameters

| Parameter | Environment variable | Default value | Description |
| :--- | :--- | :--- | :--- |
| -c --config-file | CONFIG_FILE | | Path to a yaml file with configuration settings |
| --url | ARTIFACTORY_URL | | Url to the Artifactory system |
| --user | ARTIFACTORY_USER | | User to access the Artifactory system |
| --token | ARTIFACTORY_TOKEN | | Token to access the Artifactory system |
| -f --config-folder | CONFIG_FOLDER | | Folder containing config files |
| --dry-run | DRY_RUN | false | Dry run without any changes |
| --vault-files | VAULT_FILES | | Comma separated list of ansible-vault encrypted files |
| --vault-files-pattern | VAULT_FILES_PATTERN | | Pattern to define vault secret files within config folder |
| --vault-secret | VAULT_SECRET | | Secret for vault decryption |
| -q --quiet |  | | Quiet mode |
| -v --verbose |  | | Verbose mode |

Values from `config-file` can be overridden by defined cli parameters or env vars.

## Vault encrypted secrets

Secrets can be encrypted at rest by Ansible vault and decrypted at runtime.
To do so parameters `vault-secret` and `vault-files` (or `vault-files-pattern`) need to be defined.
All secrets can be referenced by their key using Jinja2 templating engine. 

## Local Development

Dependencies are managed by `pipenv`.

```shell
pipenv --python 3.9
pipenv shell
pipenv install pyartifactory
pipenv install pytest --dev
#pipenv install -e .
#pipenv update

# Create requirements.txt file (i.e. for Docker build)
pipenv lock --keep-outdated --requirements > requirements.txt

docker build -t kwening/artifactory-config:1.0.0 .
```

```shell
# Export env vars for execution
set -o allexport; source .env; set +o allexport
```

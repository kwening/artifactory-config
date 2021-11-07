FROM python:3.9-alpine
#ENV         PYTHONUNBUFFERED=1
ENV ARTIFACTORY_URL=""
ENV ARTIFACTORY_USER=""
ENV ARTIFACTORY_TOKEN=""
ENV CONFIG_FOLDER=""
ENV DRY_RUN=""
ENV VAULT_FILES=""
ENV VAULT_SECRET=""

WORKDIR /app

COPY requirements.txt .
COPY artifactoryconfig ./artifactoryconfig
COPY bin ./bin

RUN pip install -r requirements.txt && \
    rm -rf requirements.txt

USER 65534:65534

CMD [ "bin/artifactoryconfig" ]
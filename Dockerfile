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

RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
    apk add --no-cache build-base libffi-dev openssl-dev && \
    pip install -r requirements.txt && \
    apk del -r build-base libffi-dev openssl-dev && \
    rm -rf /var/cache/apk/* requirements.txt /usr/local/lib/python3.9/site-packages/ansible_collections

USER appuser

CMD [ "bin/artifactoryconfig" ]
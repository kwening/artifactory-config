FROM python:3.10-alpine AS builder
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
COPY main.spec .
COPY artifactoryconfig ./artifactoryconfig
COPY artifactoryconfig/resources/ansible ./ansible

RUN apk add --no-cache build-base libffi-dev openssl-dev && \
    pip install -r requirements.txt && \
    pip install pyinstaller && \
    pyinstaller main.spec


FROM alpine:3.15

COPY --from=builder /app/dist/main/ /app/

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

ENTRYPOINT ["/app/main"]
CMD [ "-h" ]
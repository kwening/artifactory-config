FROM python:3.9-alpine AS builder
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

RUN apk add --no-cache build-base libffi-dev openssl-dev && \
    pip install -r requirements.txt && \
    pip install pyinstaller &&\
    pyinstaller artifactoryconfig/main.py --onefile

CMD [ "bin/artifactoryconfig" ]


FROM alpine:3.15

COPY --from=builder /app/dist/main /app/main

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

ENTRYPOINT ["/app/main"]
CMD [ "-h" ]
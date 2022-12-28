#!/bin/bash
IMAGE_NAME="kwening/artifactory-config"
TAG=$(date +"%Y%m%d-%H%M%S")

echo "INFO: Re-creating requirements.txt"
poetry export -f requirements.txt --output requirements.txt

echo "INFO: Building image '$IMAGE_NAME:$TAG'"
buildah bud -t docker.io/$IMAGE_NAME:$TAG --format docker .
buildah push docker.io/$IMAGE_NAME:$TAG

echo "INFO: Image 'docker.io/$IMAGE_NAME:$TAG' successfully built"
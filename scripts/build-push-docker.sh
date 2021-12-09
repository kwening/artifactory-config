#!/bin/bash
IMAGE_NAME="kwening/artifactory-config"
TAG=$(date +"%Y%m%d-%H%M%S")

buildah bud -t docker.io/$IMAGE_NAME:$TAG --format docker .
buildah push docker.io/$IMAGE_NAME:$TAG

echo "Image docker.io/$IMAGE_NAME:$TAG successfully built"
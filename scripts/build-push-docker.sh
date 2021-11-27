#!/bin/bash

export TAG=$(date +"%Y%m%d-%H%M%S");buildah bud -t docker.io/kwening/artifactoryconfig:$TAG --format docker .
buildah push docker.io/kwening/artifactoryconfig:$TAG
#!/bin/bash

IMAGE_NAME=$1
IMAGE_TAG=${2:-latest}

GITHUB_USER=MoserMichael

if [[ $GITHUB_TOKEN == "" ]]; then
    echo "Error: missing GITHUB_TOKEN environment variable"
    Usage
fi

echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
docker push "${IMAGE_NAME}:${IMAGE_TAG}"

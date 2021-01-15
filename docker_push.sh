#!/bin/bash

echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

docker tag linkedinscraper sventhies/linkedinscraper:latest

docker push sventhies/linkedinscraper
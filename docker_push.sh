#!/bin/bash
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker tag linkedinscraper sventhies/linkedinscraper:$(git describe --abbrev=0 --tags)
docker push sventhies/linkedinscraper:$(git describe --abbrev=0 --tags)
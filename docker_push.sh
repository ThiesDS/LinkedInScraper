#!/bin/bash
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker tag linkedinscraper:$(git describe --abbrev=0 --tags) sventhies/linkedinscraper:$(git describe --abbrev=0 --tags)
docker images
docker push sventhies/linkedinscraper:$(git describe --abbrev=0 --tags)
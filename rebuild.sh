#!/usr/bin/env bash

echo ""
echo "Removing datastore image."
docker rmi rt106/rt106-datastore:latest

echo ""
echo "Building datastore image."
docker build -t rt106/rt106-datastore:latest --build-arg http_proxy=$HTTP_PROXY --build-arg https_proxy=$HTTPS_PROXY .

echo ""
docker images

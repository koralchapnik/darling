#!/bin/sh


echo "Building base image"
docker build . -f base-image.Dockerfile -t base_image:latest

echo "Building DARLING's image"

docker build . -f Dockerfile -t darling:latest
echo "Running processor container"
docker run -it -d --name darling-processor --env-file ./env --env IP=$1 --env PORT=$2 -p "$2:80" --cpus="1" --memory="4g" darling:latest python -u /cep/processor.py
echo "Running generator container"
docker run -it -d --name darling-generator --env-file ./env --env IP=$1 --env PORT=$2 --cpus="1" --memory="4g" darling:latest python -u /cep/generator.py

docker ps

#!/bin/bash
#
# Linux/Mac BASH script to build docker container
#
docker rmi trash-collection-client
docker build -t trash-collection-client .

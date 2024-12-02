#!/bin/bash
#
# Linux/Mac BASH script to run docker container
#
docker run -it -u user -w /home/user -v .:/home/user --network="host" --rm trash-collection-client bash

@echo off
REM
REM Windows BATCH script to run docker container
REM
@echo on
docker run -it -u user -w /home/user -v .:/home/user --network="host" --rm trash-collection-client bash

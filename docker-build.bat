@echo off
REM
REM Windows BATCH script to build docker container
REM
@echo on
docker rmi trash-collection-client
docker build -t trash-collection-client .

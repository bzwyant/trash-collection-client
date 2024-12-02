FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    requests \
    jsons \
    numpy \
    opencv-python-headless

# Add a user so we don't run as root
RUN useradd -m -s /bin/bash user

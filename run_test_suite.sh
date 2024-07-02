#!/bin/bash

# Define the user home directory and desktop path
USER_HOME="/home/$(whoami)"
DESKTOP_PATH="$USER_HOME/Desktop"

# Run the Docker container with the necessary privileges and volume mappings
docker run -it --privileged \
  -v /dev:/dev \
  -v $DESKTOP_PATH:/home/devuser/Desktop \
  -e USER_HOME=$USER_HOME \
  flight-controller-test-suite

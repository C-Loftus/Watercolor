### Dockerfile for the ATSPI Server


# Use a base image with Python installed
FROM ubuntu:latest

# Install the required packages
RUN apt-get update && apt-get install -y libgirepository1.0-dev gir1.2-atspi-2.0

# Set the working directory in the container
WORKDIR /app

# Copy all Python files from the current directory to the container
COPY .atspi-server/ /app/.atspi-server
COPY shared/ /app/shared

# Run the main.py script
CMD ["/usr/bin/python3", "./.atspi-server/main.py"]

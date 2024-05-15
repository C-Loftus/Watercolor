# Use a base image with Python installed
FROM python:3

# Install the required packages
RUN apt-get update && apt-get install -y python3-pyatspi

# Set the working directory in the container
WORKDIR /app

# Copy all Python files from the current directory to the container
COPY *.py /app/

# Run the main.py script
CMD ["/usr/bin/python3", "main.py"]

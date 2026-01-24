# Use a Python base image
FROM python:3.9-slim-buster

# Set working directory
WORKDIR /app

# Copy the Python script from the root of the build context
COPY node_discovery.py .

# Install dependencies
RUN pip install requests

# Command to run the script periodically
# This runs the script once every 30 minutes. Adjust as needed.
CMD ["bash", "-c", "while true; do python3 node_discovery.py; sleep 1800; done"]

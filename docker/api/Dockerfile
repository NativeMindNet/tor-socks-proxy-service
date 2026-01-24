# Use a Python base image
FROM python:3.9-slim-buster

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY api/requirements.txt .
RUN pip install --default-timeout=1000 --retries 10 -r requirements.txt

# Copy the API application code
COPY api/main.py .

# Expose the API port
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

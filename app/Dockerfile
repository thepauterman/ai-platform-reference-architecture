# Base image - slim Python to keep image size small
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy and install dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run injects PORT env var - uvicorn must listen on it
ENV PORT=8080
EXPOSE 8080

# Start the gateway service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

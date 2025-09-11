# Use a lightweight base image (Python 3.11, ARM-compatible)
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies (if needed for logging or your libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to leverage Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full app code
COPY . .

# Expose Dash app port
EXPOSE 80

# Set environment variables (can be overridden via --env-file)
ENV PYTHONUNBUFFERED=1 \
    PORT=80

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:80", "wsgi:server"]
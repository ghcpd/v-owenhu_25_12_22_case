FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create config directory
RUN mkdir -p config logs

# Copy application files
COPY input.py .
COPY input_backup.py .

# Create a non-root user to run the application
RUN useradd -m appuser && chown -R appuser:appuser /app

USER appuser

# Expose port 5000
EXPOSE 5000

# Default command
CMD ["python", "input.py"]

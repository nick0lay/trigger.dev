# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./

# Make the main script executable
RUN chmod +x ops_controller.py

# Create a non-root user
RUN useradd -m -u 1000 opscontroller && \
    chown -R opscontroller:opscontroller /app

USER opscontroller

# Default command - runs continuous monitoring
CMD ["python", "ops_controller.py"]

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Labels for documentation
LABEL maintainer="nick0lay" \
      description="Ops Controller for Trigger.dev supervisor deployment" \
      version="1.0.0"
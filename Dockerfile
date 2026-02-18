# Coder-Factory Docker Image
# Multi-stage build for optimal image size

# Stage 1: Base runtime
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Builder
FROM base AS builder

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime
FROM base AS runtime

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY . .

# Create workspace directory for generated projects
RUN mkdir -p /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_PATH=/workspace

# Entry point
ENTRYPOINT ["python", "-m", "coder_factory.cli"]
CMD ["--help"]

FROM python:3.11-slim

WORKDIR /app

# System dependencies for health checks and any future CV/image work
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy requirements from server extras (FastAPI, Uvicorn, Click)
COPY requirements-server.txt ./
RUN pip install --no-cache-dir -r requirements-server.txt

# Copy the application code
COPY src/ ./src
COPY pyproject.toml ./

# Install the auto-sdlc package itself
RUN pip install --no-cache-dir -e .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0
ENV REPORTS_DIR=/data/reports

# Create reports directory
RUN mkdir -p /data/reports

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the server
CMD ["auto-sdlc", "serve", "--host", "0.0.0.0", "--port", "8080"]

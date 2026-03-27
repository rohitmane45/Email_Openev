FROM python:3.11-slim

LABEL maintainer="Scaler Hackathon Team"
LABEL description="Email Triage MCP Environment — OpenEnv Hackathon Submission"

# Set working directory
WORKDIR /app

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start server
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]

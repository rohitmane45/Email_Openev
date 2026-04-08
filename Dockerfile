FROM python:3.11-slim

LABEL maintainer="Scaler Hackathon Team"
LABEL description="Email Triage MCP Environment — OpenEnv Hackathon Submission"

# Runtime settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=7860

# Set working directory
WORKDIR /app

# Copy requirements first (Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose default Hugging Face Spaces port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", \"7860\")}/health')" || exit 1

# Start server (Hugging Face Spaces sets PORT in some runtimes)
CMD ["sh", "-c", "exec uvicorn email_triage_env.server.app:app --host ${HOST} --port ${PORT}"]

# Dockerfile for RPG Graph VTT Service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files (build context is parent directory)
COPY rpg-graph-vtt/pyproject.toml rpg-graph-vtt/setup.py rpg-graph-vtt/README.md ./
COPY rpg-graph-vtt/rpg_graph_vtt/ ./rpg_graph_vtt/
COPY rpg-graph-vtt/web/ ./web/
COPY rpg-graph-vtt/client/ ./client/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    "neo4j>=5.0.0" \
    "pydantic>=2.0.0" \
    "pydantic-settings>=2.8.1" \
    "python-dotenv>=1.0.0" \
    "fastapi>=0.100.0" \
    "uvicorn[standard]>=0.23.0" && \
    pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/characters || exit 1

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["uvicorn", "web.server:app", "--host", "0.0.0.0", "--port", "8000"]


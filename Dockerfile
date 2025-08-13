FROM python:3.12-slim

# Install git and git-lfs for fetching LFS files
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install dependencies with uv
RUN uv pip install --system -r requirements.txt

# Copy source code
COPY . .

# Initialize git-lfs and fetch LFS files
RUN git lfs install && \
    git lfs pull || echo "Warning: Could not fetch LFS files"

# Expose port
EXPOSE 3000

# Set environment variables
ENV PORT=3000
ENV PYTHONPATH=/app

# VOYAGE_API_KEY will be provided at runtime via Smithery config
ENV VOYAGE_API_KEY=""

# Run the FastMCP server
CMD ["python", "mcp_server.py"]
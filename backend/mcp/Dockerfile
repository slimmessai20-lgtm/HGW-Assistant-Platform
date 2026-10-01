# MCP Server — standalone image (used when running MCP as a separate service)
# NOTE: in the standard docker-compose setup the MCP code is embedded in the
# backend image and launched as a subprocess via stdio. This Dockerfile exists
# as a reference / for future HTTP-based MCP deployments.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml ./
COPY mcpserver/ ./mcpserver/

# Install dependencies via uv
RUN uv sync --no-dev

ENV PYTHONUNBUFFERED=1
ENV HGW_HOST=192.168.2.254
ENV HGW_PORT=23
ENV HGW_USER=root
ENV HGW_PASSWORD=sah

CMD ["uv", "run", "mcp", "run", "mcpserver/main.py"]

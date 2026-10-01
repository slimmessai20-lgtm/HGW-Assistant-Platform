# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System dependencies for bcrypt, pymysql, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev-compat \
    libmariadb-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (needed to launch the MCP server subprocess)
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary from builder (installs to .local/bin)
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv

# Copy installed Python packages
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ ./src/
COPY prompts.yaml ./prompts.yaml

# Copy MCP server alongside the API
COPY mcp/ ./mcp/

# Install MCP dependencies into the mcp venv so uv can run it
RUN uv --directory /app/mcp sync --no-dev || true

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Docker-specific MCP paths (override default Windows paths)
ENV MCP_SERVER_PATH=/app/mcp/mcpserver/main.py
ENV MCP_DIR=/app/mcp

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

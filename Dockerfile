# syntax=docker/dockerfile:1.4

FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Add SSH config to avoid host verification prompts
RUN mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts

FROM base AS builder

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Sync dependencies with SSH access for private GitHub deps
RUN --mount=type=ssh \
    uv venv && uv sync

# Copy source code
COPY . .

# Final image
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

# Run the flask app. This will serve on port 5000. 
CMD ["python", "-m", "src.web.app"]
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy dependency files first (cache layer)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ src/

# Change ownership
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 7860

CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "7860"]

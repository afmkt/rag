# Base image with all dependencies
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies and uv in one layer for better caching
RUN apt-get update && apt-get install -y curl \
    && pip install uv \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first for better cache
COPY pyproject.toml uv.lock ./

# Install CPU-only PyTorch first to avoid CUDA dependencies
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies (cached if deps unchanged)
# Increase timeout for better reliability
ENV UV_HTTP_TIMEOUT=300
ENV UV_COMPILE_BYTECODE=0
# Retry uv sync up to 3 times in case of network issues
RUN for i in 1 2 3; do \
        if uv sync --no-install-project; then \
            break; \
        elif [ $i -eq 3 ]; then \
            echo "Failed to install dependencies after 3 attempts"; \
            exit 1; \
        else \
            echo "Attempt $i failed, retrying in 10 seconds..."; \
            sleep 10; \
        fi; \
    done

# Expose port and set default command (expects app code to be mounted)
EXPOSE 8080
CMD ["uv", "run", "python", "api.py"]
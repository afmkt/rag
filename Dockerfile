# Application image inheriting from base image
ARG BASE_IMAGE=agno:base
FROM ${BASE_IMAGE}

# Copy application code
COPY . .

# Use Docker-specific environment file
COPY .env.docker .env

EXPOSE 8080
CMD ["uv", "run", "python", "api.py"]
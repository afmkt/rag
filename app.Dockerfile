# Application code image - contains only source code
FROM busybox:latest

# Copy only the application source code and config
COPY api.py .
COPY middle.py .
COPY post.py .
COPY pre.py .
COPY qa.py .
COPY query_rag.py .
COPY rag.py .
COPY retrieval.py .
COPY test_api.py .
COPY load_data.py .
COPY init_ollama.sh .
COPY pyproject.toml .
COPY uv.lock .
COPY .env.docker .env
COPY openrouter_llm.py .

# Keep container running to provide volume
# Copy app files to volume on startup
CMD ["sh", "-c", "cp api.py middle.py post.py pre.py qa.py query_rag.py rag.py retrieval.py test_api.py load_data.py init_ollama.sh pyproject.toml uv.lock .env openrouter_llm.py /app && sleep infinity"]

# This image is meant to be used as a volume mount, not run directly
# The CMD is just for reference - actual execution happens in base image
# RAG Medical Document System

A comprehensive Retrieval-Augmented Generation (RAG) system for processing and querying medical documents including questionnaires, clinical guidance, and medical records.

## Features

- **Multi-collection RAG**: Separate vector stores for pre (questionnaires), middle (clinical guidance), and post (medical records) data
- **Document Upload**: Dynamic upload and processing of .docx files
- **Multilingual Support**: Handles both Chinese and English content
- **Context-Aware Responses**: Direct quoting from source documents with recommended actions
- **REST API**: FastAPI-based endpoints for queries and uploads
- **Docker Support**: Complete containerized deployment

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose
- At least 8GB RAM for Ollama model

### Start the System

```bash
# Clone the repository
git clone <repository-url>
cd rag-medical-system

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

The system will be available at:
- **API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Database**: localhost:5432

## Building Docker Images

The project uses completely separated base and application Docker images for maximum build efficiency.

### Architecture

- **`base.Dockerfile`** → Base images with all dependencies (system + Python packages)
- **`Dockerfile`** → Application images that **completely inherit** from base images
- **Complete separation**: Base images contain only dependencies, app images contain only application code

### Platform-Specific Builds

Build for your specific platform:

```bash
# For x64 (Intel/AMD) systems
./buildx64.sh

# For Mac M3 (Apple Silicon)
./buildm3.sh
```

### Multi-Platform Builds

Build for both platforms simultaneously:

```bash
# Build for both x64 and M3
./build.sh

# Build for specific platform only
./build.sh x64    # x64 only
./build.sh m3     # M3 only
```

### Layered Deployment (Recommended for Frequent Updates)

For production deployments where you want to update application code frequently without redeploying the heavy base image:

1. **Deploy the base image once** (~4.5GB with all dependencies)
2. **Deploy app code updates** (~7MB with only source code)

```bash
# Start with layered deployment
docker-compose --profile layered up -d

# The system will be available at:
# - API: http://localhost:8081
# - API Docs: http://localhost:8081/docs
# - Database: localhost:5432

# To update app code:
# 1. Rebuild only the app code image
docker build -f app.Dockerfile -t agno:app-x64 .
# 2. Restart the services
docker-compose --profile layered restart api-layered app-code-container
```

**Benefits:**
- Base image deployed once (4.5GB)
- App updates are tiny (7MB vs 4.5GB)
- Faster deployments and rollbacks
- Better caching for CI/CD

### Build Process

1. **Base images** are built first using `docker buildx` for cross-platform support, containing all system dependencies and Python packages
2. **Application images** are built using `docker build` and inherit from the locally built base images, adding only the application code
3. **Complete separation** ensures maximum caching - dependencies are never rebuilt unless they change
4. **Local inheritance** - App images use `docker build` to access locally loaded base images, avoiding registry pulls
5. **Size optimization** - UV package manager is configured for efficient installation without unnecessary duplication

### Troubleshooting

**Network Timeout Issues**: If you encounter network timeouts during the build (especially with `pillow` or other large packages), the build will automatically retry up to 3 times with a 5-minute timeout. If builds still fail:

- Check your internet connection
- Try building during off-peak hours
- Consider using a different network or VPN if behind restrictive firewalls

### Available Images

After building, you'll have:
- `agno:base-x64` / `agno:base-m3` - Base images with dependencies (~4.5GB)
- `agno:x64` / `agno:m3` - Full application images (~4.5GB total)
- `agno:app-x64` / `agno:app-m3` - Application code only (~7MB)

Upload your .docx files using the API endpoints:

```bash
# Upload questionnaire document
curl -X POST -F "file=@pre.docx" http://localhost:8080/upload/pre

# Upload clinical guidance document
curl -X POST -F "file=@middle.docx" http://localhost:8080/upload/middle

# Upload medical records document
curl -X POST -F "file=@post.docx" http://localhost:8080/upload/post
```

## Configuration


### LLM Model Selection (Groq)

The system now uses [Groq](https://groq.com/) for LLM inference. Configure your API key and model in the `.env` file:

```
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=mixtral-8x7b-32768
```

**Docker deployment:**
Edit `docker-compose.yml` and set the `GROQ_API_KEY` and `GROQ_MODEL` environment variables in the `api` service:

```yaml
environment:
  - GROQ_API_KEY=your-groq-api-key-here
  - GROQ_MODEL=mixtral-8x7b-32768
```

### Query the System

```bash
# Query questionnaire data
curl -X POST "http://localhost:8080/query/pre" \
  -H "Content-Type: application/json" \
  -d '{"question": "What questions are in the questionnaire?"}'

# Query clinical guidance
curl -X POST "http://localhost:8080/query/middle" \
  -H "Content-Type: application/json" \
  -d '{"question": "How to treat hypertension?"}'

# Query medical records
curl -X POST "http://localhost:8080/query/post" \
  -H "Content-Type: application/json" \
  -d '{"question": "What medical records are available?"}'
```

## Architecture

### Services

- **api**: FastAPI application with RAG endpoints
  - Built from local Dockerfile using uv for dependency management
  - Exposes REST API on port 8080
  - Depends on healthy database and Ollama services
  - Mounts data directory for persistent document storage

- **db**: PostgreSQL with pgvector extension
  - Uses pgvector/pgvector:pg16 image
  - Stores vector embeddings and metadata
  - Persistent data volume for database storage

- **ollama**: LLM service for question answering
  - Uses ollama/ollama:latest image
  - Automatically pulls and serves configured model (default: llama2:7b)
  - Persistent volume for model storage

### Data Flow

1. **Upload**: .docx files are uploaded via API endpoints
2. **Processing**: Documents are processed using docling library
3. **Storage**: Structured data is stored in JSON format
4. **Indexing**: Content is vectorized and stored in pgvector
5. **Querying**: Questions are processed through retrieval and generation pipeline

## API Endpoints

### Query Endpoints

- `POST /query/pre` - Query questionnaire data
- `POST /query/middle` - Query clinical guidance
- `POST /query/post` - Query medical records

### Upload Endpoints

- `POST /upload/pre` - Upload questionnaire document (.docx)
- `POST /upload/middle` - Upload clinical guidance document (.docx)
- `POST /upload/post` - Upload medical records document (.docx)

## Development

### Local Setup

```bash
# Install dependencies
pip install uv
uv sync

# Start PostgreSQL (using Docker)
docker run -d --name postgres -p 5432:5432 \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=mydatabase \
  pgvector/pgvector:pg16

# Start Ollama
docker run -d --name ollama -p 11434:11434 ollama/ollama

# Pull the model (use OLLAMA_MODEL env var or default llama2:7b)
docker exec ollama ollama pull ${OLLAMA_MODEL:-llama2:7b}

# Load initial data
python load_data.py

# Start the API
uv run python api.py
```

### Testing

```bash
# Run the Docker test script
./test_docker.sh

# Or test manually
curl -X POST "http://localhost:8000/query/middle" \
  -H "Content-Type: application/json" \
  -d '{"question": "How to treat hypertension?"}'
```

## Configuration

Environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `OLLAMA_BASE_URL`: Ollama service URL (default: http://localhost:11434)

## Troubleshooting

### Common Issues

1. **Model not found**: Ensure Ollama has pulled the configured model (default: `llama2:7b`). Check the `OLLAMA_MODEL` environment variable.
2. **Database connection**: Check PostgreSQL is running and accessible
3. **Memory issues**: Ensure sufficient RAM (8GB+ recommended)

### Logs

```bash
# View API logs
docker-compose logs api

# View database logs
docker-compose logs db

# View Ollama logs
docker-compose logs ollama
```

## License

[Add your license here]

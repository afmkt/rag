#!/bin/bash
# Script to initialize Ollama model

echo "Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "Waiting for Ollama..."
  sleep 2
done

# Get model name from environment variable, default to llama2:7b
OLLAMA_MODEL=${OLLAMA_MODEL:-llama2:7b}

echo "Checking if $OLLAMA_MODEL model is available..."
if ! curl -s http://localhost:11434/api/tags | grep -q "$OLLAMA_MODEL"; then
  echo "Pulling $OLLAMA_MODEL model..."
  curl -X POST http://localhost:11434/api/pull -d "{\"name\": \"$OLLAMA_MODEL\"}"
else
  echo "Model $OLLAMA_MODEL is already available"
fi

echo "Ollama initialization complete"
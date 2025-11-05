#!/bin/bash
# Test script for Docker deployment

echo "Testing Docker deployment..."

# Build and start services
echo "Building and starting services..."
docker compose up -d --build

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Check service health
echo "Checking service health..."
docker compose ps

# Test API health
echo "Testing API health..."
curl -f http://localhost:8080/docs > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ API is healthy"
else
    echo "❌ API is not healthy"
fi

# Test a simple query
echo "Testing API query..."
response=$(curl -s -X POST "http://localhost:8080/query/middle" \
  -H "Content-Type: application/json" \
  -d '{"question": "test question"}')

if echo "$response" | grep -q "answer"; then
    echo "✅ API query successful"
else
    echo "❌ API query failed"
    echo "Response: $response"
fi

echo "Test completed. Services are still running."
echo "To stop services: docker compose down"
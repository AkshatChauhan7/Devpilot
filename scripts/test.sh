#!/bin/bash
# Test runner script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running DevPilot tests..."

cd "$PROJECT_ROOT"

# Backend tests
echo "📦 Running backend tests..."
docker-compose exec -T backend pytest -v --tb=short

# Frontend tests
echo "📦 Running frontend tests..."
docker-compose exec -T frontend npm test -- --watchAll=false

echo "✅ All tests passed!"
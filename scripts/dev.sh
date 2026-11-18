#!/bin/bash
# Development startup script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting DevPilot development environment..."

# Check for .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo "📝 Please edit .env with your credentials before continuing."
    exit 1
fi

# Check required environment variables
source "$PROJECT_ROOT/.env"

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your-anthropic-api-key" ]; then
    echo "❌ ANTHROPIC_API_KEY not set in .env"
    exit 1
fi

if [ -z "$GITHUB_OAUTH_CLIENT_ID" ] || [ "$GITHUB_OAUTH_CLIENT_ID" = "your-oauth-client-id" ]; then
    echo "❌ GITHUB_OAUTH_CLIENT_ID not set in .env"
    exit 1
fi

if [ -z "$GITHUB_OAUTH_CLIENT_SECRET" ] || [ "$GITHUB_OAUTH_CLIENT_SECRET" = "your-oauth-client-secret" ]; then
    echo "❌ GITHUB_OAUTH_CLIENT_SECRET not set in .env"
    exit 1
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here-generate-with-openssl-rand-hex-32" ]; then
    echo "❌ SECRET_KEY not set in .env"
    echo "💡 Generate with: openssl rand -hex 32"
    exit 1
fi

echo "✅ Environment variables validated"

# Start services
echo "🐳 Starting Docker services..."
cd "$PROJECT_ROOT"
docker-compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T backend alembic upgrade head

echo ""
echo "✅ DevPilot is running!"
echo ""
echo "📍 Access points:"
echo "   Frontend:     http://localhost:3000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Grafana:      http://localhost:3001 (admin/admin)"
echo "   Prometheus:   http://localhost:9090"
echo ""
echo "📋 Useful commands:"
echo "   View logs:    docker-compose logs -f [service]"
echo "   Stop:         docker-compose down"
echo "   Restart:      docker-compose restart [service]"
echo "   Shell:        docker-compose exec backend bash"
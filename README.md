# DevPilot

**Autonomous AI-powered development assistant** that automates code generation, bug detection, testing, and deployment through intelligent multi-agent orchestration.

## Features

- 🤖 **Multi-Agent Orchestration** - LangGraph-powered agents for repository analysis, bug detection, code generation, and test creation
- 🔍 **Repository Intelligence** - Deep code analysis with static analysis, dependency mapping, and architecture understanding
- 🐛 **Autonomous Bug Detection** - AI-powered bug detection with severity classification and fix suggestions
- ✨ **Code Generation & Modification** - Generate new code or modify existing code from specifications
- 🧪 **Test Generation** - Automatically generate comprehensive test suites
- 🐳 **Isolated Execution** - Docker-based code execution in secure, isolated containers
- 🔀 **Pull Request Automation** - Create, manage, and merge PRs with human approval gates
- 📊 **Observability** - Prometheus metrics, Grafana dashboards, and structured logging
- 🔐 **GitHub Integration** - GitHub App and OAuth support for seamless repository access

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  Database   │
│  (Next.js)  │     │  (FastAPI)  │     │ (PostgreSQL)│
└─────────────┘     └─────────────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐ ┌──────────┐ ┌──────────┐
         │ Workers │ │ Execution│ │  Redis   │
         │(Celery) │ │ Runner   │ │  (Queue) │
         └─────────┘ └──────────┘ └──────────┘
              │            │
              ▼            ▼
         ┌────────────────────────┐
         │     Agent System       │
         │  (LangGraph + Claude)  │
         └────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- GitHub OAuth App credentials
- Anthropic API key (Claude)

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```bash
# Required
ANTHROPIC_API_KEY=your-claude-api-key
GITHUB_OAUTH_CLIENT_ID=your-github-oauth-client-id
GITHUB_OAUTH_CLIENT_SECRET=your-github-oauth-client-secret
SECRET_KEY=your-secret-key-min-32-chars

# Optional: GitHub App (for installation-based access)
GITHUB_APP_ID=your-github-app-id
GITHUB_APP_PRIVATE_KEY=your-github-app-private-key
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

### Development

Start all services:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend API on port 8000
- Frontend on port 3000
- Celery Worker
- Prometheus on port 9090
- Grafana on port 3001

Access the application:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3001 (admin/admin)

### Production Deployment

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Project Structure

```
DevPilot/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic services
│   │   ├── agents/         # LangGraph agents
│   │   ├── tasks/          # Celery tasks
│   │   └── workers/        # Worker entry points
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   ├── lib/           # Utilities
│   │   └── types/         # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── execution/             # Execution runner service
│   ├── app/
│   └── Dockerfile
├── infrastructure/        # Monitoring configs
│   ├── prometheus.yml
│   └── grafana/
├── docker-compose.yml
├── .env.example
└── README.md
```

## API Endpoints

### Authentication
- `GET /api/v1/auth/github/url` - Get GitHub OAuth URL
- `POST /api/v1/auth/github/callback` - Handle OAuth callback
- `GET /api/v1/auth/me` - Get current user

### Repositories
- `GET /api/v1/repositories` - List repositories
- `POST /api/v1/repositories` - Add repository
- `POST /api/v1/repositories/sync` - Sync from GitHub
- `POST /api/v1/repositories/{id}/analyze` - Trigger analysis

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task details
- `POST /api/v1/tasks/{id}/cancel` - Cancel task

### Executions
- `GET /api/v1/executions` - List executions
- `POST /api/v1/executions` - Create execution
- `GET /api/v1/executions/{id}` - Get execution details
- `POST /api/v1/executions/{id}/cancel` - Cancel execution

### Pull Requests
- `GET /api/v1/pull-requests` - List PRs
- `POST /api/v1/pull-requests` - Create PR
- `GET /api/v1/pull-requests/{id}` - Get PR details
- `POST /api/v1/pull-requests/{id}/merge` - Merge PR
- `POST /api/v1/pull-requests/{id}/close` - Close PR

### GitHub
- `GET /api/v1/github/user` - Get GitHub user
- `GET /api/v1/github/repositories` - List GitHub repos
- `GET /api/v1/github/repositories/{owner}/{repo}/contents` - Get file contents
- `POST /api/v1/github/repositories/{owner}/{repo}/create-file` - Create file
- `POST /api/v1/github/repositories/{owner}/{repo}/update-file` - Update file

## Agent System

DevPilot uses a multi-agent system built with LangGraph:

1. **Repository Analyzer** - Analyzes codebase structure, dependencies, and patterns
2. **Bug Detector** - Identifies bugs, security issues, and code quality problems
3. **Code Generator** - Generates new code from specifications
4. **Code Modifier** - Modifies existing code for fixes/refactoring
5. **Test Generator** - Creates comprehensive test suites

Agents communicate through a shared context and message passing system.

## Security

- All code execution happens in isolated Docker containers
- No network access for execution containers
- Read-only filesystems for execution containers
- GitHub tokens never exposed to execution environments
- Human approval required for all GitHub mutations
- JWT-based authentication with secure HTTP-only cookies

## Monitoring

- **Prometheus** metrics at `/metrics` on all services
- **Grafana** dashboards for system and business metrics
- **Structured logging** with correlation IDs
- **Health checks** at `/health` on all services

## Development

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

### Database Migrations

```bash
cd backend
alembic upgrade head
```

Create new migration:
```bash
alembic revision --autogenerate -m "description"
```

### Code Style

Backend: Black, isort, mypy
Frontend: ESLint, Prettier, TypeScript strict mode

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request
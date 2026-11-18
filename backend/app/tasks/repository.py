"""Repository analysis tasks."""
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.repository import Repository
from app.models.task import Task, TaskStatus
from app.services.repository import RepositoryService

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_repository_task(self, repository_id: int):
    """Analyze a repository for code intelligence."""
    import asyncio

    async def _analyze():
        async with get_db_context() as db:
            # Create task record
            task = Task(
                task_id=f"repo_analyze_{repository_id}",
                type="repository_analysis",
                title=f"Analyze repository {repository_id}",
                status=TaskStatus.RUNNING,
                user_id=1,  # System user
                repository_id=repository_id,
                progress=0,
                total_steps=4,
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)

            try:
                # Update progress
                task.progress = 10
                task.current_step = "Cloning repository"
                await db.commit()

                # Run analysis
                service = RepositoryService()
                await service.analyze_repository(repository_id)

                task.progress = 100
                task.current_step = "Completed"
                task.status = TaskStatus.COMPLETED
                await db.commit()

            except Exception as e:
                logger.exception("Repository analysis failed", repository_id=repository_id, error=str(e))
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                await db.commit()
                raise

    asyncio.run(_analyze())


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def sync_repositories_task(self, installation_id: int, user_id: int):
    """Sync repositories from GitHub installation."""
    import asyncio

    async def _sync():
        async with get_db_context() as db:
            task = Task(
                task_id=f"repo_sync_{installation_id}",
                type="repository_analysis",
                title=f"Sync repositories for installation {installation_id}",
                status=TaskStatus.RUNNING,
                user_id=user_id,
                progress=0,
                total_steps=3,
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)

            try:
                from app.services.github import GitHubService
                github = GitHubService()
                token = await github.get_installation_token(installation_id)
                if not token:
                    raise Exception("Failed to get installation token")

                repos = await github.get_installation_repositories(token)
                task.progress = 50
                task.current_step = f"Found {len(repos)} repositories"
                await db.commit()

                for repo_data in repos:
                    # Check if exists
                    result = await db.execute(
                        select(Repository).where(
                            Repository.github_id == repo_data["id"],
                            Repository.owner_id == user_id,
                        )
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        existing.name = repo_data["name"]
                        existing.full_name = repo_data["full_name"]
                        existing.description = repo_data.get("description")
                        existing.html_url = repo_data["html_url"]
                        existing.clone_url = repo_data["clone_url"]
                        existing.ssh_url = repo_data["ssh_url"]
                        existing.default_branch = repo_data["default_branch"]
                        existing.language = repo_data.get("language")
                        existing.stars = repo_data["stargazers_count"]
                        existing.forks = repo_data["forks_count"]
                        existing.is_private = repo_data["private"]
                        existing.is_fork = repo_data["fork"]
                        existing.is_archived = repo_data["archived"]
                        existing.installation_id = installation_id
                    else:
                        repository = Repository(
                            github_id=repo_data["id"],
                            name=repo_data["name"],
                            full_name=repo_data["full_name"],
                            description=repo_data.get("description"),
                            html_url=repo_data["html_url"],
                            clone_url=repo_data["clone_url"],
                            ssh_url=repo_data["ssh_url"],
                            default_branch=repo_data["default_branch"],
                            language=repo_data.get("language"),
                            stars=repo_data["stargazers_count"],
                            forks=repo_data["forks_count"],
                            is_private=repo_data["private"],
                            is_fork=repo_data["fork"],
                            is_archived=repo_data["archived"],
                            owner_id=user_id,
                            installation_id=installation_id,
                        )
                        db.add(repository)

                await db.commit()
                task.progress = 100
                task.current_step = "Completed"
                task.status = TaskStatus.COMPLETED
                await db.commit()

            except Exception as e:
                logger.exception("Repository sync failed", installation_id=installation_id, error=str(e))
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                await db.commit()
                raise

    asyncio.run(_sync())
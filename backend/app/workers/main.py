"""Worker entry point for background tasks."""
import asyncio
import signal
import sys
from celery import Celery

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.tasks.base import celery_app

setup_logging()
logger = get_logger(__name__)


def main():
    """Run Celery worker."""
    logger.info("Starting DevPilot worker", queues=["default", "repository", "agent", "execution"])

    # Configure worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=4",
        "--queues=default,repository,agent,execution",
        "--max-tasks-per-child=100",
        "--time-limit=3600",
        "--soft-time-limit=3000",
    ])


if __name__ == "__main__":
    main()
"""Celery configuration and base tasks."""
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Queue

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

# Setup logging for workers
setup_logging()
logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "devpilot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.repository",
        "app.tasks.agent",
        "app.tasks.execution",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 min soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    result_expires=86400,  # 24 hours
    task_routes={
        "app.tasks.repository.*": {"queue": "repository"},
        "app.tasks.agent.*": {"queue": "agent"},
        "app.tasks.execution.*": {"queue": "execution"},
    },
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("repository", routing_key="repository"),
        Queue("agent", routing_key="agent"),
        Queue("execution", routing_key="execution"),
    ),
    beat_schedule={},
)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log task start."""
    logger.info("Task started", task_name=task.name, task_id=task_id)


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Log task completion."""
    logger.info("Task completed", task_name=task.name, task_id=task_id, state=state)


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Log task failure."""
    logger.error("Task failed", task_name=sender.name, task_id=task_id, exception=str(exception))
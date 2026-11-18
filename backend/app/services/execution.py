"""Execution service for running code in isolated containers."""
import docker
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.execution import Execution, ExecutionStatus

logger = get_logger(__name__)


class ExecutionService:
    """Service for managing code execution in Docker containers."""

    def __init__(self):
        self.client = docker.DockerClient(base_url=settings.DOCKER_HOST)
        self.running_containers: Dict[str, docker.models.containers.Container] = {}

    async def queue_execution(self, execution_id: int):
        """Queue execution for processing."""
        # In production, this would be a Celery task
        asyncio.create_task(self._run_execution(execution_id))

    async def _run_execution(self, execution_id: int):
        """Run execution in Docker container."""
        async with get_db_context() as db:
            result = await db.execute(select(Execution).where(Execution.id == execution_id))
            execution = result.scalar_one_or_none()
            if not execution:
                logger.error("Execution not found", execution_id=execution_id)
                return

            execution.status = ExecutionStatus.PREPARING
            execution.started_at = datetime.now(timezone.utc)
            await db.commit()

            try:
                # Prepare container
                execution.status = ExecutionStatus.RUNNING
                await db.commit()

                # Pull image if needed
                await self._pull_image(execution.image)

                # Create and start container
                container = await self._create_container(execution)
                execution.container_id = container.id
                await db.commit()

                # Run container and capture output
                start_time = datetime.now(timezone.utc)
                result = await self._run_container(container, execution.timeout)
                end_time = datetime.now(timezone.utc)

                execution.stdout = result.get("stdout", "")
                execution.stderr = result.get("stderr", "")
                execution.exit_code = result.get("exit_code")
                execution.duration_ms = int((end_time - start_time).total_seconds() * 1000)

                if execution.exit_code == 0:
                    execution.status = ExecutionStatus.COMPLETED
                else:
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = result.get("stderr", "Execution failed")

            except asyncio.TimeoutError:
                execution.status = ExecutionStatus.TIMEOUT
                execution.error_message = f"Execution timed out after {execution.timeout} seconds"
            except Exception as e:
                logger.exception("Execution failed", execution_id=execution_id, error=str(e))
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
            finally:
                execution.completed_at = datetime.now(timezone.utc)
                await db.commit()

                # Cleanup container
                if execution.container_id:
                    await self._cleanup_container(execution.container_id)

    async def _pull_image(self, image: str):
        """Pull Docker image if not present locally."""
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:
            logger.info("Pulling image", image=image)
            self.client.images.pull(image)

    async def _create_container(self, execution: Execution) -> docker.models.containers.Container:
        """Create Docker container for execution."""
        container = self.client.containers.create(
            image=execution.image,
            command=execution.command,
            working_dir=execution.working_directory,
            environment=execution.environment or {},
            detach=True,
            stdin_open=False,
            tty=False,
            network_disabled=True,  # Security: no network access
            read_only=True,  # Security: read-only filesystem
            mem_limit=execution.memory_limit,
            cpu_count=execution.cpu_limit,
            pids_limit=100,  # Limit processes
            ulimits=[
                docker.types.Ulimit(name="nofile", soft=1024, hard=1024),
                docker.types.Ulimit(name="nproc", soft=50, hard=50),
            ],
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],
        )
        return container

    async def _run_container(
        self,
        container: docker.models.containers.Container,
        timeout: int,
    ) -> Dict[str, Any]:
        """Run container and capture output."""
        container.start()

        try:
            # Wait for container to finish with timeout
            exit_code = await asyncio.wait_for(
                asyncio.to_thread(container.wait),
                timeout=timeout,
            )

            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            return {
                "exit_code": exit_code.get("StatusCode", -1),
                "stdout": stdout,
                "stderr": stderr,
            }
        except asyncio.TimeoutError:
            # Kill container on timeout
            container.kill()
            raise

    async def _cleanup_container(self, container_id: str):
        """Clean up Docker container."""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True, v=True)
        except docker.errors.NotFound:
            pass
        except Exception as e:
            logger.warning("Failed to cleanup container", container_id=container_id, error=str(e))

    async def cancel_execution(self, execution_id: int):
        """Cancel a running execution."""
        async with get_db_context() as db:
            result = await db.execute(select(Execution).where(Execution.id == execution_id))
            execution = result.scalar_one_or_none()
            if not execution or not execution.container_id:
                return

            try:
                container = self.client.containers.get(execution.container_id)
                container.kill()
                container.remove(force=True, v=True)
            except docker.errors.NotFound:
                pass
            except Exception as e:
                logger.warning("Failed to cancel execution", execution_id=execution_id, error=str(e))

    async def get_logs(self, execution_id: int) -> List[str]:
        """Get execution logs."""
        async with get_db_context() as db:
            result = await db.execute(select(Execution).where(Execution.id == execution_id))
            execution = result.scalar_one_or_none()
            if not execution:
                return []

            logs = []
            if execution.stdout:
                logs.append(f"STDOUT:\n{execution.stdout}")
            if execution.stderr:
                logs.append(f"STDERR:\n{execution.stderr}")
            return logs

    def get_container_stats(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Get container resource usage stats."""
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            return {
                "cpu_percent": self._calculate_cpu_percent(stats),
                "memory_usage": stats["memory_stats"].get("usage", 0),
                "memory_limit": stats["memory_stats"].get("limit", 0),
                "network_rx": stats["networks"].get("eth0", {}).get("rx_bytes", 0),
                "network_tx": stats["networks"].get("eth0", {}).get("tx_bytes", 0),
            }
        except Exception:
            return None

    def _calculate_cpu_percent(self, stats: Dict[str, Any]) -> float:
        """Calculate CPU percentage from Docker stats."""
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
        if system_delta > 0 and cpu_delta > 0:
            return (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100
        return 0.0
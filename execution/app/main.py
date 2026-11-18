"""Execution service main entry point."""
import asyncio
import json
import redis.asyncio as redis
from typing import Dict, Any
import docker

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


class ExecutionWorker:
    """Worker for processing execution jobs from Redis queue."""

    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.docker_client = docker.DockerClient(base_url=settings.DOCKER_HOST)
        self.running = False

    async def start(self):
        """Start the execution worker."""
        self.running = True
        logger.info("Execution worker started")

        while self.running:
            try:
                # Pop job from queue
                job_data = await self.redis_client.brpop("execution:queue", timeout=5)
                if job_data:
                    _, job_json = job_data
                    job = json.loads(job_json)
                    await self.process_job(job)
            except Exception as e:
                logger.exception("Error in execution worker loop", error=str(e))
                await asyncio.sleep(5)

    async def stop(self):
        """Stop the execution worker."""
        self.running = False
        await self.redis_client.close()
        logger.info("Execution worker stopped")

    async def process_job(self, job: Dict[str, Any]):
        """Process an execution job."""
        execution_id = job.get("execution_id")
        logger.info("Processing execution job", execution_id=execution_id)

        # Update status to running
        await self.update_status(execution_id, "running")

        try:
            # Run execution
            result = await self.run_execution(job)

            # Update with result
            await self.update_result(execution_id, result)

        except Exception as e:
            logger.exception("Execution failed", execution_id=execution_id, error=str(e))
            await self.update_status(execution_id, "failed", error=str(e))

    async def run_execution(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Run code execution in Docker container."""
        image = job.get("image", "python:3.12-slim")
        command = job.get("command", "echo 'Hello World'")
        working_dir = job.get("working_directory", "/workspace")
        environment = job.get("environment", {})
        timeout = job.get("timeout", 300)
        cpu_limit = job.get("cpu_limit")
        memory_limit = job.get("memory_limit")

        # Pull image if needed
        try:
            self.docker_client.images.get(image)
        except docker.errors.ImageNotFound:
            logger.info("Pulling image", image=image)
            self.docker_client.images.pull(image)

        # Create container
        container = self.docker_client.containers.create(
            image=image,
            command=command,
            working_dir=working_dir,
            environment=environment,
            detach=True,
            stdin_open=False,
            tty=False,
            network_disabled=True,
            read_only=True,
            mem_limit=memory_limit,
            cpu_count=cpu_limit,
            pids_limit=100,
            ulimits=[
                docker.types.Ulimit(name="nofile", soft=1024, hard=1024),
                docker.types.Ulimit(name="nproc", soft=50, hard=50),
            ],
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],
        )

        try:
            # Start container
            container.start()

            # Wait for completion with timeout
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
                "duration_ms": 0,  # Would calculate actual duration
            }

        except asyncio.TimeoutError:
            container.kill()
            raise TimeoutError(f"Execution timed out after {timeout} seconds")
        finally:
            # Cleanup
            try:
                container.remove(force=True, v=True)
            except Exception:
                pass

    async def update_status(self, execution_id: str, status: str, error: str = None):
        """Update execution status in Redis."""
        key = f"execution:{execution_id}"
        data = {"status": status}
        if error:
            data["error"] = error
        await self.redis_client.hset(key, mapping=data)
        await self.redis_client.expire(key, 86400)  # 24 hours

    async def update_result(self, execution_id: str, result: Dict[str, Any]):
        """Update execution result in Redis."""
        key = f"execution:{execution_id}"
        data = {
            "status": "completed" if result.get("exit_code") == 0 else "failed",
            "exit_code": str(result.get("exit_code", -1)),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "duration_ms": str(result.get("duration_ms", 0)),
        }
        await self.redis_client.hset(key, mapping=data)
        await self.redis_client.expire(key, 86400)


async def main():
    """Main entry point."""
    worker = ExecutionWorker()

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))

    await worker.start()


if __name__ == "__main__":
    import signal
    asyncio.run(main())
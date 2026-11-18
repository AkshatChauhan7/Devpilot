"""Test database models."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.repository import Repository
from app.models.installation import Installation
from app.models.task import Task, TaskStatus, TaskType
from app.models.execution import Execution, ExecutionStatus
from app.models.pull_request import PullRequest, PRStatus


class TestUserModel:
    """Test User model."""

    @pytest.mark.asyncio
    async def test_create_user(self, test_session: AsyncSession):
        """Test creating a user."""
        user = User(
            github_id=12345,
            username="testuser",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        assert user.id is not None
        assert user.github_id == 12345
        assert user.username == "testuser"
        assert user.role == UserRole.USER
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_user_unique_constraints(self, test_session: AsyncSession):
        """Test user unique constraints."""
        user1 = User(github_id=1, username="user1", email="user1@example.com")
        user2 = User(github_id=1, username="user2", email="user2@example.com")

        test_session.add(user1)
        await test_session.commit()

        test_session.add(user2)
        with pytest.raises(Exception):  # Unique constraint violation
            await test_session.commit()


class TestRepositoryModel:
    """Test Repository model."""

    @pytest.mark.asyncio
    async def test_create_repository(self, test_session: AsyncSession):
        """Test creating a repository."""
        user = User(github_id=1, username="owner", email="owner@example.com")
        test_session.add(user)
        await test_session.commit()

        repo = Repository(
            github_id=123,
            name="test-repo",
            full_name="owner/test-repo",
            html_url="https://github.com/owner/test-repo",
            clone_url="https://github.com/owner/test-repo.git",
            ssh_url="git@github.com:owner/test-repo.git",
            owner_id=user.id,
        )
        test_session.add(repo)
        await test_session.commit()
        await test_session.refresh(repo)

        assert repo.id is not None
        assert repo.full_name == "owner/test-repo"
        assert repo.owner_id == user.id


class TestTaskModel:
    """Test Task model."""

    @pytest.mark.asyncio
    async def test_create_task(self, test_session: AsyncSession):
        """Test creating a task."""
        user = User(github_id=1, username="owner", email="owner@example.com")
        test_session.add(user)
        await test_session.commit()

        task = Task(
            task_id="test_001",
            type=TaskType.BUG_DETECTION,
            title="Test bug detection",
            status=TaskStatus.PENDING,
            user_id=user.id,
            progress=0,
            total_steps=3,
        )
        test_session.add(task)
        await test_session.commit()
        await test_session.refresh(task)

        assert task.id is not None
        assert task.type == TaskType.BUG_DETECTION
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0

    @pytest.mark.asyncio
    async def test_task_subtask_relationship(self, test_session: AsyncSession):
        """Test parent-child task relationship."""
        user = User(github_id=1, username="owner", email="owner@example.com")
        test_session.add(user)
        await test_session.commit()

        parent = Task(
            task_id="parent_001",
            type=TaskType.BUG_DETECTION,
            title="Parent task",
            user_id=user.id,
        )
        test_session.add(parent)
        await test_session.commit()
        await test_session.refresh(parent)

        child = Task(
            task_id="child_001",
            type=TaskType.CODE_MODIFICATION,
            title="Child task",
            user_id=user.id,
            parent_task_id=parent.id,
        )
        test_session.add(child)
        await test_session.commit()

        assert child.parent_task_id == parent.id


class TestExecutionModel:
    """Test Execution model."""

    @pytest.mark.asyncio
    async def test_create_execution(self, test_session: AsyncSession):
        """Test creating an execution."""
        execution = Execution(
            execution_id="exec_001",
            command="python test.py",
            image="python:3.12-slim",
            status=ExecutionStatus.PENDING,
            timeout=300,
        )
        test_session.add(execution)
        await test_session.commit()
        await test_session.refresh(execution)

        assert execution.id is not None
        assert execution.command == "python test.py"
        assert execution.status == ExecutionStatus.PENDING


class TestPullRequestModel:
    """Test Pull Request model."""

    @pytest.mark.asyncio
    async def test_create_pull_request(self, test_session: AsyncSession):
        """Test creating a pull request."""
        user = User(github_id=1, username="owner", email="owner@example.com")
        test_session.add(user)
        await test_session.commit()

        repo = Repository(
            github_id=123,
            name="test-repo",
            full_name="owner/test-repo",
            html_url="https://github.com/owner/test-repo",
            clone_url="https://github.com/owner/test-repo.git",
            ssh_url="git@github.com:owner/test-repo.git",
            owner_id=user.id,
        )
        test_session.add(repo)
        await test_session.commit()
        await test_session.refresh(repo)

        pr = PullRequest(
            title="Test PR",
            body="Test description",
            head_branch="feature/test",
            base_branch="main",
            status=PRStatus.DRAFT,
            repository_id=repo.id,
        )
        test_session.add(pr)
        await test_session.commit()
        await test_session.refresh(pr)

        assert pr.id is not None
        assert pr.title == "Test PR"
        assert pr.status == PRStatus.DRAFT
        assert pr.repository_id == repo.id
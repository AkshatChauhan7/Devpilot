"""Initial migration.

Revision ID: 001_initial
Revises:
Create Date: 2026-11-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('role', sa.Enum('user', 'admin', name='userrole'), nullable=False, server_default='user'),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_github_id'), 'users', ['github_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create installations table
    op.create_table(
        'installations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.Integer(), nullable=False),
        sa.Column('account_login', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('account_avatar_url', sa.Text(), nullable=True),
        sa.Column('account_html_url', sa.String(length=500), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('permissions', sa.Text(), nullable=False),
        sa.Column('events', sa.Text(), nullable=False),
        sa.Column('repository_selection', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('suspended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id'),
    )
    op.create_index(op.f('ix_installations_github_id'), 'installations', ['github_id'], unique=True)
    op.create_index(op.f('ix_installations_account_login'), 'installations', ['account_login'], unique=False)
    op.create_index(op.f('ix_installations_user_id'), 'installations', ['user_id'], unique=False)

    # Create repositories table
    op.create_table(
        'repositories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('html_url', sa.String(length=500), nullable=False),
        sa.Column('clone_url', sa.String(length=500), nullable=False),
        sa.Column('ssh_url', sa.String(length=500), nullable=False),
        sa.Column('default_branch', sa.String(length=255), nullable=False, server_default='main'),
        sa.Column('language', sa.String(length=100), nullable=True),
        sa.Column('stars', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('forks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_fork', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('installation_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analysis_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('analysis_error', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['installation_id'], ['installations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_id'),
    )
    op.create_index(op.f('ix_repositories_github_id'), 'repositories', ['github_id'], unique=True)
    op.create_index(op.f('ix_repositories_owner_id'), 'repositories', ['owner_id'], unique=False)
    op.create_index(op.f('ix_repositories_installation_id'), 'repositories', ['installation_id'], unique=False)
    op.create_index(op.f('ix_repositories_full_name'), 'repositories', ['full_name'], unique=False)
    op.create_index('ix_repository_owner_full_name', 'repositories', ['owner_id', 'full_name'], unique=False)

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=False),
        sa.Column('type', sa.Enum('repository_analysis', 'bug_detection', 'code_generation', 'code_modification', 'test_generation', 'test_execution', 'pr_creation', 'dependency_update', 'security_scan', name='tasktype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'queued', 'running', 'completed', 'failed', 'cancelled', name='taskstatus'), nullable=False, server_default='pending'),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_step', sa.String(length=255), nullable=True),
        sa.Column('total_steps', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=True),
        sa.Column('parent_task_id', sa.Integer(), nullable=True),
        sa.Column('celery_task_id', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id'),
    )
    op.create_index(op.f('ix_tasks_task_id'), 'tasks', ['task_id'], unique=True)
    op.create_index(op.f('ix_tasks_user_id'), 'tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_tasks_repository_id'), 'tasks', ['repository_id'], unique=False)
    op.create_index(op.f('ix_tasks_parent_task_id'), 'tasks', ['parent_task_id'], unique=False)
    op.create_index(op.f('ix_tasks_celery_task_id'), 'tasks', ['celery_task_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_type'), 'tasks', ['type'], unique=False)
    op.create_index('ix_task_user_status', 'tasks', ['user_id', 'status'], unique=False)
    op.create_index('ix_task_repo_status', 'tasks', ['repository_id', 'status'], unique=False)
    op.create_index('ix_task_type_status', 'tasks', ['type', 'status'], unique=False)

    # Create executions table
    op.create_table(
        'executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('pending', 'queued', 'preparing', 'running', 'completed', 'failed', 'timeout', 'cancelled', name='executionstatus'), nullable=False, server_default='pending'),
        sa.Column('command', sa.Text(), nullable=False),
        sa.Column('working_directory', sa.String(length=500), nullable=False, server_default='/workspace'),
        sa.Column('image', sa.String(length=500), nullable=False),
        sa.Column('environment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timeout', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('cpu_limit', sa.Float(), nullable=True),
        sa.Column('memory_limit', sa.String(length=50), nullable=True),
        sa.Column('stdout', sa.Text(), nullable=True),
        sa.Column('stderr', sa.Text(), nullable=True),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('repository_id', sa.Integer(), nullable=True),
        sa.Column('container_id', sa.String(length=100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('execution_id'),
    )
    op.create_index(op.f('ix_executions_execution_id'), 'executions', ['execution_id'], unique=True)
    op.create_index(op.f('ix_executions_task_id'), 'executions', ['task_id'], unique=False)
    op.create_index(op.f('ix_executions_repository_id'), 'executions', ['repository_id'], unique=False)
    op.create_index(op.f('ix_executions_status'), 'executions', ['status'], unique=False)
    op.create_index('ix_execution_task_status', 'executions', ['task_id', 'status'], unique=False)
    op.create_index('ix_execution_repo_status', 'executions', ['repository_id', 'status'], unique=False)

    # Create pull_requests table
    op.create_table(
        'pull_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('github_pr_id', sa.Integer(), nullable=True),
        sa.Column('github_pr_number', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('head_branch', sa.String(length=255), nullable=False),
        sa.Column('base_branch', sa.String(length=255), nullable=False, server_default='main'),
        sa.Column('status', sa.Enum('draft', 'open', 'closed', 'merged', 'failed', name='prstatus'), nullable=False, server_default='draft'),
        sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mergeable', sa.Boolean(), nullable=True),
        sa.Column('merge_commit_sha', sa.String(length=100), nullable=True),
        sa.Column('head_sha', sa.String(length=100), nullable=True),
        sa.Column('base_sha', sa.String(length=100), nullable=True),
        sa.Column('changes_summary', sa.Text(), nullable=True),
        sa.Column('files_changed', sa.Integer(), nullable=True),
        sa.Column('additions', sa.Integer(), nullable=True),
        sa.Column('deletions', sa.Integer(), nullable=True),
        sa.Column('review_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('merged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_pr_id'),
    )
    op.create_index(op.f('ix_pull_requests_github_pr_id'), 'pull_requests', ['github_pr_id'], unique=True)
    op.create_index(op.f('ix_pull_requests_github_pr_number'), 'pull_requests', ['github_pr_number'], unique=False)
    op.create_index(op.f('ix_pull_requests_repository_id'), 'pull_requests', ['repository_id'], unique=False)
    op.create_index(op.f('ix_pull_requests_task_id'), 'pull_requests', ['task_id'], unique=False)
    op.create_index(op.f('ix_pull_requests_status'), 'pull_requests', ['status'], unique=False)
    op.create_index('ix_pull_request_repo_status', 'pull_requests', ['repository_id', 'status'], unique=False)
    op.create_index('ix_pull_request_task', 'pull_requests', ['task_id'], unique=False)


def downgrade() -> None:
    op.drop_table('pull_requests')
    op.drop_table('executions')
    op.drop_table('tasks')
    op.drop_table('repositories')
    op.drop_table('installations')
    op.drop_table('users')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS tasktype')
    op.execute('DROP TYPE IF EXISTS executionstatus')
    op.execute('DROP TYPE IF EXISTS prstatus')
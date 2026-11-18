"""GitHub API service."""
import httpx
import jwt
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import hashlib
import hmac

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""

    BASE_URL = "https://api.github.com"
    APP_BASE_URL = "https://api.github.com/app"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        await self.client.aclose()

    def _get_headers(self, token: str, accept: str = "application/vnd.github+json") -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        return {
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # OAuth methods
    def get_oauth_url(self) -> tuple[str, str]:
        """Get GitHub OAuth authorization URL."""
        import secrets
        state = secrets.token_urlsafe(32)
        url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={settings.GITHUB_OAUTH_CLIENT_ID}"
            f"&redirect_uri={settings.NEXT_PUBLIC_API_URL}/api/v1/auth/github/callback"
            f"&scope=repo,user:email,read:org"
            f"&state={state}"
        )
        return url, state

    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange OAuth code for access token."""
        response = await self.client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_OAUTH_CLIENT_ID,
                "client_secret": settings.GITHUB_OAUTH_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        if response.status_code == 200:
            return response.json()
        logger.error("Failed to exchange code for token", status=response.status_code, response=response.text)
        return None

    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get authenticated user info."""
        response = await self.client.get(
            f"{self.BASE_URL}/user",
            headers=self._get_headers(token),
        )
        if response.status_code == 200:
            return response.json()
        logger.error("Failed to get user info", status=response.status_code)
        return None

    async def get_user_repositories(self, token: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get user repositories."""
        repos = []
        page = 1
        while True:
            response = await self.client.get(
                f"{self.BASE_URL}/user/repos",
                headers=self._get_headers(token),
                params={"per_page": per_page, "page": page, "sort": "updated"},
            )
            if response.status_code != 200:
                break
            page_repos = response.json()
            if not page_repos:
                break
            repos.extend(page_repos)
            if len(page_repos) < per_page:
                break
            page += 1
        return repos

    # GitHub App methods
    def _generate_app_jwt(self) -> str:
        """Generate GitHub App JWT."""
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": settings.GITHUB_APP_ID,
        }
        return jwt.encode(payload, settings.GITHUB_APP_PRIVATE_KEY, algorithm="RS256")

    async def get_installation_token(self, installation_id: int) -> Optional[str]:
        """Get installation access token."""
        app_jwt = self._generate_app_jwt()
        response = await self.client.post(
            f"{self.APP_BASE_URL}/installations/{installation_id}/access_tokens",
            headers=self._get_headers(app_jwt, "application/vnd.github+json"),
        )
        if response.status_code == 201:
            return response.json()["token"]
        logger.error("Failed to get installation token", installation_id=installation_id, status=response.status_code)
        return None

    async def get_installation_repositories(self, token: str) -> List[Dict[str, Any]]:
        """Get repositories for an installation."""
        repos = []
        page = 1
        while True:
            response = await self.client.get(
                f"{self.BASE_URL}/installation/repositories",
                headers=self._get_headers(token),
                params={"per_page": 100, "page": page},
            )
            if response.status_code != 200:
                break
            data = response.json()
            page_repos = data.get("repositories", [])
            if not page_repos:
                break
            repos.extend(page_repos)
            if len(page_repos) < 100:
                break
            page += 1
        return repos

    async def get_repository(self, token: str, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository details."""
        response = await self.client.get(
            f"{self.BASE_URL}/repos/{owner}/{repo}",
            headers=self._get_headers(token),
        )
        if response.status_code == 200:
            return response.json()
        return None

    async def get_contents(
        self,
        token: str,
        owner: str,
        repo: str,
        path: str = "",
        ref: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get repository contents."""
        params = {}
        if ref:
            params["ref"] = ref
        response = await self.client.get(
            f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
            headers=self._get_headers(token),
            params=params,
        )
        if response.status_code == 200:
            return response.json()
        return None

    async def get_branches(self, token: str, owner: str, repo: str) -> List[Dict[str, Any]]:
        """List repository branches."""
        branches = []
        page = 1
        while True:
            response = await self.client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/branches",
                headers=self._get_headers(token),
                params={"per_page": 100, "page": page},
            )
            if response.status_code != 200:
                break
            page_branches = response.json()
            if not page_branches:
                break
            branches.extend(page_branches)
            if len(page_branches) < 100:
                break
            page += 1
        return branches

    async def get_commits(
        self,
        token: str,
        owner: str,
        repo: str,
        sha: Optional[str] = None,
        path: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        per_page: int = 30,
    ) -> List[Dict[str, Any]]:
        """List repository commits."""
        params = {"per_page": per_page}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        response = await self.client.get(
            f"{self.BASE_URL}/repos/{owner}/{repo}/commits",
            headers=self._get_headers(token),
            params=params,
        )
        if response.status_code == 200:
            return response.json()
        return []

    async def create_branch(
        self,
        token: str,
        owner: str,
        repo: str,
        branch_name: str,
        from_branch: str = "main",
    ) -> Optional[Dict[str, Any]]:
        """Create a new branch."""
        # Get the SHA of the from_branch
        ref_response = await self.client.get(
            f"{self.BASE_URL}/repos/{owner}/{repo}/git/ref/heads/{from_branch}",
            headers=self._get_headers(token),
        )
        if ref_response.status_code != 200:
            return None

        sha = ref_response.json()["object"]["sha"]

        # Create new branch
        response = await self.client.post(
            f"{self.BASE_URL}/repos/{owner}/{repo}/git/refs",
            headers=self._get_headers(token),
            json={"ref": f"refs/heads/{branch_name}", "sha": sha},
        )
        if response.status_code == 201:
            return response.json()
        return None

    async def create_file(
        self,
        token: str,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
    ) -> Optional[Dict[str, Any]]:
        """Create a file in repository."""
        import base64
        response = await self.client.put(
            f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
            headers=self._get_headers(token),
            json={
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch,
            },
        )
        if response.status_code in (200, 201):
            return response.json()
        return None

    async def update_file(
        self,
        token: str,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: str,
    ) -> Optional[Dict[str, Any]]:
        """Update a file in repository."""
        import base64
        response = await self.client.put(
            f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
            headers=self._get_headers(token),
            json={
                "message": message,
                "content": base64.b64encode(content.encode()).decode(),
                "branch": branch,
                "sha": sha,
            },
        )
        if response.status_code in (200, 201):
            return response.json()
        return None

    async def delete_file(
        self,
        token: str,
        owner: str,
        repo: str,
        path: str,
        message: str,
        branch: str,
        sha: str,
    ) -> Optional[Dict[str, Any]]:
        """Delete a file in repository."""
        response = await self.client.delete(
            f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
            headers=self._get_headers(token),
            json={
                "message": message,
                "branch": branch,
                "sha": sha,
            },
        )
        if response.status_code == 200:
            return response.json()
        return None

    async def create_pull_request(
        self,
        token: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Create a pull request."""
        response = await self.client.post(
            f"{self.BASE_URL}/repos/{owner}/{repo}/pulls",
            headers=self._get_headers(token),
            json={
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": draft,
            },
        )
        if response.status_code == 201:
            return response.json()
        logger.error("Failed to create PR", status=response.status_code, response=response.text)
        return None

    async def merge_pull_request(
        self,
        token: str,
        owner: str,
        repo: str,
        pr_number: int,
        merge_method: str = "merge",
    ) -> Optional[Dict[str, Any]]:
        """Merge a pull request."""
        response = await self.client.put(
            f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/merge",
            headers=self._get_headers(token),
            json={"merge_method": merge_method},
        )
        if response.status_code == 200:
            return response.json()
        return None

    async def close_pull_request(
        self,
        token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> Optional[Dict[str, Any]]:
        """Close a pull request."""
        response = await self.client.patch(
            f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=self._get_headers(token),
            json={"state": "closed"},
        )
        if response.status_code == 200:
            return response.json()
        return None

    def verify_webhook_signature(self, payload: bytes, headers: Dict[str, str]) -> bool:
        """Verify GitHub webhook signature."""
        if not settings.GITHUB_WEBHOOK_SECRET:
            return True  # Skip verification if secret not set

        signature = headers.get("X-Hub-Signature-256", "")
        if not signature.startswith("sha256="):
            return False

        expected = hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)
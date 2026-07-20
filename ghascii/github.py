"""Async GitHub API client for ghascii."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from ghascii import cache


class GitHubClient:
    """Thin async wrapper around the GitHub REST API."""

    def __init__(self, token: str | None = None) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers=headers,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        ttl: int | None = None,
        **kwargs: Any,
    ) -> Any:
        req = self.client.build_request(method, path, **kwargs)
        url = str(req.url)
        if ttl:
            cached = cache.get(method, url, ttl)
            if cached is not None:
                return cached
        response = await self.client.send(req)
        response.raise_for_status()
        data = response.json()
        if ttl:
            cache.set(method, url, data)
        return data

    async def verify_token(self) -> dict:
        return await self.request("GET", "/user")

    async def list_repositories(self) -> list[dict]:
        """Return all repositories owned by the authenticated user."""
        repos: list[dict] = []
        page = 1
        while True:
            data = await self.request(
                "GET",
                "/user/repos",
                ttl=300,
                params={
                    "affiliation": "owner",
                    "sort": "updated",
                    "per_page": "100",
                    "page": str(page),
                },
            )
            if not data:
                break
            repos.extend(data)
            if len(data) < 100:
                break
            page += 1
        return repos

    async def get_default_branch(self, owner: str, repo: str) -> str:
        data = await self.request("GET", f"/repos/{owner}/{repo}", ttl=60)
        return data.get("default_branch", "main")

    async def get_latest_commit_sha(self, owner: str, repo: str, branch: str) -> str:
        data = await self.request(
            "GET",
            f"/repos/{owner}/{repo}/git/refs/heads/{branch}",
            ttl=60,
        )
        return data["object"]["sha"]

    async def get_commit_tree_sha(self, owner: str, repo: str, commit_sha: str) -> str:
        data = await self.request(
            "GET",
            f"/repos/{owner}/{repo}/git/commits/{commit_sha}",
            ttl=60,
        )
        return data["tree"]["sha"]

    async def get_tree(
        self, owner: str, repo: str, tree_sha: str, recursive: bool = True
    ) -> list[dict]:
        params = {"recursive": "1"} if recursive else {}
        data = await self.request(
            "GET",
            f"/repos/{owner}/{repo}/git/trees/{tree_sha}",
            ttl=600,
            params=params,
        )
        return data.get("tree", [])

    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str = "HEAD"
    ) -> str:
        """Fetch and decode a single file from the repository."""
        data = await self.request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            ttl=3600,
            params={"ref": ref},
        )
        if isinstance(data, list):
            raise IsADirectoryError(f"{owner}/{repo}/{path} is a directory")
        content = data.get("content", "")
        if data.get("encoding") == "base64":
            return base64.b64decode(content).decode("utf-8", errors="replace")
        return content

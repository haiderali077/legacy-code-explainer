"""
GitHub API integration service
"""

import httpx
from typing import List, Dict, Optional
from app.security.encryption import retrieve_github_token


async def get_user_repositories(github_token: str) -> List[Dict]:
    """
    Fetch user's GitHub repositories
    
    Args:
        github_token: Decrypted GitHub access token
    
    Returns:
        List of repository objects with name, url, description, etc.
    """
    
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Fetch all repos (including private ones)
    params = {
        "per_page": 100,  # Max per page
        "sort": "updated",  # Most recently updated first
        "affiliation": "owner,collaborator"  # Repos user owns or collaborates on
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise error if request failed
        
        repos = response.json()
    
    # Transform to our format
    return [
        {
            "id": repo["id"],
            "name": repo["name"],
            "full_name": repo["full_name"],
            "description": repo.get("description", ""),
            "html_url": repo["html_url"],
            "private": repo["private"],
            "language": repo.get("language"),
            "stargazers_count": repo["stargazers_count"],
            "updated_at": repo["updated_at"],
            "default_branch": repo["default_branch"]
        }
        for repo in repos
    ]


async def get_repository_details(github_token: str, owner: str, repo: str) -> Dict:
    """
    Get detailed information about a specific repository
    
    Args:
        github_token: Decrypted GitHub access token
        owner: Repository owner (username or org)
        repo: Repository name
    
    Returns:
        Detailed repository information
    """
    
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()


async def get_repository_commits_count(
    github_token: str,
    owner: str,
    repo: str,
    branch: str = "main"
) -> int:
    """
    Get total number of commits in a repository
    
    Args:
        github_token: Decrypted GitHub access token
        owner: Repository owner
        repo: Repository name
        branch: Branch name (default: main)
    
    Returns:
        Total commit count
    """
    
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    params = {
        "sha": branch,
        "per_page": 1  # We only need the count, not the data
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        # GitHub provides total count in Link header
        # For simplicity, we'll estimate from pagination
        # In production, you'd parse the Link header or use GraphQL
        
        # Quick estimate: check if there are more than 100 commits
        link_header = response.headers.get("Link", "")
        if "last" in link_header:
            # Has pagination, likely 100+ commits
            # For MVP, we'll do a rough estimate
            # You can improve this by parsing the Link header
            return 100  # Placeholder
        else:
            # Fetch all commits on first page to count
            response = await client.get(
                url,
                headers=headers,
                params={"sha": branch, "per_page": 100}
            )
            commits = response.json()
            return len(commits)


async def fetch_repository_commits(
    github_token: str,
    owner: str,
    repo: str,
    branch: str = "main",
    per_page: int = 100,
    page: int = 1
) -> List[Dict]:
    """
    Fetch commits from a GitHub repository with pagination
    
    Args:
        github_token: Decrypted GitHub access token
        owner: Repository owner
        repo: Repository name
        branch: Branch name (default: main)
        per_page: Commits per page (max 100)
        page: Page number (1-indexed)
    
    Returns:
        List of commit objects with detailed information
    """
    
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    params = {
        "sha": branch,
        "per_page": min(per_page, 100),  # GitHub max is 100
        "page": page
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        commits = response.json()
    
    # Transform to our format with key information
    return [
        {
            "sha": commit["sha"],
            "message": commit["commit"]["message"],
            "author_name": commit["commit"]["author"]["name"],
            "author_email": commit["commit"]["author"]["email"],
            "commit_date": commit["commit"]["author"]["date"],
            "html_url": commit["html_url"],
            "author_github_login": commit["author"]["login"] if commit.get("author") else None,
            "author_avatar": commit["author"]["avatar_url"] if commit.get("author") else None,
        }
        for commit in commits
    ]


async def fetch_commit_details(
    github_token: str,
    owner: str,
    repo: str,
    sha: str
) -> Dict:
    """
    Fetch detailed information about a specific commit
    
    Includes: files changed, additions, deletions, patch/diff
    
    Args:
        github_token: Decrypted GitHub access token
        owner: Repository owner
        repo: Repository name
        sha: Commit SHA
    
    Returns:
        Detailed commit object with files changed
    """
    
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        
        commit_data = response.json()
    
    # Extract file changes
    files_changed = [
        {
            "filename": file["filename"],
            "status": file["status"],  # added, removed, modified
            "additions": file["additions"],
            "deletions": file["deletions"],
            "changes": file["changes"],
            "patch": file.get("patch", "")  # Actual diff (may be large)
        }
        for file in commit_data.get("files", [])
    ]
    
    return {
        "sha": commit_data["sha"],
        "message": commit_data["commit"]["message"],
        "author_name": commit_data["commit"]["author"]["name"],
        "author_email": commit_data["commit"]["author"]["email"],
        "commit_date": commit_data["commit"]["author"]["date"],
        "html_url": commit_data["html_url"],
        "files_changed": files_changed,
        "total_additions": commit_data["stats"]["additions"],
        "total_deletions": commit_data["stats"]["deletions"],
        "total_changes": commit_data["stats"]["total"]
    }


"""
User CRUD operations
"""

from typing import List, Optional, Dict
import uuid
from datetime import datetime

users_db = {}


async def create_or_update_user(github_id: str, github_username: str, encrypted_token_ref: str, email: Optional[str] = None) -> Dict:
    """Create new user or update existing"""
    for user in users_db.values():
        if user["github_id"] == github_id:
            user["github_username"] = github_username
            user["encrypted_token_ref"] = encrypted_token_ref
            user["email"] = email
            user["last_login"] = datetime.utcnow()
            return user
    
    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "github_id": github_id,
        "github_username": github_username,
        "encrypted_token_ref": encrypted_token_ref,
        "email": email,
        "created_at": datetime.utcnow(),
        "last_login": datetime.utcnow()
    }
    users_db[user_id] = new_user
    return new_user


async def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    return users_db.get(user_id)


# Repository storage (in-memory for MVP)
repositories_db = {}

# Commits storage (in-memory for MVP)
commits_db = {}


async def create_repository(
    user_id: str,
    github_repo_id: int,
    owner: str,
    repo_name: str,
    full_name: str,
    html_url: str,
    default_branch: str = "main"
) -> Dict:
    """
    Create repository record for analysis
    
    Args:
        user_id: Owner user ID
        github_repo_id: GitHub's repository ID
        owner: Repository owner (username/org)
        repo_name: Repository name
        full_name: Full name (owner/repo)
        html_url: GitHub URL
        default_branch: Default branch name
    
    Returns:
        Repository record
    """
    import uuid
    from datetime import datetime
    
    # Check if repo already exists for this user
    for repo in repositories_db.values():
        if repo["github_repo_id"] == github_repo_id and repo["user_id"] == user_id:
            # Update existing
            repo["analysis_status"] = "pending"
            repo["analyzed_commits"] = 0
            repo["last_analyzed"] = None
            return repo
    
    # Create new repository record
    repo_id = str(uuid.uuid4())
    new_repo = {
        "id": repo_id,
        "user_id": user_id,
        "github_repo_id": github_repo_id,
        "owner": owner,
        "repo_name": repo_name,
        "full_name": full_name,
        "html_url": html_url,
        "default_branch": default_branch,
        "analysis_status": "pending",  # pending, processing, complete, failed
        "total_commits": 0,
        "analyzed_commits": 0,
        "last_analyzed": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    repositories_db[repo_id] = new_repo
    return new_repo


async def get_repository_by_id(repo_id: str) -> Optional[Dict]:
    """Get repository by ID"""
    return repositories_db.get(repo_id)


async def update_repository_status(
    repo_id: str,
    status: str,
    total_commits: int = None, # type: ignore
    analyzed_commits: int = None # type: ignore
) -> Optional[Dict]:
    """
    Update repository analysis status
    
    Args:
        repo_id: Repository ID
        status: New status (pending, processing, complete, failed)
        total_commits: Total number of commits
        analyzed_commits: Number of commits analyzed
    """
    from datetime import datetime
    
    repo = repositories_db.get(repo_id)
    if not repo:
        return None
    
    repo["analysis_status"] = status
    repo["updated_at"] = datetime.utcnow()
    
    if total_commits is not None:
        repo["total_commits"] = total_commits
    
    if analyzed_commits is not None:
        repo["analyzed_commits"] = analyzed_commits
    
    if status == "complete":
        repo["last_analyzed"] = datetime.utcnow()
    
    return repo


async def get_user_repositories(user_id: str) -> List[Dict]:
    """Get all repositories for a user"""
    return [repo for repo in repositories_db.values() if repo["user_id"] == user_id]


async def create_commit(
    repo_id: str,
    sha: str,
    message: str,
    author_name: str,
    author_email: str,
    commit_date: str,
    html_url: str,
    files_changed: List[str] = None,
    additions: int = 0,
    deletions: int = 0
) -> Dict:
    """
    Store a commit record
    
    Args:
        repo_id: Repository ID this commit belongs to
        sha: Commit SHA (unique identifier)
        message: Commit message
        author_name: Author's name
        author_email: Author's email
        commit_date: ISO format commit date
        html_url: GitHub URL for the commit
        files_changed: List of file paths modified
        additions: Lines added
        deletions: Lines deleted
    
    Returns:
        Commit record
    """
    import uuid
    from datetime import datetime
    
    # Check if commit already exists
    for commit in commits_db.values():
        if commit["sha"] == sha and commit["repo_id"] == repo_id:
            return commit  # Already stored
    
    commit_id = str(uuid.uuid4())
    new_commit = {
        "id": commit_id,
        "repo_id": repo_id,
        "sha": sha,
        "message": message,
        "author_name": author_name,
        "author_email": author_email,
        "commit_date": commit_date,
        "html_url": html_url,
        "files_changed": files_changed or [],
        "additions": additions,
        "deletions": deletions,
        "analysis_status": "pending",  # pending, analyzed, failed
        "ai_summary": None,  # Will be filled by Gemini later
        "embedding": None,  # Will be filled by sentence-transformers later
        "created_at": datetime.utcnow()
    }
    
    commits_db[commit_id] = new_commit
    return new_commit


async def get_repository_commits(repo_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    Get commits for a repository with pagination
    
    Args:
        repo_id: Repository ID
        limit: Max number of commits to return
        offset: Number of commits to skip
    
    Returns:
        List of commit records
    """
    repo_commits = [c for c in commits_db.values() if c["repo_id"] == repo_id]
    # Sort by commit date (newest first)
    repo_commits.sort(key=lambda x: x["commit_date"], reverse=True)
    return repo_commits[offset:offset + limit]


async def get_commits_count(repo_id: str) -> int:
    """Get total number of stored commits for a repository"""
    return len([c for c in commits_db.values() if c["repo_id"] == repo_id])


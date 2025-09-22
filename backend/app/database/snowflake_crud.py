"""
Snowflake-based CRUD operations
Replaces in-memory dictionaries with Snowflake tables
"""

from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json
from app.services.snowflake_service import snowflake_service
import logging

logger = logging.getLogger(__name__)


# ==================== USERS ====================

async def create_or_update_user(
    github_id: str,
    github_username: str,
    encrypted_token_ref: str,
    email: Optional[str] = None
) -> Optional[Dict]:
    """Create new user or update existing"""
    
    # Check if user exists
    existing_user = await get_user_by_github_id(github_id)
    
    if existing_user:
        # Update existing user
        query = """
        UPDATE users
        SET github_username = %s,
            encrypted_token_ref = %s,
            email = %s,
            last_login = CURRENT_TIMESTAMP()
        WHERE github_id = %s
        """
        snowflake_service.execute_query(
            query,
            params=(github_username, encrypted_token_ref, email, github_id),
            fetch=False
        )
        # Fetch updated user
        return await get_user_by_github_id(github_id)
    
    # Create new user
    user_id = str(uuid.uuid4())
    query = """
    INSERT INTO users (id, github_id, github_username, encrypted_token_ref, email)
    VALUES (%s, %s, %s, %s, %s)
    """
    snowflake_service.execute_query(
        query,
        params=(user_id, github_id, github_username, encrypted_token_ref, email),
        fetch=False
    )
    
    return await get_user_by_id(user_id)


async def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    query = "SELECT * FROM users WHERE id = %s"
    result = snowflake_service.execute_query(query, params=(user_id,), fetch=True)
    if result:
        user = dict(result[0])
        return {k.lower(): v for k, v in user.items()}
    return None


async def get_user_by_github_id(github_id: str) -> Optional[Dict]:
    """Get user by GitHub ID"""
    query = "SELECT * FROM users WHERE github_id = %s"
    result = snowflake_service.execute_query(query, params=(github_id,), fetch=True)
    if result:
        user = dict(result[0])
        return {k.lower(): v for k, v in user.items()}
    return None


# ==================== REPOSITORIES ====================

async def create_repository(
    user_id: str,
    github_repo_id: int,
    owner: str,
    repo_name: str,
    full_name: str,
    html_url: str,
    default_branch: str = "main"
) -> Optional[Dict]:
    """Create repository record for analysis"""
    
    # Check if repo already exists for this user
    existing_repo = await get_repository_by_github_id(user_id, github_repo_id)
    
    if existing_repo:
        # Reset analysis status
        query = """
        UPDATE repositories
        SET analysis_status = 'pending',
            analyzed_commits = 0,
            updated_at = CURRENT_TIMESTAMP()
        WHERE id = %s
        """
        snowflake_service.execute_query(
            query,
            params=(existing_repo["id"],),
            fetch=False
        )
        # Fetch updated repository
        return await get_repository_by_id(existing_repo["id"])
    
    # Create new repository
    repo_id = str(uuid.uuid4())
    query = """
    INSERT INTO repositories (
        id, user_id, github_repo_id, owner, repo_name,
        full_name, html_url, default_branch, analysis_status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    snowflake_service.execute_query(
        query,
        params=(repo_id, user_id, github_repo_id, owner, repo_name, full_name, html_url, default_branch, "pending"),
        fetch=False
    )
    
    return await get_repository_by_id(repo_id)


async def get_repository_by_id(repo_id: str) -> Optional[Dict]:
    """Get repository by ID"""
    query = "SELECT * FROM repositories WHERE id = %s"
    result = snowflake_service.execute_query(query, params=(repo_id,), fetch=True)
    
    if result:
        # Convert Snowflake column names (uppercase) to lowercase
        repo = dict(result[0])
        return {k.lower(): v for k, v in repo.items()}
    return None


async def get_repository_by_github_id(user_id: str, github_repo_id: int) -> Optional[Dict]:
    """Get repository by GitHub repo ID and user"""
    query = "SELECT * FROM repositories WHERE user_id = %s AND github_repo_id = %s"
    result = snowflake_service.execute_query(query, params=(user_id, github_repo_id), fetch=True)
    
    if result:
        repo = dict(result[0])
        return {k.lower(): v for k, v in repo.items()}
    return None


async def update_repository_status(
    repo_id: str,
    status: str,
    total_commits: Optional[int] = None,
    analyzed_commits: Optional[int] = None
) -> Optional[Dict]:
    """Update repository analysis status"""
    
    update_fields = ["analysis_status = %s", "updated_at = CURRENT_TIMESTAMP()"]
    params: List[Any] = [status]
    
    if total_commits is not None:
        update_fields.append("total_commits = %s")
        params.append(total_commits)
    
    if analyzed_commits is not None:
        update_fields.append("analyzed_commits = %s")
        params.append(analyzed_commits)
    
    if status == "complete":
        update_fields.append("last_analyzed = CURRENT_TIMESTAMP()")
    
    params.append(repo_id)
    
    query = f"""
    UPDATE repositories
    SET {', '.join(update_fields)}
    WHERE id = %s
    """
    snowflake_service.execute_query(query, params=tuple(params), fetch=False)
    
    return await get_repository_by_id(repo_id)


async def get_user_repositories(user_id: str) -> List[Dict]:
    """Get all repositories for a user"""
    query = "SELECT * FROM repositories WHERE user_id = %s ORDER BY updated_at DESC"
    results = snowflake_service.execute_query(query, params=(user_id,), fetch=True)
    
    return [{k.lower(): v for k, v in dict(row).items()} for row in results] if results else []


# ==================== COMMITS ====================

async def create_commit(
    repo_id: str,
    sha: str,
    message: str,
    author_name: str,
    author_email: str,
    commit_date: str,
    html_url: str,
    files_changed: Optional[List[str]] = None,
    additions: int = 0,
    deletions: int = 0
) -> Optional[Dict]:
    """Store a commit record"""
    
    # Check if commit already exists
    query_check = "SELECT * FROM commits_analysis WHERE repo_id = %s AND sha = %s"
    existing = snowflake_service.execute_query(query_check, params=(repo_id, sha), fetch=True)
    
    if existing:
        result = dict(existing[0])
        return {k.lower(): v for k, v in result.items()}
    
    # Create new commit
    commit_id = str(uuid.uuid4())
    
    # For VARIANT columns, use SELECT with PARSE_JSON instead of VALUES
    files_json = json.dumps(files_changed or [])
    
    query = """
    INSERT INTO commits_analysis (
        id, repo_id, sha, message, author_name, author_email,
        commit_date, html_url, files_changed, additions, deletions, analysis_status
    )
    SELECT %s, %s, %s, %s, %s, %s, %s, %s, PARSE_JSON(%s), %s, %s, %s
    """
    snowflake_service.execute_query(
        query,
        params=(commit_id, repo_id, sha, message, author_name, author_email,
                commit_date, html_url, files_json, additions, deletions, "pending"),
        fetch=False
    )
    
    return await get_commit_by_id(commit_id)


async def get_commit_by_id(commit_id: str) -> Optional[Dict]:
    """Get commit by ID"""
    query = "SELECT * FROM commits_analysis WHERE id = %s"
    result = snowflake_service.execute_query(query, params=(commit_id,), fetch=True)
    
    if result:
        commit = dict(result[0])
        commit_dict = {k.lower(): v for k, v in commit.items()}
        # Parse JSON array back to list
        if commit_dict.get("files_changed"):
            commit_dict["files_changed"] = json.loads(commit_dict["files_changed"])
        return commit_dict
    return None


async def get_commit_by_sha(repo_id: str, sha: str) -> Optional[Dict]:
    """Get commit by SHA"""
    query = "SELECT * FROM commits_analysis WHERE repo_id = %s AND sha = %s"
    result = snowflake_service.execute_query(query, params=(repo_id, sha), fetch=True)
    
    if result:
        commit = dict(result[0])
        commit_dict = {k.lower(): v for k, v in commit.items()}
        if commit_dict.get("files_changed"):
            commit_dict["files_changed"] = json.loads(commit_dict["files_changed"])
        return commit_dict
    return None


async def update_commit_ai_summary(commit_id: str, ai_summary: str) -> Optional[Dict]:
    """Update commit with AI-generated summary"""
    query = """
    UPDATE commits_analysis
    SET ai_summary = %s,
        analysis_status = 'analyzed'
    WHERE id = %s
    """
    snowflake_service.execute_query(query, params=(ai_summary, commit_id), fetch=False)
    return await get_commit_by_id(commit_id)


async def update_commit_embedding(commit_id: str, embedding: List[float]) -> Optional[Dict]:
    """Update commit with vector embedding"""
    embedding_str = json.dumps(embedding)
    query = """
    UPDATE commits_analysis
    SET embedding = PARSE_JSON(%s)::VECTOR(FLOAT, 768)
    WHERE id = %s
    """
    snowflake_service.execute_query(query, params=(embedding_str, commit_id), fetch=False)
    return await get_commit_by_id(commit_id)


async def get_repository_commits(repo_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get commits for a repository with pagination"""
    query = """
    SELECT * FROM commits_analysis
    WHERE repo_id = %s
    ORDER BY commit_date DESC
    LIMIT %s OFFSET %s
    """
    results = snowflake_service.execute_query(query, params=(repo_id, limit, offset), fetch=True)
    
    commits = []
    if results:
        for row in results:
            commit = {k.lower(): v for k, v in dict(row).items()}
            if commit.get("files_changed"):
                try:
                    commit["files_changed"] = json.loads(commit["files_changed"])
                except:
                    commit["files_changed"] = []
            commits.append(commit)
    
    return commits


async def get_commits_count(repo_id: str) -> int:
    """Get total number of stored commits for a repository"""
    query = "SELECT COUNT(*) as count FROM commits_analysis WHERE repo_id = %s"
    result = snowflake_service.execute_query(query, params=(repo_id,), fetch=True)
    return result[0]["COUNT"] if result else 0


async def search_commits_by_vector(
    repo_id: str,
    query_embedding: List[float],
    limit: int = 5
) -> List[Dict]:
    """
    Vector similarity search for commits
    
    Args:
        repo_id: Repository ID
        query_embedding: Query vector embedding
        limit: Number of results to return
    
    Returns:
        List of most similar commits with similarity scores
    """
    embedding_str = json.dumps(query_embedding)
    
    query = """
    SELECT *,
           VECTOR_COSINE_SIMILARITY(embedding, PARSE_JSON(%s)::VECTOR(FLOAT, 768)) as similarity
    FROM commits_analysis
    WHERE repo_id = %s
      AND embedding IS NOT NULL
    ORDER BY similarity DESC
    LIMIT %s
    """
    
    results = snowflake_service.execute_query(
        query,
        params=(embedding_str, repo_id, limit),
        fetch=True
    )
    
    commits = []
    if results:
        for row in results:
            commit = {k.lower(): v for k, v in dict(row).items()}
            if commit.get("files_changed"):
                try:
                    commit["files_changed"] = json.loads(commit["files_changed"])
                except:
                    commit["files_changed"] = []
            commits.append(commit)
    
    return commits

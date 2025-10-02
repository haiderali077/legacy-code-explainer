"""
Repository management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from pydantic import BaseModel
import httpx
import logging
from app.security.auth import get_current_user
from app.services.github_service import (
    get_user_repositories,
    get_repository_commits_count,
    fetch_repository_commits,
    fetch_commit_details
)
from app.services.gemini_service import build_prompt, polish_commits
from app.database.snowflake_crud import (
    get_user_by_id,
    create_repository,
    get_repository_by_id,
    update_repository_status,
    create_commit,
    get_repository_commits,
    get_commits_count
)
from app.security.encryption import retrieve_github_token

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalyzeRepositoryRequest(BaseModel):
    """Request model for repository analysis"""
    owner: str
    repo_name: str
    full_name: str
    github_repo_id: int
    html_url: str
    default_branch: str = "main"


@router.get("/repositories")
async def list_repositories(current_user: dict = Depends(get_current_user)):
    """
    List all GitHub repositories accessible to the authenticated user
    
    Requires: JWT authentication
    
    Returns:
        List of repositories with basic info
    """
    
    try:
        # Get user from database to retrieve their encrypted GitHub token
        user = await get_user_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Decrypt GitHub token
        github_token = await retrieve_github_token(user["encrypted_token_ref"])
        
        # Fetch repositories from GitHub API
        repositories = await get_user_repositories(github_token)
        
        return {
            "count": len(repositories),
            "repositories": repositories
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e.response.status_code}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching repositories: {str(e)}"
        )


@router.post("/repositories/analyze")
async def analyze_repository(
    request: AnalyzeRepositoryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Start analyzing a GitHub repository
    
    This will:
    1. Save repository info to database
    2. Fetch commit count
    3. Queue background analysis job (TODO: implement worker)
    4. Return analysis status
    
    Requires: JWT authentication
    
    Body:
        owner: Repository owner (username/org)
        repo_name: Repository name
        full_name: Full name (owner/repo)
        github_repo_id: GitHub's repository ID
        html_url: Repository URL
        default_branch: Default branch (default: main)
    
    Returns:
        Repository analysis record with status
    """
    
    try:
        # Get user from database
        user = await get_user_by_id(current_user["user_id"])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Decrypt GitHub token
        github_token = await retrieve_github_token(user["encrypted_token_ref"])
        
        # Check if repository already exists in database
        from app.database.snowflake_crud import get_repository_by_github_id
        existing_repo = await get_repository_by_github_id(
            user_id=current_user["user_id"],
            github_repo_id=request.github_repo_id
        )
        
        if existing_repo:
            # Repository already exists - return existing record
            logger.info(f"Repository {request.full_name} already exists in database")
            
            # Get current commit count to check if it's already analyzed
            stored_commits = await get_commits_count(existing_repo["id"])
            
            return {
                "message": "Repository already exists" if stored_commits > 0 else "Repository found, no commits yet",
                "already_analyzed": stored_commits > 0,
                "repository": {
                    "id": existing_repo["id"],
                    "full_name": existing_repo["full_name"],
                    "analysis_status": existing_repo["analysis_status"],
                    "total_commits": existing_repo["total_commits"],
                    "analyzed_commits": existing_repo["analyzed_commits"],
                    "created_at": existing_repo["created_at"].isoformat()
                }
            }
        
        # Create repository record in database (new repository)
        repository = await create_repository(
            user_id=current_user["user_id"],
            github_repo_id=request.github_repo_id,
            owner=request.owner,
            repo_name=request.repo_name,
            full_name=request.full_name,
            html_url=request.html_url,
            default_branch=request.default_branch
        )
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create repository record"
            )
        
        # Get commit count from GitHub
        try:
            commit_count = await get_repository_commits_count(
                github_token,
                request.owner,
                request.repo_name,
                request.default_branch
            )
            
            # Update repository with commit count
            updated_repo = await update_repository_status(
                repository["id"],
                status="pending",
                total_commits=commit_count,
                analyzed_commits=0
            )
            if updated_repo:
                repository = updated_repo
        except Exception as e:
            # If we can't get commit count, that's okay, continue anyway
            commit_count = 0
        
        # TODO: Trigger background job to analyze commits
        # For now, we just return the pending status
        # In next steps, we'll implement:
        # - Background worker to fetch commits
        # - Send commits to Gemini for analysis
        # - Store embeddings in Snowflake
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create repository record"
            )
        
        return {
            "message": "Repository queued for analysis",
            "repository": {
                "id": repository["id"],
                "full_name": repository["full_name"],
                "analysis_status": repository["analysis_status"],
                "total_commits": repository["total_commits"],
                "analyzed_commits": repository["analyzed_commits"],
                "created_at": repository["created_at"].isoformat()
            }
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e.response.status_code}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting repository analysis: {str(e)}"
        )


@router.get("/repositories/{repo_id}/status")
async def get_repository_status(
    repo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get repository analysis status and progress
    
    Returns current analysis status, progress percentage,
    and detailed information about the repository.
    
    Requires: JWT authentication
    
    Path Parameters:
        repo_id: Repository ID (UUID)
    
    Returns:
        Repository status with analysis progress
    """
    
    try:
        # Get repository from database
        repository = await get_repository_by_id(repo_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Verify repository belongs to authenticated user
        if repository["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this repository"
            )
        
        # Calculate progress percentage
        progress = 0.0
        if repository["total_commits"] > 0:
            progress = (repository["analyzed_commits"] / repository["total_commits"]) * 100
        
        # Determine if analysis is complete
        is_complete = repository["analysis_status"] == "complete"
        
        # Format response
        return {
            "id": repository["id"],
            "full_name": repository["full_name"],
            "owner": repository["owner"],
            "repo_name": repository["repo_name"],
            "html_url": repository["html_url"],
            "analysis_status": repository["analysis_status"],
            "total_commits": repository["total_commits"],
            "analyzed_commits": repository["analyzed_commits"],
            "progress_percentage": round(progress, 2),
            "is_complete": is_complete,
            "created_at": repository["created_at"].isoformat(),
            "last_analyzed": repository["last_analyzed"].isoformat() if repository["last_analyzed"] else None,
            "updated_at": repository["updated_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching repository status: {str(e)}"
        )


@router.post("/repositories/{repo_id}/fetch-commits")
async def fetch_commits(
    repo_id: str,
    page: int = 1,
    per_page: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch commits from GitHub and store them in the database
    
    This endpoint fetches commits page by page from GitHub's API
    and stores them locally. You can call this multiple times to
    paginate through all commits.
    
    Requires: JWT authentication
    
    Path Parameters:
        repo_id: Repository ID (UUID)
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Commits per page, max 100 (default: 100)
    
    Returns:
        Fetched commits and pagination info
    """
    
    try:
        # Get repository from database
        repository = await get_repository_by_id(repo_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Verify repository belongs to authenticated user
        if repository["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this repository"
            )
        
        # Get user's GitHub token
        user = await get_user_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        github_token = await retrieve_github_token(user["encrypted_token_ref"])
        
        # Fetch commits from GitHub (basic info)
        commits = await fetch_repository_commits(
            github_token,
            repository["owner"],
            repository["repo_name"],
            repository["default_branch"],
            per_page,
            page
        )
        
        # Store commits in database
        stored_commits = []
        skipped_commits = 0
        
        for commit in commits:
            # Check if commit already exists to avoid re-analysis
            from app.database.snowflake_crud import get_commit_by_sha
            existing_commit = await get_commit_by_sha(repo_id, commit["sha"])
            
            if existing_commit:
                logger.info(f"⏭️  Skipping already analyzed commit {commit['sha'][:7]}")
                skipped_commits += 1
                stored_commits.append({
                    "id": existing_commit["id"],
                    "sha": existing_commit["sha"][:7],
                    "message": existing_commit["message"][:80],
                    "author": existing_commit["author_name"],
                    "date": existing_commit["commit_date"],
                    "files_changed": len(existing_commit.get("files_changed", [])) if existing_commit.get("files_changed") else 0,
                    "additions": existing_commit.get("additions", 0),
                    "deletions": existing_commit.get("deletions", 0),
                    "has_ai_summary": existing_commit.get("ai_summary") is not None,
                    "skipped": True
                })
                continue
            
            # Fetch detailed commit information (includes files, additions, deletions)
            detailed_commit = None
            files_changed = []
            additions = 0
            deletions = 0
            ai_summary = None
            
            try:
                detailed_commit = await fetch_commit_details(
                    github_token,
                    repository["owner"],
                    repository["repo_name"],
                    commit["sha"]
                )
                
                # Extract just filenames for the files_changed array
                files_changed = [file["filename"] for file in detailed_commit["files_changed"]]
                additions = detailed_commit["total_additions"]
                deletions = detailed_commit["total_deletions"]
                
                # Generate AI summary using Snowflake Cortex (fast, integrated)
                try:
                    from app.services.snowflake_service import generate_commit_summary_cortex
                    ai_summary = generate_commit_summary_cortex(detailed_commit)
                    logger.info(f"✅ Generated Cortex summary for commit {commit['sha'][:7]}")
                except Exception as cortex_error:
                    logger.warning(f"⚠️ Cortex summary generation failed for {commit['sha'][:7]}: {cortex_error}")
                    ai_summary = None
                    # Continue without AI summary - not critical
                
            except Exception as e:
                # If detailed fetch fails, use basic info
                logger.warning(f"⚠️ Could not fetch details for commit {commit['sha'][:7]}: {e}")
                files_changed = []
                additions = 0
                deletions = 0
            
            stored_commit = await create_commit(
                repo_id=repo_id,
                sha=commit["sha"],
                message=commit["message"],
                author_name=commit["author_name"],
                author_email=commit["author_email"],
                commit_date=commit["commit_date"],
                html_url=commit["html_url"],
                files_changed=files_changed,
                additions=additions,
                deletions=deletions
            )
            
            # If we have an AI summary and the commit was stored, update it
            if stored_commit and ai_summary:
                try:
                    from app.database.snowflake_crud import update_commit_ai_summary
                    await update_commit_ai_summary(stored_commit["id"], ai_summary)
                    logger.info(f"✅ Stored AI summary for commit {stored_commit['sha'][:7]}")
                except Exception as update_error:
                    logger.warning(f"⚠️ Failed to update AI summary: {update_error}")
            
            if stored_commit:
                stored_commits.append({
                    "id": stored_commit["id"],
                    "sha": stored_commit["sha"][:7],  # Short SHA
                    "message": stored_commit["message"][:80],  # Truncate long messages
                    "author": stored_commit["author_name"],
                    "date": stored_commit["commit_date"],
                    "files_changed": len(files_changed),
                    "additions": additions,
                    "deletions": deletions,
                    "has_ai_summary": ai_summary is not None,
                    "skipped": False
                })
        
        # Get total stored commits count
        total_stored = await get_commits_count(repo_id)
        
        # Update repository status
        await update_repository_status(
            repo_id,
            status="processing",
            analyzed_commits=total_stored
        )
        
        return {
            "page": page,
            "per_page": per_page,
            "fetched": len(commits),
            "new_commits": len(commits) - skipped_commits,
            "skipped_commits": skipped_commits,
            "total_stored": total_stored,
            "has_more": len(commits) == per_page,  # If we got full page, likely more exist
            "commits": stored_commits,
            "next_page": page + 1 if len(commits) == per_page else None
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e.response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching commits: {str(e)}"
        )


@router.get("/repositories/{repo_id}/commits")
async def list_commits(
    repo_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    List stored commits for a repository
    
    Returns commits that have been fetched from GitHub and
    stored locally. Use /fetch-commits to fetch more commits.
    
    Requires: JWT authentication
    
    Path Parameters:
        repo_id: Repository ID (UUID)
    
    Query Parameters:
        limit: Max commits to return (default: 50)
        offset: Number of commits to skip (default: 0)
    
    Returns:
        List of commits with pagination info
    """
    
    try:
        # Get repository from database
        repository = await get_repository_by_id(repo_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Verify repository belongs to authenticated user
        if repository["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this repository"
            )
        
        # Get commits from database
        commits = await get_repository_commits(repo_id, limit, offset)
        total_count = await get_commits_count(repo_id)
        
        # Format response
        commits_list = [
            {
                "id": commit["id"],
                "sha": commit["sha"],
                "sha_short": commit["sha"][:7],
                "message": commit["message"],
                "ai_summary": commit["ai_summary"],  # Include AI summary
                "author_name": commit["author_name"],
                "author_email": commit["author_email"],
                "commit_date": commit["commit_date"],
                "html_url": commit["html_url"],
                "files_changed_count": len(commit["files_changed"]),
                "additions": commit["additions"],
                "deletions": commit["deletions"],
                "analysis_status": commit["analysis_status"],
                "has_ai_summary": commit["ai_summary"] is not None
            }
            for commit in commits
        ]
        
        return {
            "repository": {
                "id": repository["id"],
                "full_name": repository["full_name"]
            },
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "returned": len(commits_list),
                "has_more": offset + len(commits_list) < total_count
            },
            "commits": commits_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing commits: {str(e)}"
        )


@router.get("/repositories/{repo_id}/commits/{commit_sha}/details")
async def get_commit_details(
    repo_id: str,
    commit_sha: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch detailed information about a specific commit from GitHub
    
    This fetches fresh data from GitHub including file changes,
    diffs, and statistics. Useful for getting detailed info on demand.
    
    Requires: JWT authentication
    
    Path Parameters:
        repo_id: Repository ID (UUID)
        commit_sha: Commit SHA (can be short form like 'abc123' or full)
    
    Returns:
        Detailed commit information with file changes
    """
    
    try:
        # Get repository from database
        repository = await get_repository_by_id(repo_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Verify repository belongs to authenticated user
        if repository["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this repository"
            )
        
        # Get user's GitHub token
        user = await get_user_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        github_token = await retrieve_github_token(user["encrypted_token_ref"])
        
        # Fetch commit details from GitHub
        commit_details = await fetch_commit_details(
            github_token,
            repository["owner"],
            repository["repo_name"],
            commit_sha
        )
        
        return {
            "repository": repository["full_name"],
            "commit": commit_details
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e.response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching commit details: {str(e)}"
        )


@router.post("/repositories/{repo_id}/enrich-commits")
async def enrich_existing_commits(
    repo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Enrich existing commits with detailed file information
    
    This endpoint fetches detailed information (files changed, additions, deletions)
    for commits that were stored with basic info only. Useful for updating old commits.
    
    Requires: JWT authentication
    
    Path Parameters:
        repo_id: Repository ID (UUID)
    
    Returns:
        Number of commits enriched
    """
    
    try:
        # Get repository from database
        repository = await get_repository_by_id(repo_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Verify repository belongs to authenticated user
        if repository["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this repository"
            )
        
        # Get user's GitHub token
        user = await get_user_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        github_token = await retrieve_github_token(user["encrypted_token_ref"])
        
        # Get all commits for this repository from database
        commits = await get_repository_commits(repo_id)
        
        enriched_count = 0
        failed_count = 0
        
        for commit in commits:
            # Skip if commit already has file data
            if commit.get("additions", 0) > 0 or (commit.get("files_changed") and len(commit["files_changed"]) > 2):
                continue
            
            try:
                # Fetch detailed commit information from GitHub
                detailed_commit = await fetch_commit_details(
                    github_token,
                    repository["owner"],
                    repository["repo_name"],
                    commit["sha"]
                )
                
                # Extract just filenames for the files_changed array
                files_changed = [file["filename"] for file in detailed_commit["files_changed"]]
                
                # Generate AI summary from code changes
                ai_summary = None
                try:
                    from app.services.gemini_service import generate_commit_summary
                    ai_summary = generate_commit_summary(detailed_commit)
                except Exception as gemini_error:
                    logger.warning(f"⚠️ AI summary generation failed for {commit['sha'][:7]}: {gemini_error}")
                
                # Update the commit in database
                from app.services.snowflake_service import snowflake_service
                
                update_query = """
                UPDATE commits_analysis
                SET 
                    files_changed = PARSE_JSON(%s),
                    additions = %s,
                    deletions = %s,
                    ai_summary = %s
                WHERE id = %s
                """
                
                import json
                snowflake_service.execute_query(
                    update_query,
                    params=(
                        json.dumps(files_changed),
                        detailed_commit["total_additions"],
                        detailed_commit["total_deletions"],
                        ai_summary,
                        commit["id"]
                    ),
                    fetch=False
                )
                
                enriched_count += 1
                
            except Exception as e:
                failed_count += 1
                continue
        
        return {
            "repository": repository["full_name"],
            "total_commits": len(commits),
            "enriched": enriched_count,
            "failed": failed_count,
            "message": f"Successfully enriched {enriched_count} commits with file details"
        }
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commit not found"
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e.response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching commit details: {str(e)}"
        )


@router.post("/repositories/{repo_id}/commits/{commit_sha}/enhance")
async def enhance_commit_message(
    repo_id: str,
    commit_sha: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate AI-enhanced commit message using Gemini
    
    Takes a commit and generates a professional, detailed commit message
    following conventional commits style using Gemini AI.
    
    Requires: JWT authentication
    
    Path Parameters:
        repo_id: Repository ID (UUID)
        commit_sha: Commit SHA (can be short form)
    
    Returns:
        Original and AI-enhanced commit messages
    """
    
    try:
        # Get repository from database
        repository = await get_repository_by_id(repo_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Verify repository belongs to authenticated user
        if repository["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this repository"
            )
        
        # Get user's GitHub token
        user = await get_user_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        github_token = await retrieve_github_token(user["encrypted_token_ref"])
        
        # Fetch commit details from GitHub
        commit_details = await fetch_commit_details(
            github_token,
            repository["owner"],
            repository["repo_name"],
            commit_sha
        )
        
        # Prepare commit data for gemini service
        commit_data = {
            "message": commit_details["message"],
            "lines_added": commit_details["total_additions"],
            "lines_deleted": commit_details["total_deletions"]
        }
        
        # Use teammate's gemini service functions
        polished_commits = polish_commits([commit_data])
        ai_message = polished_commits[0]["ai_message"]
        
        # Update commit record in database with AI summary
        from app.database.snowflake_crud import get_commit_by_sha, update_commit_ai_summary
        
        commit_record = await get_commit_by_sha(repo_id, commit_details["sha"])
        if commit_record:
            await update_commit_ai_summary(commit_record["id"], ai_message.strip())
        
        return {
            "original_message": commit_details["message"],
            "ai_enhanced_message": ai_message.strip(),
            "commit_sha": commit_details["sha"],
            "stats": {
                "files_changed": len(commit_details["files_changed"]),
                "additions": commit_details["total_additions"],
                "deletions": commit_details["total_deletions"]
            }
        }
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commit not found"
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e.response.status_code}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enhancing commit message: {str(e)}"
        )


@router.post("/repositories/{repo_id}/commits/batch-enhance")
async def batch_enhance_commits(
    repo_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate AI-enhanced messages for multiple commits at once
    
    Processes up to 'limit' commits and generates AI-enhanced messages
    for all of them. Useful for batch processing.
    
    Requires: JWT authentication
    
    Path Parameters:
        repo_id: Repository ID (UUID)
    
    Query Parameters:
        limit: Max commits to process (default: 10, max: 50)
    
    Returns:
        List of enhanced commits with original and AI messages
    """
    
    try:
        # Limit to prevent abuse
        limit = min(limit, 50)
        
        # Get repository from database
        repository = await get_repository_by_id(repo_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Verify repository belongs to authenticated user
        if repository["user_id"] != current_user["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this repository"
            )
        
        # Get commits that haven't been analyzed yet
        commits = await get_repository_commits(repo_id, limit=limit)
        pending_commits = [c for c in commits if c["analysis_status"] == "pending"][:limit]
        
        if not pending_commits:
            return {
                "message": "No pending commits to enhance",
                "processed": 0,
                "results": []
            }
        
        # Get user's GitHub token
        user = await get_user_by_id(current_user["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        github_token = await retrieve_github_token(user["encrypted_token_ref"])
        
        results = []
        
        for commit in pending_commits:
            try:
                # Fetch full commit details from GitHub
                commit_details = await fetch_commit_details(
                    github_token,
                    repository["owner"],
                    repository["repo_name"],
                    commit["sha"]
                )
                
                # Prepare commit data for gemini service
                commit_data = {
                    "message": commit["message"],
                    "lines_added": commit_details["total_additions"],
                    "lines_deleted": commit_details["total_deletions"]
                }
                
                # Use teammate's gemini service function
                polished = polish_commits([commit_data])
                ai_message = polished[0]["ai_message"]
                
                # Update commit in database
                commit["ai_summary"] = ai_message.strip()
                commit["analysis_status"] = "analyzed"
                
                results.append({
                    "sha": commit["sha"][:7],
                    "original": commit["message"],
                    "ai_enhanced": ai_message.strip(),
                    "status": "success"
                })
                
            except Exception as e:
                results.append({
                    "sha": commit["sha"][:7],
                    "original": commit["message"],
                    "error": str(e),
                    "status": "failed"
                })
        
        return {
            "message": f"Processed {len(results)} commits",
            "processed": len(results),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error batch enhancing commits: {str(e)}"
        )



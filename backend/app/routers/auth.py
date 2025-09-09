"""
Authentication router - GitHub OAuth and session management
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import secrets
import httpx
from datetime import timedelta

from app.core.github_config import (
    get_github_oauth_url,
    GITHUB_ACCESS_TOKEN_URL,
    GITHUB_USER_API_URL
)
from app.core.config import settings
from app.security.auth import create_access_token, get_current_user
from app.security.encryption import encrypt_github_token, store_encrypted_token
from app.security.rate_limiter import rate_limit
from app.services.redis_service import get_redis_client
from app.database.snowflake_crud import create_or_update_user

router = APIRouter()

# In-memory fallback for OAuth state (dev only; production uses Redis)
_oauth_states_fallback = {}


@router.get("/github", dependencies=[Depends(rate_limit(10, 60))])
async def github_login():
    """
    Initiate GitHub OAuth flow
    
    Returns authorization URL for frontend to redirect to
    """
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    redis_client = get_redis_client()
    if redis_client:
        redis_client.setex(f"oauth_state:{state}", 600, "1")
    else:
        _oauth_states_fallback[state] = True
    
    auth_url = get_github_oauth_url(state)
    
    return {
        "auth_url": auth_url,
        "message": "Redirect user to this URL for GitHub authentication"
    }


@router.get("/github/callback", dependencies=[Depends(rate_limit(10, 60))])
async def github_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(..., description="State parameter for CSRF protection")
):
    """
    GitHub OAuth callback handler
    
    Steps:
    1. Verify state parameter
    2. Exchange code for access token
    3. Fetch user info from GitHub
    4. Encrypt and store token with 1Password
    5. Create user in database
    6. Generate JWT session token
    7. Return JWT to frontend
    """
    
    # Step 1: Verify state (Redis or in-memory fallback)
    redis_client = get_redis_client()
    if redis_client:
        result = redis_client.getdel(f"oauth_state:{state}")
        if not result:
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    else:
        if state not in _oauth_states_fallback:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        del _oauth_states_fallback[state]
    
    # Step 2: Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GITHUB_ACCESS_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.github_redirect_uri
            },
            headers={"Accept": "application/json"}
        )
    
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token")
    
    token_data = token_response.json()
    github_access_token = token_data.get("access_token")
    
    if not github_access_token:
        raise HTTPException(status_code=400, detail="No access token received")
    
    # Step 3: Fetch user info from GitHub
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            GITHUB_USER_API_URL,
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json"
            }
        )
    
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")
    
    github_user = user_response.json()
    
    # Step 4: Encrypt and store token
    encrypted_token_ref = await store_encrypted_token(
        user_id=str(github_user["id"]),
        token=github_access_token
    )
    
    # Step 5: Create or update user in database
    user = await create_or_update_user(
        github_id=str(github_user["id"]),
        github_username=github_user["login"],
        encrypted_token_ref=encrypted_token_ref,
        email=github_user.get("email")
    )
    
    # Step 6: Generate JWT session token
    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "github_id": user["github_id"],
            "github_username": user["github_username"]
        },
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Step 7: Redirect to frontend with token in URL fragment (not query params)
    from urllib.parse import urlencode
    params = urlencode({
        "access_token": access_token,
        "user_id": user["id"],
        "username": user["github_username"],
    })
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback#{params}"
    return RedirectResponse(url=frontend_url)


@router.post("/logout")
async def logout(request: Request):
    """
    Logout user (invalidate token)
    
    In a stateless JWT system, this is handled client-side by deleting the token.
    For server-side invalidation, you'd add the token to a blacklist.
    """
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user info
    """
    return current_user

"""
GitHub OAuth Configuration and Settings
"""

from app.core.config import settings

# GitHub OAuth endpoints
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"
GITHUB_REPOS_API_URL = "https://api.github.com/user/repos"

# OAuth scopes needed for repository access
GITHUB_SCOPES = [
    "read:user",      # Read user profile
    "user:email",     # Access user email
    "repo",           # Full control of repositories (needed for commits/PRs)
]

def get_github_oauth_url(state: str) -> str:
    """Generate GitHub OAuth authorization URL"""
    scope_string = " ".join(GITHUB_SCOPES)
    return (
        f"{GITHUB_AUTHORIZE_URL}"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope={scope_string}"
        f"&state={state}"
    )

# Testing the UI

## Quick Start

### 1. Start the Backend (if not already running)
```powershell
cd backend
.venv\Scripts\activate
uvicorn main:app --reload
```
Backend will run on: http://localhost:8000

### 2. Start the Frontend
Open a new terminal:
```powershell
cd backend
python serve_frontend.py
```
Frontend will run on: http://localhost:3000

### 3. Update GitHub OAuth Settings
Go to your GitHub OAuth App settings:
https://github.com/settings/developers

Update the callback URL to:
```
http://localhost:3000
```

### 4. Open the UI
Navigate to: http://localhost:3000

## Testing Flow

1. **Click "Login with GitHub"**
   - Redirects to GitHub
   - Approve access
   - Returns with JWT token

2. **View Your Repositories**
   - Lists all your GitHub repos
   - Click on a repo to select it

3. **Analyze Repository**
   - Click "Start Analysis"
   - Creates repository record in DB

4. **Fetch Commits**
   - Click "Fetch Commits (Page 1)"
   - Fetches 100 commits from GitHub
   - Stores them in database
   - Can continue fetching more pages

5. **View Stored Commits**
   - Click "View Stored Commits"
   - Shows all commits we've fetched
   - Displays metadata and stats

## API Endpoints Being Tested

- ✅ `GET /auth/github` - Initiate OAuth
- ✅ `GET /auth/github/callback` - Complete OAuth
- ✅ `GET /auth/me` - Get current user
- ✅ `GET /api/repositories` - List GitHub repos
- ✅ `POST /api/repositories/analyze` - Start repo analysis
- ✅ `GET /api/repositories/{id}/status` - Check progress
- ✅ `POST /api/repositories/{id}/fetch-commits` - Fetch commits
- ✅ `GET /api/repositories/{id}/commits` - View stored commits

## Troubleshooting

**"Failed to initiate login"**
- Make sure backend is running on port 8000

**"Authentication failed"**
- Check GitHub OAuth callback URL is set to `http://localhost:3000`
- Verify GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in backend/.env

**CORS errors**
- The frontend server handles CORS
- Make sure both servers are running

**"Please analyze the repository first"**
- Click "Start Analysis" before fetching commits

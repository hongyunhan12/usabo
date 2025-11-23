# GitHub Repository Deployment Instructions

## Quick Start - Using GitHub API

### Step 1: Create a GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name (e.g., `usabo-repo-creator`)
4. Select scope: **`repo`** (full control of private repositories)
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't see it again!)

### Step 2: Run the Deployment Script

**Option A: Provide token via command line**
```bash
py create_github_repo.py --token YOUR_GITHUB_TOKEN
```

**Option B: Set environment variable (Windows PowerShell)**
```powershell
$env:GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
py create_github_repo.py
```

**Option C: Set environment variable (Windows CMD)**
```cmd
set GITHUB_TOKEN=YOUR_GITHUB_TOKEN
py create_github_repo.py
```

**Option D: Interactive mode**
```bash
py create_github_repo.py
```
Then enter your token when prompted.

### Step 3: Choose Repository Visibility

- The script will ask if you want a private repository
- Or use `--private` flag: `py create_github_repo.py --token YOUR_TOKEN --private`

### Step 4: Done!

The script will:
1. ✅ Create the repository on GitHub
2. ✅ Add the remote to your local git
3. ✅ Push all your code to GitHub

## Additional Options

### Create repository without pushing code
```bash
py create_github_repo.py --token YOUR_TOKEN --no-push
```

### Use a different repository name
```bash
py create_github_repo.py --token YOUR_TOKEN --repo-name my-usabo-app
```

## Troubleshooting

### "Token is required" error
- Make sure you've provided the token via `--token`, `GITHUB_TOKEN` environment variable, or interactively

### "Failed to authenticate" error
- Verify your token is correct
- Make sure the token has `repo` scope
- Check if the token has expired

### "Repository already exists" error
- The repository name `usabo` might already exist
- Use `--repo-name` to specify a different name
- Or delete the existing repository on GitHub first

### "Failed to push code" error
- The repository was created successfully
- You can push manually:
  ```bash
  git remote add origin https://github.com/YOUR_USERNAME/usabo.git
  git branch -M main
  git push -u origin main
  ```
- When prompted for password, use your Personal Access Token (not your GitHub password)

## Security Note

⚠️ **Never commit your GitHub token to git!**

The token is sensitive information. Always:
- Use environment variables or command-line arguments
- Never include it in scripts that get committed
- Revoke and regenerate tokens if accidentally exposed


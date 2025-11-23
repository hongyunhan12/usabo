# Deploying to GitHub

## Quick Start

### Option 1: Using the Deployment Script (Windows)

1. Run the deployment script:
   ```bash
   deploy_to_github.bat
   ```

2. Follow the prompts:
   - Create the repository on GitHub first (https://github.com/new)
   - Repository name: `usabo`
   - Choose Public or Private
   - **DO NOT** initialize with README (we already have one)
   - Copy the repository URL
   - Paste it when prompted

### Option 2: Manual Deployment

1. **Create the repository on GitHub:**
   - Go to https://github.com/new
   - Repository name: `usabo`
   - Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license
   - Click "Create repository"

2. **Add remote and push:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/usabo.git
   git branch -M main
   git push -u origin main
   ```

### Option 3: Using GitHub CLI (if installed)

```bash
gh repo create usabo --public --source=. --remote=origin --push
```

## Authentication

If you encounter authentication issues:

1. **Use a Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate a new token with `repo` scope
   - Use the token as your password when pushing

2. **Or use SSH:**
   ```bash
   git remote set-url origin git@github.com:YOUR_USERNAME/usabo.git
   git push -u origin main
   ```

## Verify Deployment

After pushing, visit:
```
https://github.com/YOUR_USERNAME/usabo
```

You should see all your files including:
- `test_ui_app.py`
- `templates/` folder
- `README.md`
- `requirements.txt`
- `.gitignore`


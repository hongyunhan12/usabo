#!/usr/bin/env python3
"""
Script to create a GitHub repository using the GitHub API
"""
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found.")
    print("Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests


def get_github_token(token_arg=None):
    """Get GitHub token from argument, environment, or prompt user"""
    token = token_arg or os.environ.get("GITHUB_TOKEN")
    
    if not token:
        print("\n" + "="*60)
        print("GitHub Personal Access Token Required")
        print("="*60)
        print("\nTo create a token:")
        print("1. Go to: https://github.com/settings/tokens")
        print("2. Click 'Generate new token' -> 'Generate new token (classic)'")
        print("3. Give it a name (e.g., 'usabo-repo-creator')")
        print("4. Select scope: 'repo' (full control of private repositories)")
        print("5. Click 'Generate token'")
        print("6. Copy the token (you won't see it again!)")
        print("\n" + "-"*60)
        print("\nYou can provide the token in three ways:")
        print("  1. Command line: py create_github_repo.py --token YOUR_TOKEN")
        print("  2. Environment: set GITHUB_TOKEN=YOUR_TOKEN")
        print("  3. Interactive: Run the script and enter when prompted")
        print("\n" + "-"*60)
        
        # Only prompt if stdin is a TTY (interactive terminal)
        if sys.stdin.isatty():
            token = input("\nEnter your GitHub Personal Access Token: ").strip()
        else:
            print("\nError: Token is required. Please provide it via --token or GITHUB_TOKEN environment variable.")
            sys.exit(1)
        
        if not token:
            print("Error: Token is required.")
            sys.exit(1)
    
    return token


def get_github_username(token):
    """Get GitHub username from API"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        response.raise_for_status()
        return response.json()["login"]
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to authenticate with GitHub API: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)


def create_repo(token, repo_name, is_private=False):
    """Create a GitHub repository using the API"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "description": "USABO Test UI - Interactive web-based test application for USABO exams",
        "private": is_private,
        "auto_init": False  # Don't initialize with README (we have one)
    }
    
    print(f"\nCreating repository '{repo_name}' on GitHub...")
    
    try:
        response = requests.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        repo_data = response.json()
        repo_url = repo_data["clone_url"]
        repo_html_url = repo_data["html_url"]
        
        print(f"✓ Repository created successfully!")
        print(f"  URL: {repo_html_url}")
        print(f"  Clone URL: {repo_url}")
        
        return repo_url, repo_html_url
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to create repository: {e}")
        if hasattr(e, 'response') and e.response is not None:
            error_data = e.response.json() if e.response.text else {}
            if "message" in error_data:
                print(f"  Message: {error_data['message']}")
            if "errors" in error_data:
                print(f"  Errors: {error_data['errors']}")
            print(f"  Response: {e.response.text}")
        sys.exit(1)


def setup_git_remote(repo_url):
    """Set up git remote and push code"""
    print("\n" + "="*60)
    print("Setting up Git remote and pushing code...")
    print("="*60)
    
    # Check if remote already exists
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"\nRemote 'origin' already exists: {result.stdout.strip()}")
            response = input("Do you want to update it? (y/n): ").strip().lower()
            if response == 'y':
                subprocess.run(["git", "remote", "remove", "origin"], check=True)
                print("Removed existing remote.")
            else:
                print("Keeping existing remote.")
                return False
    except subprocess.CalledProcessError:
        pass
    
    # Add remote
    print(f"\nAdding remote 'origin'...")
    try:
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        print("✓ Remote added successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to add remote: {e}")
        return False
    
    # Rename branch to main if needed
    print("\nChecking branch name...")
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = result.stdout.strip()
        
        if current_branch != "main":
            print(f"Renaming branch from '{current_branch}' to 'main'...")
            subprocess.run(["git", "branch", "-M", "main"], check=True)
            print("✓ Branch renamed to 'main'")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not check/rename branch: {e}")
    
    # Push code
    print("\nPushing code to GitHub...")
    try:
        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
        print("✓ Code pushed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError: Failed to push code: {e}")
        print("\nPossible issues:")
        print("- Authentication required (use Personal Access Token as password)")
        print("- Network connectivity issues")
        print("\nYou can push manually with:")
        print(f"  git push -u origin main")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Create GitHub repository using API")
    parser.add_argument("--token", help="GitHub Personal Access Token")
    parser.add_argument("--repo-name", default="usabo", help="Repository name (default: usabo)")
    parser.add_argument("--private", action="store_true", help="Create private repository")
    parser.add_argument("--no-push", action="store_true", help="Don't push code after creating repo")
    
    args = parser.parse_args()
    repo_name = args.repo_name
    
    print("="*60)
    print("USABO Test UI - GitHub Repository Creator")
    print("="*60)
    
    # Check if we're in a git repository
    if not Path(".git").exists():
        print("\nError: Not a git repository. Run 'git init' first.")
        sys.exit(1)
    
    # Get GitHub token
    token = get_github_token(args.token)
    
    # Get username
    print("\nAuthenticating with GitHub...")
    username = get_github_username(token)
    print(f"✓ Authenticated as: {username}")
    
    # Ask if private or public (if not specified via command line)
    is_private = args.private
    if not args.private and sys.stdin.isatty():
        print("\n" + "-"*60)
        response = input("Create private repository? (y/n, default: n): ").strip().lower()
        is_private = response == 'y'
    
    # Create repository
    repo_url, repo_html_url = create_repo(token, repo_name, is_private)
    
    # Set up git remote and push (unless --no-push is specified)
    success = False
    if not args.no_push:
        success = setup_git_remote(repo_url)
    else:
        print("\nSkipping push (--no-push specified)")
        print(f"\nTo push manually, run:")
        print(f"  git remote add origin {repo_url}")
        print(f"  git branch -M main")
        print(f"  git push -u origin main")
    
    if success:
        print("\n" + "="*60)
        print("SUCCESS! Repository deployed to GitHub")
        print("="*60)
        print(f"\nYour repository is available at:")
        print(f"  {repo_html_url}")
        print("\nYou can view it in your browser now!")
    else:
        print("\n" + "="*60)
        print("Repository created, but push failed")
        print("="*60)
        print(f"\nRepository URL: {repo_html_url}")
        print(f"Clone URL: {repo_url}")
        print("\nTo push manually, run:")
        print(f"  git remote add origin {repo_url}")
        print(f"  git branch -M main")
        print(f"  git push -u origin main")


if __name__ == "__main__":
    main()

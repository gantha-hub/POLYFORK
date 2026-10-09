#!/usr/bin/env python3
"""
VrikshaVision GitHub Push Script (Xcode-free / Pure Python)
Pushes the committed digital twin codebase and GitHub Pages assets to https://github.com/gantha-hub/POLYFORK.
"""

import sys
import os
import getpass

# Configure SSL certificates via certifi
try:
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
except ImportError:
    pass

import dulwich.porcelain as porcelain
from dulwich.repo import Repo

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_REPO = "gantha-hub/POLYFORK"

def main():
    print("=" * 65)
    print("🌲 VRIKSHAVISION: PUSH TO GITHUB (gantha-hub/POLYFORK)")
    print("=" * 65)

    # 1. Obtain GitHub Token
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if len(sys.argv) > 1 and sys.argv[1].strip():
        token = sys.argv[1].strip()

    if not token:
        print("\nGitHub requires authentication to push to your repository.")
        print("To create a token in 30 seconds:")
        print("  1. Visit: https://github.com/settings/tokens/new")
        print("  2. Check the 'repo' scope checkbox")
        print("  3. Click 'Generate token' and copy it")
        print("-" * 65)
        try:
            token = getpass.getpass("Enter your GitHub Personal Access Token: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nPush cancelled.")
            return

    if not token:
        print("Error: Token cannot be empty.")
        sys.exit(1)

    authenticated_url = f"https://oauth2:{token}@github.com/{GITHUB_REPO}.git"
    clean_url = f"https://github.com/{GITHUB_REPO}.git"

    repo = Repo(REPO_DIR)

    print(f"\n[1/3] Staging all files and creating commit...")
    try:
        porcelain.add(REPO_DIR, ".")
    except Exception as e:
        print(f"      Add warning: {e}")

    try:
        commit_sha = porcelain.commit(
            REPO_DIR,
            message="Upgrade VrikshaVision to professional, map-first, touch-friendly UI (Desktop/Tablet/Mobile)",
            committer=b"Gantha Hub <developer@gantha-hub.org>",
            author=b"Gantha Hub <developer@gantha-hub.org>"
        )
        print(f"      Created new commit: {commit_sha.decode()[:8]}")
    except Exception as e:
        head_commit = repo.head().decode()
        print(f"      Using existing HEAD commit: {head_commit[:8]} ({e})")

    print(f"[2/3] Connecting to https://github.com/{GITHUB_REPO}...")

    # Temporarily set authenticated remote URL
    config = repo.get_config()
    config.set((b"remote", b"origin"), b"url", authenticated_url.encode())
    config.write_to_path()

    try:
        print(f"[3/3] Pushing 'main' branch to GitHub...")
        porcelain.push(repo, "origin", ["refs/heads/main:refs/heads/main"], force=True)
        print("\n" + "=" * 65)
        print("🎉 SUCCESS! Pushed all files, workflows, and index.html to:")
        print(f"   👉 https://github.com/{GITHUB_REPO}")
        print(f"   👉 Live Site: https://gantha-hub.github.io/POLYFORK/")
        print("=" * 65)
    except Exception as err:
        print(f"\n❌ Push failed: {err}")
        print("\nPlease verify:")
        print("1. Your token has the 'repo' permission enabled.")
        print(f"2. You have write/admin access to https://github.com/{GITHUB_REPO}.")
        sys.exit(1)
    finally:
        # Sanitize token from git config so secrets are never left in plaintext on disk
        config.set((b"remote", b"origin"), b"url", clean_url.encode())
        config.write_to_path()

if __name__ == "__main__":
    main()

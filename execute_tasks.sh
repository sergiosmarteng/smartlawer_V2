#!/usr/bin/env bash
set -euo pipefail

# Simple execution of core steps (no winget, no gh)
# Configure git author
git config user.email "195499178+schinasergio@users.noreply.github.com"
git config user.name "schinasergio"

# Commit any pending changes
echo "Committing any changes..."
git add .
git commit -m "Ready for GitHub tasks setup" || echo "No changes to commit"

# Push to GitHub (this will work if remote is already set)
echo "Pushing to GitHub..."
git push --force-with-lease origin HEAD

echo "Core setup complete. Now run the full setup script with proper permissions."
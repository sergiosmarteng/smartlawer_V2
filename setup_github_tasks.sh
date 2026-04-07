#!/usr/bin/env bash
set -euo pipefail

# Configuration
REPO="schinasergio/smartlawer_V2"
PROJECT_NAME="SmartLawer-Squad-Board"
# Try capturing token gracefully
if [ -f "smartlawer_V2/.env" ]; then
    GITHUB_TOKEN=$(grep -oP '^GITHUB_TOKEN=\K.*' smartlawer_V2/.env || echo "")
else
    echo ".env not found!"
    exit 1
fi

export GITHUB_TOKEN

echo "Ensuring gh cli..."
if ! command -v gh &> /dev/null; then
    echo "Please install gh cli manually in your windows environment or via winget: winget install --id GitHub.cli"
    exit 1
fi

echo "Authenticating with GitHub..."
gh auth login --with-token <<< "$GITHUB_TOKEN"
gh auth status

# Set git user info
echo "Configuring Git Global Info..."
git config user.email "195499178+schinasergio@users.noreply.github.com"
git config user.name "schinasergio"

# Add and Commit All Current Code
echo "Committing recent progress (Phase 1 and Squad Config)..."
# Going into submodule or project dir if needed
# We are currently in root folder (where this script is)
git pull origin main || echo "No remote or up to date"

git add .
git commit -m "feat(Phase 1 & Squad): docker setup, DB schemas, backend skeleton and Microharness multi-agent config" || echo "No changes to commit"
echo "Pushing code to $REPO"
git branch -M main
git push origin main || git push origin main --force || echo "Push failed or already pushed"

# Project Generation
echo "Retrieving Project Board: $PROJECT_NAME"
PROJECT_ID=$(gh project list --owner schinasergio --format json | jq -r ".[] | select(.title == \"$PROJECT_NAME\") | .id" || true)
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gh project create "$PROJECT_NAME" --owner schinasergio --template basic --visibility public --format json | jq -r .id)
    echo "Created project board ID: $PROJECT_ID"
else
    echo "Board already exists ID: $PROJECT_ID"
fi

# Ensure columns
declare -A COLUMN_MAP=(
    ["Backlog"]="backlog"
    ["In Progress"]="inprogress"
    ["Review"]="review"
    ["Done"]="done"
)

for col_name in "${!COLUMN_MAP[@]}"; do
    COLUMN_ID=$(gh project column-list "$PROJECT_ID" --format json | jq -r ".[] | select(.name == \"$col_name\") | .id" || true)
    if [ -z "$COLUMN_ID" ]; then
        COLUMN_ID=$(gh project column-create "$PROJECT_ID" --name "$col_name" --format json | jq -r .id)
    fi
done

# We will put the specific column IDs we need
BACKLOG_COLUMN_ID=$(gh project column-list "$PROJECT_ID" --format json | jq -r '.[] | select(.name == "Backlog") | .id')
DONE_COLUMN_ID=$(gh project column-list "$PROJECT_ID" --format json | jq -r '.[] | select(.name == "Done") | .id')

declare -A TASKS=(
    [1]="Phase 1: Setup Docker Environment|Create docker-compose.yml for FastAPI, PostgreSQL, and Redis.|infrastructure|Done"
    [2]="Phase 1: Configure Database Schema|Set up SQLAlchemy models for User, Document, Analysis, Template.|database|Done"
    [3]="Phase 1: Python Project Init|Initialize backend python pip project and folder structure.|backend|Done"
    [4]="Phase 12: Multi-Agent Squad|Configure Agents structure for Microharness (Leader, Architect, SEs, DB, Designer, Reviewer).|architecture|Done"
    [5]="Phase 2: Implement User Model|Create SQLAlchemy User model with password hashing (bcrypt).|database|Backlog"
    [6]="Phase 2: Auth Flow|Implement OAuth2 flow with Password Bearer for login endpoints.|backend|Backlog"
    [7]="Phase 3: File Upload Endpoint|Create POST /api/documents/upload to save PDFs.|backend|Backlog"
    [8]="Phase 3: Text Extraction Service|Implement PyMuPDF and Tesseract inside python.|backend|Backlog"
    [9]="Phase 3: Async Task Queue|Setup Celery and Redis to handle OCR/Analysis processing.|backend|Backlog"
    [10]="Phase 4: OpenAI Integration|Configure OpenAI Client for Legal Analysis (Summary, Requests, Laws).|ai|Backlog"
    [11]="Phase 5: Docx Template Parser|Logic to read .docx files and identify placeholders using python-docx.|docgen|Backlog"
    [12]="Phase 5: Defense Gen Logic|Map Analysis data + user input to generate actual final .docx.|docgen|Backlog"
    [13]="Phase 6: Frontend API Client|Set up Axios and configure React to consume Auth and Document APIs.|frontend|Backlog"
)

for task_id in "${!TASKS[@]}"; do
    IFS='|' read -r title description label state <<< "${TASKS[$task_id]}"
    
    EXISTING_ISSUE=$(gh issue list --repo "$REPO" --state all --search "title:\"$title\"" --json number -q '.[0].number' || true)
    if [ -n "$EXISTING_ISSUE" ] && [ "$EXISTING_ISSUE" != "null" ]; then
        echo "Task already exists as issue #$EXISTING_ISSUE, skipping."
        ISSUE_NUMBER=$EXISTING_ISSUE
    else
        echo "Creating issue: $title"
        ISSUE_OUTPUT=$(gh issue create --repo "$REPO" --title "$title" --body "$description" --label "$label" --json number)
        ISSUE_NUMBER=$(echo "$ISSUE_OUTPUT" | jq -r .number)
    fi
    
    # Assign to column
    if [ "$state" == "Done" ]; then
        gh issue close "$ISSUE_NUMBER" --repo "$REPO" || true
        gh project item-add "$PROJECT_ID" --id "$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json id -q .id)" --column-id "$DONE_COLUMN_ID" || true
    else
        gh project item-add "$PROJECT_ID" --id "$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json id -q .id)" --column-id "$BACKLOG_COLUMN_ID" || true
    fi
done

echo "Tracking sync finished!"
import os
import requests
import re

# Extract token
token = ""
with open("smartlawer_V2/.env", "r") as f:
    for line in f:
        if line.startswith("GITHUB_TOKEN="):
            token = line.strip().split("=")[1]

if not token:
    print("Token not found!")
    exit(1)

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

repo = "schinasergio/smartlawer_V2"
url = f"https://api.github.com/repos/{repo}/issues"

tasks = [
    {"title": "Phase 2: Implement User Model & Auth Flow", "body": "Create SQLAlchemy User model with password hashing and JWT flow.", "labels": ["backend"]},
    {"title": "Phase 3: File Upload & Text Extraction Service", "body": "POST /api/documents/upload, PyMuPDF, Tesseract, Celery Tasks.", "labels": ["backend"]},
    {"title": "Phase 4: OpenAI Integration", "body": "Configure OpenAI Client for Analysis Pipeline.", "labels": ["ai"]},
    {"title": "Phase 5: Docx Template Parser & Generation", "body": "python-docx logic to generate final .docx from Analysis data.", "labels": ["docgen"]},
    {"title": "Phase 6: Frontend Integration", "body": "Set up Axios and UI to consume Auth and Document APIs.", "labels": ["frontend"]}
]

for task in tasks:
    print(f"Creating issue: {task['title']}")
    resp = requests.post(url, json=task, headers=headers)
    if resp.status_code == 201:
        print(f"Created: {resp.json().get('html_url')}")
    else:
        print(f"Failed: {resp.status_code} {resp.text}")

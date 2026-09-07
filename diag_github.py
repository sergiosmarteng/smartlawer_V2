import os
import requests
import json

# Configuration
env_path = ".env"
token = ""
owner = ""
repo_name = ""

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.strip().startswith("GITHUB_TOKEN="):
                token = line.strip().split("=")[1]
            if line.strip().startswith("GITHUB_OWNER="):
                owner = line.strip().split("=")[1]
            if line.strip().startswith("GITHUB_REPO="):
                repo_name = line.strip().split("=")[1]

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

graphql_url = "https://api.github.com/graphql"

def run_query(query, variables=None):
    request = requests.post(graphql_url, json={'query': query, 'variables': variables}, headers=headers)
    return request.json()

# Check projects
query_project = """
query($owner: String!) {
  user(login: $owner) {
    projectsV2(first: 20) {
      nodes {
        id
        title
      }
    }
  }
  organization(login: $owner) {
    projectsV2(first: 20) {
      nodes {
        id
        title
      }
    }
  }
}
"""
res = run_query(query_project, {"owner": owner})
print(json.dumps(res, indent=2))

# Check issues
query_repo = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issues(first: 10, states: [OPEN, CLOSED]) {
      nodes {
        title
        state
      }
    }
  }
}
"""
res_repo = run_query(query_repo, {"owner": owner, "name": repo_name})
print(json.dumps(res_repo, indent=2))

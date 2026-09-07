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
            if line.startswith("GITHUB_TOKEN="):
                token = line.strip().split("=")[1]
            if line.startswith("GITHUB_OWNER="):
                owner = line.strip().split("=")[1]
            if line.startswith("GITHUB_REPO="):
                repo_name = line.strip().split("=")[1]

if not token or not owner or not repo_name:
    print(f"Missing config: token={bool(token)}, owner={owner}, repo={repo_name}")
    exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

graphql_url = "https://api.github.com/graphql"

def run_query(query, variables=None):
    request = requests.post(graphql_url, json={'query': query, 'variables': variables}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(f"Query failed: {request.status_code}. {request.text}")

# 1. Ensure Issues exist
phases = [
    {"title": "Phase 1: Setup Environment & DB", "body": "Docker, FastAPI, PostgreSQL, Redis, SQLAlchemy Schemas.", "labels": ["infrastructure", "database"]},
    {"title": "Phase 2: Authentication Flow", "body": "JWT-based auth with Axios interceptors and JWT Provider.", "labels": ["backend", "auth"]},
    {"title": "Phase 3: OCR & Document Processing", "body": "PyMuPDF, Tesseract, Celery Tasks for file extraction.", "labels": ["backend", "ai"]},
    {"title": "Phase 4: AI Analysis Pipeline", "body": "OpenAI/LangChain integration for legal summary and arguments.", "labels": ["ai"]},
    {"title": "Phase 5: Docx Generation", "body": "Python-docx template parsing and document generation.", "labels": ["docgen"]},
    {"title": "Phase 6: Frontend UI/UX (Precision Atelier)", "body": "Next.js dashboard, upload, and analysis pages redesign.", "labels": ["frontend", "design"]},
    {"title": "Phase 7: Backend Stitching & Data Fetching", "body": "Replacing mocks with actual API calls in all frontend routes.", "labels": ["frontend", "backend"]}
]

print("Syncing Issues...")
issue_nodes = {} # {title: id}

# Get existing issues
query_issues = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issues(first: 100) {
      nodes {
        id
        title
        number
        state
      }
    }
  }
}
"""
res = run_query(query_issues, {"owner": owner, "name": repo_name})
if 'data' in res and res['data']['repository']:
    existing_issues = {node['title']: node for node in res['data']['repository']['issues']['nodes']}
else:
    existing_issues = {}

for phase in phases:
    if phase['title'] in existing_issues:
        issue_nodes[phase['title']] = existing_issues[phase['title']]['id']
        # Close if done (Phases 1-7 are done)
        if existing_issues[phase['title']]['state'] == 'OPEN':
            print(f"Closing issue: {phase['title']}")
            close_query = """
            mutation($id: ID!) {
              closeIssue(input: {issueId: $id}) {
                issue {
                  state
                }
              }
            }
            """
            run_query(close_query, {"id": issue_nodes[phase['title']]})
    else:
        print(f"Creating issue: {phase['title']}")
        rest_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
        resp = requests.post(rest_url, json=phase, headers=headers)
        if resp.status_code == 201:
            issue_data = resp.json()
            issue_nodes[phase['title']] = issue_data['node_id']
            # Close it since it's done
            close_query = """
            mutation($id: ID!) {
              closeIssue(input: {issueId: $id}) {
                issue {
                  state
                }
              }
            }
            """
            run_query(close_query, {"id": issue_nodes[phase['title']]})
        else:
            print(f"Failed to create issue: {resp.text}")

print("Syncing Project Board...")
# 2. Sync to Project Board
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
}
"""
res = run_query(query_project, {"owner": owner})
project_id = None
if 'data' in res and 'user' in res['data'] and res['data']['user']:
    for p in res['data']['user']['projectsV2']['nodes']:
        if p and p.get('title') == "SmartLawer-Squad-Board":
            project_id = p['id']
            break

if not project_id:
    # Try Organization if not user
    query_org_project = """
    query($owner: String!) {
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
    res_org = run_query(query_org_project, {"owner": owner})
    if 'data' in res_org and 'organization' in res_org['data'] and res_org['data']['organization']:
        for p in res_org['data']['organization']['projectsV2']['nodes']:
            if p['title'] == "SmartLawer-Squad-Board":
                project_id = p['id']
                break

if not project_id:
    print("Project 'SmartLawer-Squad-Board' not found. Please create it manually if needed.")
else:
    # Get Project Columns (Fields)
    query_fields = """
    query($id: ID!) {
      node(id: $id) {
        ... on ProjectV2 {
          fields(first: 20) {
            nodes {
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    res = run_query(query_fields, {"id": project_id})
    status_field = None
    done_option_id = None
    if 'data' in res and res['data']['node']:
        for field in res['data']['node']['fields']['nodes']:
            if field.get('name') == 'Status':
                status_field = field['id']
                for opt in field['options']:
                    if opt['name'] == 'Done':
                        done_option_id = opt['id']
                        break
                break
    
    for title, node_id in issue_nodes.items():
        # Add to project
        print(f"Adding item to project: {title}")
        add_item_query = """
        mutation($project: ID!, $content: ID!) {
          addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
            item {
              id
            }
          }
        }
        """
        item_res = run_query(add_item_query, {"project": project_id, "content": node_id})
        if 'data' in item_res and item_res['data']['addProjectV2ItemById']:
            item_id = item_res['data']['addProjectV2ItemById']['item']['id']
            
            if status_field and done_option_id:
                # Set Status to Done
                update_item_query = """
                mutation($project: ID!, $item: ID!, $field: ID!, $option: ID!) {
                  updateProjectV2ItemFieldValue(input: {
                    projectId: $project,
                    itemId: $item,
                    fieldId: $field,
                    value: { singleSelectOptionId: $option }
                  }) {
                    projectV2Item {
                      id
                    }
                  }
                }
                """
                run_query(update_item_query, {
                    "project": project_id,
                    "item": item_id,
                    "field": status_field,
                    "option": done_option_id
                })

print("GitHub Sync Finished!")

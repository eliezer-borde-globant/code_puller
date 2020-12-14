import os

from git import Repo
from github import Github
from datetime import datetime

def init_repo(path, dts):
    repo = Repo(path)
    iso = datetime.now().date().isoformat().replace("-", "_")
    secrets = {file_path: [{
                    "file": file_path,
                    "line": secret_found.lineno,
                    "value": secret_found.secret_value
                } for secret_type, secret_found in secrets_detects.items()
        ] for file_path, secrets_detects in dts.data.items()}
    for file_path, _ in secrets.items():
        branch_name = f"Secret_Found_{file_path}_{iso}"
        git = repo.git
        git.checkout('master')  # create a new branch
        git.branch('-d', f'{branch_name}')  # create a new branch
        git.checkout('master', b=branch_name)  # create a new branch
        git.push("--set-upstream", "origin", f"{branch_name}")

def create_repo(repo):
    token = os.environ.get("GITHUB_TOKEN")
    g = Github(token)
    repo = g.get_repo(repo)
    body = "Test"
    pr = repo.create_pull(
        title="test",
        body=body,
        head="master",
        base="master"
    )
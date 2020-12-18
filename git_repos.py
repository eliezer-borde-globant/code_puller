import requests
import os
import json
import shutil
import logging

from git import Repo
from github import Github

from detects import start_scan

import uuid

logger = logging.getLogger(__file__)

# create console handler and set level to debug
ch = logging.StreamHandler()
logger.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

def get_org_repo(org_name, auth_token):
    page_number = 1
    repos = []

    logger.info(f"Scanning repos for organization {org_name}")
    while True:
        logger.info(f"URL: https://api.github.com/orgs/{org_name}/repos?page={page_number}&per_page=100")
        response = requests.get(f"https://api.github.com/orgs/{org_name}/repos?page={page_number}&per_page=100",
                                headers={
                                    'Authorization': f'token {auth_token}'
                                })
        logger.info(f"Response from URL - {response.status_code}")
        repos += response.json()
        page_number += 1
        if len(response.json()) == 0:
            break
    return {repo['name']: repo['clone_url'] for repo in repos if secret_file_exists(org_name, repo['name'], auth_token) == 404}


def secret_file_exists(org_name, repo_name, auth_token):
    logger.info(f"Checking .secrets.baseline file in the repo with URL - https://api.github.com/repos/{org_name}/{repo_name}/contents/.secrets.baseline")
    response = requests.get(f"https://api.github.com/repos/{org_name}/{repo_name}/contents/.secrets.baseline",
                            headers={
                                'Authorization': f'token {auth_token}'
                            }
                            )
    if response.status_code == 200:
        logger.info(f".secrets.baseline file exists for repo - {org_name}/{repo_name}")
    elif response.status_code == 404:
        logger.info(f".secrets.baseline file doesn't exists for repo - {org_name}/{repo_name}")
    else:
        logger.error(f"Error Occured: Response status - {response.status_code} for {org_name}/{repo_name}")

    return response.status_code


def download_repo(repo_name, repo_url, token):
    logger.info(f"Trying to download repo - {repo_name} from {repo_url}")
    repo = repo_url.replace("github.com", f"{token}@github.com")
    repo_dir = Repo.clone_from(repo, f'repos/{repo_name}')
    logger.info(f"Starting to scan {repo_name}")
    secrets_text = start_scan(repo_dir.working_dir)
    with open(f'{repo_dir.working_dir}/.secrets.baseline', 'w') as secrets_file:
        logger.info(f"Creating .secrets.baseline file for {repo_name}")
        secrets_file.write(secrets_text)

    git_operations(repo_name, repo_dir, repo_url, token)


def git_operations(repo_name, repo_dir, repo_url, token):

    owner_and_repo = repo_url.split('.com/')[1].replace(".git", '')
    branch_name = f"{repo_name}_secrets_branch_{uuid.uuid1()}"
    git = repo_dir.git
    base_branch = repo_dir.active_branch.name
    git.checkout(base_branch, b=branch_name)
    git.add(".secrets.baseline")
    logger.info(f"Creating commit to branch name {branch_name} in {repo_name}")
    git.commit("-m", "feat: secrets file added")
    logger.info(f"Pushing commit to branch name {branch_name} in {repo_name}")
    git.push("--set-upstream", "origin", branch_name)
    g = Github(token)
    repo = g.get_repo(owner_and_repo)
    body = f"Found secrets for {repo_name} and added to .secrets.baseline"
    logger.info(f"Making PR for {branch_name} in {repo_name}")
    repo.create_pull(
        title=f"{repo_name}-.secrets.baseline Added",
        body=body,
        head=branch_name,
        base=base_branch
    )
    logger.info(f"PR has been created in {repo_name}")
    logger.info(f"Removing folder {repo_name}")
    dirpath = os.path.join('repos', f'{repo_name}')
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)

org_name = "felipe-hernandez-globant"
auth_token = ""

# pprint.pprint(get_org_repo(org_name, auth_token))
download_repo('lemanga', 'https://github.com/felipe-hernandez-globant/lemanga.git', auth_token)
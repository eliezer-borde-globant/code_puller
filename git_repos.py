import requests
import os
import json
import shutil
import logging

from git import Repo
from github import Github

from detects import start_scan

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

    logger.info(f"scanning for organization {org_name}")
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
    repo = repo_url.replace("github.com", f"{token}@github.com")
    # deleting if folder exists
    dirpath = os.path.join('repos', f'{repo_name}')
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)
    repo_dir = Repo.clone_from(repo, f'repos/{repo_name}')
    secrets_text = start_scan(repo_dir.working_dir)
    with open(f'{repo_dir.working_dir}/.secrets.baseline', 'w') as secrets_file:
        secrets_file.write(secrets_text)

    git_operations(repo_name, repo_dir, repo_url, token)


def git_operations(repo_name, repo_dir, repo_url, token):
    branch_name = f"{repo_name}_secrets_branch_11"
    git = repo_dir.git
    git.checkout(repo_dir.active_branch.name, b=branch_name)
    git.add(".secrets.baseline")
    git.commit("-m", "feat: secrets file added")
    git.push("--set-upstream", "origin", branch_name)
    #
    # g = Github(token)
    # repo = g.get_repo('leonardo-orozco-globant/lemanga')
    # body = "Test"

    create_pull_request(
        "leonardo-orozco-globant",  # project_name
        "lemanga",  # repo_name
        "Test",  # title
        "My pull request description",  # description
        branch_name,  # head_branch
        repo_dir.active_branch.name,  # base_branch
        token,  # git_token
    )
    # repo.create_pull(
    #     title="test",
    #     body=body,
    #     head=branch_name,
    #     base=repo_dir.active_branch.name
    # )

def create_pull_request(project_name, repo_name, title, description, head_branch, base_branch, git_token):
    """Creates the pull request for the head_branch against the base_branch"""
    git_pulls_api = "https://github.com/api/v3/repos/{0}/{1}/pulls".format(
        project_name,
        repo_name)
    headers = {
        "Authorization": "token {0}".format(git_token),
        "Content-Type": "application/json"}

    payload = {
        "title": title,
        "body": description,
        "head": head_branch,
        "base": base_branch,
    }

    s = requests.Session()
    res = s.get(git_pulls_api)
    cookies = dict(res.cookies)

    r = s.post(
        git_pulls_api,
        headers=headers,
        data=json.dumps(payload), cookies=cookies)

    if not r.ok:
        print("Request Failed: {0}".format(r.text))




# pprint.pprint(get_org_repo(org_name, auth_token))
download_repo('lemanga', 'https://github.com/eliezer-borde-globant/lemanga.git', auth_token)
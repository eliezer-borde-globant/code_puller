import requests
import os
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


def get_org_repo(organization, token):
    page_number = 1
    repos = []

    logger.info(f"scanning for organization {organization}")
    while True:
        logger.info(f"URL: https://api.github.com/orgs/{organization}/repos?page={page_number}&per_page=100")
        response = requests.get(f"https://api.github.com/orgs/{organization}/repos?page={page_number}&per_page=100",
                                headers={
                                    'Authorization': f'token {token}'
                                })
        logger.info(f"Response from URL - {response.status_code}")
        repos += response.json()
        page_number += 1
        if len(response.json()) == 0:
            break
    return {repo['name']: repo['clone_url'] for repo in repos if
            secret_file_exists(organization, repo['name'], token) == 404}


def secret_file_exists(organization, repo, token):
    logger.info(f"Checking [.secrets.baseline] file in the repo with URL - "
                f"https://api.github.com/repos/{organization}/{repo}/contents/.secrets.baseline")
    response = requests.get(f"https://api.github.com/repos/{organization}/{repo}/contents/.secrets.baseline",
                            headers={
                                'Authorization': f'token {token}'
                            }
                            )
    if response.status_code == 200:
        logger.info(f".secrets.baseline file exists for repo - {organization}/{repo}")
    elif response.status_code == 404:
        logger.info(f"[.secrets.baseline] file does not exists for repo - {organization}/{repo}")
    else:
        logger.error(f"Error Occurred: [Response status - {response.status_code} for {organization}/{repo}]")

    return response.status_code


def download_repo(repo_name, repo_url, token):
    repo = repo_url.replace("github.com", f"{token}@github.com")
    # deleting if folder exists
    directory = os.path.join('repos', f'{repo_name}')
    if os.path.exists(directory) and os.path.isdir(directory):
        shutil.rmtree(directory)
    repo_dir = Repo.clone_from(repo, f'repos/{repo_name}')
    secrets_text = start_scan(repo_dir.working_dir)
    with open(f'{repo_dir.working_dir}/.secrets.baseline', 'w') as secrets_file:
        secrets_file.write(secrets_text)

    git_operations(repo_name, repo_dir, repo_url, token)


def git_operations(repo_name, repo_dir, repo_url, token):
    owner_and_repo = repo_url.split('.com/')[1].replace(".git", '')
    branch_name = f"{repo_name}_secrets_branch_23"
    git = repo_dir.git
    base_branch = repo_dir.active_branch.name
    git.checkout(base_branch, b=branch_name)
    git.add(".secrets.baseline")
    git.commit("-m", "feat: secrets file added")
    git.push("--set-upstream", "origin", branch_name)
    # preparing for pull request
    g = Github(token)
    repo = g.get_repo(owner_and_repo)
    body = "Test"

    repo.create_pull(
        title="test",
        body=body,
        head=branch_name,
        base=base_branch
    )


org_name = 'CamelotVG'
auth_token = 'a8b3736c2d09e26bc830a49c634ab358722daac7'

# pprint.pprint(get_org_repo(org_name, auth_token))
download_repo('lemanga', 'https://github.com/eliezer-borde-globant/lemanga.git', auth_token)

import requests
import os
import shutil
import logging

from git import Repo
from github import Github

from detects import start_scan

import uuid

import click

from datetime import datetime

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


def get_org_repo(organization, token, repos_to_download='all'):
    page_number = 1
    repos = []
    logger.info(f"Scanning Repos in organization {organization}")
    while True:
        logger.info(f"Getting Repos from page {page_number} in {organization}")
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
            secret_file_exists(organization, repo['name'], token, repos_to_download) == 404}


def secret_file_exists(organization, repo, token, repos_to_download):
    if repos_to_download and (repo in repos_to_download or repos_to_download=='all'):
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


def download_repo_and_create_secret_file(repo_name, repo_url, token):
    logger.info(f"Trying to download repo - {repo_name} from {repo_url}")
    repo = repo_url.replace("github.com", f"{token}@github.com")
    directory = os.path.join('repos', f'{repo_name}')

    logger.info(f"Deleting if folder exists in {directory}")
    if os.path.exists(directory) and os.path.isdir(directory):
        shutil.rmtree(directory)

    repo_dir = Repo.clone_from(repo, f'repos/{repo_name}')
    logger.info(f"Starting to scan {repo_name}")
    secrets_text = start_scan(repo_dir.working_dir)
    with open(f'{repo_dir.working_dir}/.secrets.baseline', 'w') as secrets_file:
        logger.info(f"Creating .secrets.baseline file for {repo_name}")
        secrets_file.write(secrets_text)

    git_operations(repo_name, repo_dir, repo_url, token)


def git_operations(repo_name, repo_dir, repo_url, token):
    owner_and_repo = repo_url.split('.com/')[1].replace(".git", '')
    branch_name = f"secret_scanner_bot/{repo_name}/add/_secrets_baseline"
    git = repo_dir.git
    base_branch = repo_dir.active_branch.name
    result = git.ls_remote("--heads", "origin", branch_name)
    if result:
        logger.info(f"This branch: {branch_name} already existis in repo: {repo_name}")
        return
    logger.info(f"Result ls_remote : {result}")
    git.checkout(base_branch, b=branch_name)
    git.add(".secrets.baseline")
    logger.info(f"Creating commit to branch name {branch_name} in {repo_name}")
    git.commit("-m", "chord: Secrets file added")
    logger.info(f"Pushing commit to branch name {branch_name} in {repo_name}")
    git.push("--set-upstream", "origin", branch_name)
    g = Github(token)
    repo = g.get_repo(owner_and_repo)
    body = f"Found secrets for {repo_name} and added to .secrets.baseline"
    logger.info(f"Making PR for {branch_name} in {repo_name}")
    repo.create_pull(
        title=f"[SRE-396] {repo_name}-.secrets.baseline file added",
        body=body,
        head=branch_name,
        base=base_branch
    )
    logger.info(f"PR has been created in {repo_name}")

@click.command()
@click.option('--organization', envvar="ORGANIZATION")
@click.option('--token', envvar="TOKEN")
def main(organization, token):
    repos = get_org_repo(organization, token)

    for key, value in repos.items():
        download_repo_and_create_secret_file(key, value, token)


if __name__ == '__main__':
    main()
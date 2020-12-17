import requests
import pprint

page_number = 1
repos = []
all_repo_urls = []
while True:
    response = requests.get("https://api.github.com/orgs/CamelotVG/repos?page={}&per_page=100".format(page_number),
                            headers={
                                'Authorization': 'token yourtoken'
                            })
    repos.append(response.json())
    page_number += 1
    if len(response.json()) == 0:
        break

print(len(repos))
print(pprint.pprint(repos[0][0], indent=4))
for i in repos:
    for j in i:
        all_repo_urls.append(j['git_url'])

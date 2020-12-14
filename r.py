import requests

requests.post("http://localhost:9000/code", json={
    "name": "lemanga",
    "url": "git@github.com:leonardo-orozco-globant/lemanga.git"
})
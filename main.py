import asyncio

import os

from aiohttp import web

from detects import scan
from git_actions import init_repo


async def pull_code(request):
    data = await request.json()
    directory = f"/tmp/{data['name']}"
    cmd = f"rm -rf {directory}"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()
    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
    print("remove finish")

    url = data["url"]
    cmd = f"git clone {url} {directory}"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()
    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
    print("git finish")
    dts = scan(argv=["scan", directory, "--all-files"])
    init_repo(directory, dts)
    return web.json_response({})


app = web.Application()
app.router.add_post("/code", pull_code)


if __name__ == "__main__":
    
    port = os.environ.get("PORT", 9000)
    if port is not None:
        port = int(port)
    web.run_app(app, port=port)
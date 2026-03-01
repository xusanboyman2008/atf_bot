import asyncio
import json
import random

import aiohttp

URL = "https://atfminers.asloni.online/miner/index.php?action=sync_taps&t=1772333419892"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json"
}

payload = {
    "initData": "query_id=AAHgh7YIAwAAAOCHtggUCi16&user=%7B%22id%22%3A6588631008%2C%22first_name%22%3A%22%28%E2%96%BA__%E2%97%84%29%20T_T%20X_X%20xusanboyman%22%2C%22last_name%22%3A%22%F0%9F%87%BA%F0%9F%87%BF%22%2C%22username%22%3A%22xusanboyman200%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FABKucBBOPE9qSGZbrWEF4xW6wrAlil-YqDxjQfABvEOlAI0lJIBU15Q2npDYdUbN.svg%22%7D&auth_date=1772333403&signature=Az6iIK-AmexRFpYTMAa5z6CmWlPQt0Oi80nzFzCTttzgYxBl6PqEJRqFzkaStpL5o8EzzeAF9KvjzQ6HM0Q4BQ&hash=d0b4d725d7e2b2c0fe70e56b481aa4f4ad53e8c4cb6077f974715a9fb75c8624",
    "tg_id": "6588631008",
    "taps": 20
}
DATA = json.dumps(payload)

# ✅ SAFE VALUES FOR SHARED HOSTING
WORKERS = 500  # do NOT increase much
BASE_DELAY = 0  # request spacing


async def worker(name, session):
    while True:
        try:
            async with session.post(URL, data=DATA) as resp:

                # read response so connection is reused
                await resp.read()
                print(resp.status)
                if resp.status == 429:
                    await asyncio.sleep(3)
        except aiohttp.ClientError as e:
            print(f"[{name}] network error:", e)
            await asyncio.sleep(3)


async def main():
    # ✅ LIMITED connector (critical for Alwaysdata)
    connector = aiohttp.TCPConnector(
        ssl=False,
        ttl_dns_cache=300,
        enable_cleanup_closed=True,
    )

    async with aiohttp.ClientSession(
            headers=HEADERS,
            connector=connector
    ) as session:
        tasks = [
            asyncio.create_task(worker(i, session))
            for i in range(WORKERS)
        ]

        await asyncio.gather(*tasks)


asyncio.run(main())

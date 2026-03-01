import asyncio
import json
import random

import aiohttp

URL = "https://atfminers.asloni.online/miner/index.php?action=sync_taps&t=1772280042728"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json"
}

payload = {
    "initData": "query_id=AAHgh7YIAwAAAOCHtgjXhctz&user=%7B%22id%22%3A6588631008%2C%22first_name%22%3A%22%28%E2%96%BA__%E2%97%84%29%20T_T%20X_X%20xusanboyman%22%2C%22last_name%22%3A%22%F0%9F%87%BA%F0%9F%87%BF%22%2C%22username%22%3A%22xusanboyman200%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FABKucBBOPE9qSGZbrWEF4xW6wrAlil-YqDxjQfABvEOlAI0lJIBU15Q2npDYdUbN.svg%22%7D&auth_date=1772331253&signature=35KZujKAwHvpgMxPmqq0pGjPvolGcDOviw3vM7Q7iIL87T-kqt1yLHIAy01g3ll4jy0y0FEM-OimD2-uyGtFBg&hash=8dcfca1dc3a14af71328e84c2db18ff58564fe33f7b06d94c3f37d7f89d44e48",
    "tg_id": "6859957139",
    "taps": 22
}

DATA = json.dumps(payload)

# ✅ SAFE VALUES FOR SHARED HOSTING
WORKERS = 800  # do NOT increase much
BASE_DELAY = 0.001  # request spacing


async def worker(name, session):
    while True:
        try:
            async with session.post(URL, data=DATA) as resp:

                # read response so connection is reused
                await resp.read()
                print(resp.status)

        except aiohttp.ClientError as e:
            print(f"[{name}] network error:", e)
            await asyncio.sleep(3)


async def main():
    timeout = aiohttp.ClientTimeout(
        total=15,
        connect=5,
        sock_read=10
    )

    # ✅ LIMITED connector (critical for Alwaysdata)
    connector = aiohttp.TCPConnector(
        limit=20,
        limit_per_host=10,
        ssl=False,
        ttl_dns_cache=300,
        enable_cleanup_closed=True,
    )

    async with aiohttp.ClientSession(
            headers=HEADERS,
            timeout=timeout,
            connector=connector
    ) as session:
        tasks = [
            asyncio.create_task(worker(i, session))
            for i in range(WORKERS)
        ]

        await asyncio.gather(*tasks)


asyncio.run(main())

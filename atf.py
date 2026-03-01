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
    "initData": "query_id=AAHNpiJrAwAAAM2mImsUfrYY&user=%7B%22id%22%3A8239883981%2C%22first_name%22%3A%22%26%24%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22qwertypast%22%2C%22language_code%22%3A%22en%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FY8BhGx604ifqPZP7jkXhZ6WbiQI42FqMky328iuxZqJWAKfg8J2l10_KR2RyfXYm.svg%22%7D&auth_date=1772347927&signature=BCeUqiD6W92UjGs4PBDnC2xenxbvopq6C7eI_vznVNWKLfZAw8SCzRe2tcNIpcygaxnxUoHHjAvgCLGhHtPiCw&hash=af34abecc83b6cce63849ac5c9c144c36d0ab7ccd6515ac33f2d3e3932c82bdf",
    "tg_id": "8239883981",
    "taps": 20
}
DATA = json.dumps(payload)

# ✅ SAFE VALUES FOR SHARED HOSTING
WORKERS = 800  # do NOT increase much
BASE_DELAY = 0  # request spacing


async def worker(name, session):
    while True:
        try:
            async with session.post(URL, data=DATA) as resp:

                # read response so connection is reused
                await resp.read()
                res = await resp.json()
                print(res.get('new_pending'))
                if int(res.get('new_pending',1)) >= 2500 and resp.status == 200:
                    break
                if resp.status == 429:
                    await asyncio.sleep(3)
        except aiohttp.ClientError as e:
            print(f"[{name}] network error:", e)
            await asyncio.sleep(3)


async def main2():
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


asyncio.run(main2())

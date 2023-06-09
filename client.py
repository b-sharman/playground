import asyncio
import logging
import websockets

import constants

async def data_entry(ws):
    while True:
        data = input("Enter data: ")
        await ws.send(data)

async def main():
    async with websockets.connect(f"ws://localhost:{constants.PORT}") as ws:
        task = asyncio.create_task(data_entry(ws))
        await task
        while True:
            print(await ws.recv())

if __name__ == "__main__":
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())

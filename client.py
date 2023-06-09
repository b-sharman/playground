import asyncio
import logging
import websockets

import aioconsole

import constants

async def data_entry(ws):
    while True:
        data = await aioconsole.ainput("Enter data: ")
        await ws.send(data)

async def main():
    async with websockets.connect(f"ws://localhost:{constants.PORT}") as ws:
        await asyncio.create_task(data_entry(ws))
        while True:
            print(await ws.recv())

if __name__ == "__main__":
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())

import asyncio
import logging
import websockets

import constants

async def handler(ws):
    async for message in ws:
        print(message)
        await ws.send(f"Hello, {message}!")

async def main():
    async with websockets.serve(handler, "localhost", constants.PORT, ping_interval=5, ping_timeout=10):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())

import asyncio
import json
import logging
import websockets

import aioconsole

import constants

async def data_entry(ws):
    while True:
        data = await aioconsole.ainput("Enter data: ")
        await ws.send(json.dumps({"type": constants.Msg.DEBUG, "data": data}))

async def main():
    async with websockets.connect(f"ws://localhost:{constants.PORT}") as ws:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(data_entry(ws))

            while True:
                message = json.loads(await ws.recv())
                if message["type"] == constants.Msg.DEBUG:
                    print(f"received data {message['data']}")
                if message["type"] == constants.Msg.START:
                    print("Starting now!")
                else:
                    print(message["type"])
                    print(constants.Msg.START)

if __name__ == "__main__":
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())

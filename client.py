import asyncio
import json
import logging
import websockets
import websockets.client  # only for typing, is that bad?

import aioconsole

import constants

async def data_entry(ws: websockets.client.WebSocketClientProtocol) -> None:
    """ Listen for keyboard input and send it to the server. """
    while True:
        data = await aioconsole.ainput("Enter data: ")
        await ws.send(json.dumps({"type": constants.Msg.DEBUG, "data": data}))

async def main() -> None:
    async with websockets.connect(f"ws://localhost:{constants.PORT}") as ws:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(data_entry(ws))

            while True:
                message = json.loads(await ws.recv())
                if message["type"] == constants.Msg.START:
                    print("Starting now!")

if __name__ == "__main__":
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())

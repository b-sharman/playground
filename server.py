import asyncio
import logging
import websockets

import aioconsole

import constants

CONNECTIONS = set()

async def listen_for_start(ws):
    print(f"Type '{constants.SERVER_START_KEYWORD}' at any time to start the game.")
    output = None
    while output != constants.SERVER_START_KEYWORD:
        output = await aioconsole.ainput()

    logger.log(logging.INFO, "received start message")
    message_all("start")

def message_all(message):
    logger.log(logging.DEBUG, CONNECTIONS)
    websockets.broadcast(CONNECTIONS, message)
    logger.log(logging.DEBUG, f"broadcasted the following: {message}")

async def handler(ws):
    async for message in ws:
        await ws.send(f"Hello, {message}!")

async def handle_new_connection(ws):
    """ Start server communications with ws and add ws to CONNECTIONS. """
    # needs to be an inline function so it can be wrapped in a task
    async def add_to_connections():
        # meanwhile, add the connection to the global CONNECTIONS set
        CONNECTIONS.add(ws)
        try:
            await ws.wait_closed()
        finally:
            CONNECTIONS.remove(ws)

    async with asyncio.TaskGroup() as tg:
        # start interacting with client
        client_handler = tg.create_task(handler(ws))
        # add ws to the CONNECTIONS set and remove it upon disconnect
        add_task = tg.create_task(add_to_connections())

async def main():
    async with websockets.serve(
        handle_new_connection,
        "localhost",
        constants.PORT,
        ping_interval=5,
        ping_timeout=10
    ) as server:
        await asyncio.create_task(listen_for_start(server))
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())

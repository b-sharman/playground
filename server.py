import asyncio
import json
import logging
import websockets

import aioconsole

import bbutils
import constants

CONNECTIONS = set()

async def listen_for_start(ws):
    print(f"Type '{constants.SERVER_START_KEYWORD}' at any time to start the game.")
    output = None
    while output != constants.SERVER_START_KEYWORD:
        output = await aioconsole.ainput()

    logger.log(logging.INFO, "received start message")
    message_all({"type": constants.Msg.START})

@bbutils.check_message_valid
def message_all(message):
    """ Serialize message to JSON and broadcast it to all members of CONNECTIONS. """
    logger.log(logging.DEBUG, f"{CONNECTIONS=}")
    data = json.dumps(message)
    websockets.broadcast(CONNECTIONS, data)
    logger.log(logging.DEBUG, f"broadcasted the following: {data}")

async def handler(ws):
    async for json_message in ws:
        message = json.loads(json_message)
        if message["type"] == constants.Msg.DEBUG:
            await ws.send(json.dumps({
                "type": constants.Msg.DEBUG,
                "data": f"Hello, {message['data']}!"
            }))

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

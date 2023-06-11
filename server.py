import asyncio
import json
import logging
import websockets
import websockets.server  # only for typing, is that bad?

import aioconsole

import bbutils
import constants

CONNECTIONS = set()

current_id = 0


async def listen_for_start(ws) -> None:
    """Broadcast a START message upon corresponding keyboard entry."""
    print(f"Type '{constants.SERVER_START_KEYWORD}' at any time to start the game.")
    output = None
    while output != constants.SERVER_START_KEYWORD:
        output = await aioconsole.ainput()

    logger.log(logging.INFO, "received start message")
    message_all({"type": constants.Msg.START})


@bbutils.check_message_valid
def message_all(message: bbutils.Message) -> None:
    """
    Serialize message to JSON and broadcast it to all clients.

    Clients are stored in the global CONNECTIONS set.
    """
    logger.log(logging.DEBUG, f"{CONNECTIONS=}")
    data = json.dumps(message)
    websockets.broadcast(CONNECTIONS, data)
    logger.log(logging.DEBUG, f"broadcasted the following: {data}")


async def handler(ws, player_id) -> None:
    """Listen for messages coming in from client ws."""
    async for json_message in ws:
        message = json.loads(json_message)
        match message["type"]:
            case constants.Msg.GREET:
                # TODO: find some way to prevent name collision
                #       (i.e., more than one player requesting the same name)
                print(f"{message['name']} has joined.")
            case constants.Msg.REQUEST:
                message_all(
                    {
                        "type": constants.Msg.APPROVE,
                        "id": player_id,
                        "rq": message["rq"],
                    }
                )


async def handle_new_connection(ws: websockets.server.WebSocketServer) -> None:
    """Start server communications with ws and add ws to CONNECTIONS."""
    global current_id

    player_id = current_id
    current_id += 1

    async with asyncio.TaskGroup() as tg:
        # start interacting with client
        client_handler = tg.create_task(handler(ws, player_id))

        # add ws to the CONNECTIONS set and remove it upon disconnect
        CONNECTIONS.add(ws)
        logger.log(logging.DEBUG, f"added player with id {player_id}")
        try:
            await ws.wait_closed()
        finally:
            CONNECTIONS.remove(ws)
            logger.log(logging.DEBUG, f"removed player with id {player_id}")


async def main() -> None:
    async with websockets.serve(
        handle_new_connection,
        "localhost",
        constants.PORT,
        ping_interval=5,
        ping_timeout=10,
    ) as server:
        await asyncio.create_task(listen_for_start(server))
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    logger = logging.getLogger("websockets")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    asyncio.run(main())

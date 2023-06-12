import asyncio
import json
import logging
import websockets
import websockets.server  # only for typing, is that bad?

import aioconsole

import bbutils
import constants

CLIENTS = set()

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

    Clients are stored in the global CLIENTS set.
    """
    logger.log(logging.DEBUG, f"{CLIENTS=}")
    data = json.dumps(message)
    websockets.broadcast([c.ws for c in CLIENTS], data)
    logger.log(logging.DEBUG, f"broadcasted the following: {data}")


class Player:
    """
    Server's representation of a player in a game.

    Whereas Client represents the network connection, this class handles tasks like
    collision detection, health tracking, etc.
    """
    def __init__(self) -> None:
        self.name = None


class Client:
    """Server's representation of a network client."""

    def __init__(
        self,
        ws: websockets.server.WebSocketServer,
        tg: asyncio.TaskGroup
    ) -> None:
        """Warning: only create Client instances within the tg context manager."""
        global current_id

        # assign this client a unique id
        self.client_id = current_id
        current_id += 1

        self.ws = ws

        self.player = Player()

        # start listening to messages coming in from the client
        handler = tg.create_task(self.handler())

    async def handler(self) -> None:
        """Listen for messages coming in from client ws."""
        async for json_message in self.ws:
            message = json.loads(json_message)
            match message["type"]:
                case constants.Msg.GREET:
                    # TODO: find some way to prevent name collision
                    #       (i.e., more than one player requesting the same name)
                    self.player.name = message["name"]
                    print(f"{message['name']} has joined.")
                case constants.Msg.REQUEST:
                    message_all(
                        {
                            "type": constants.Msg.APPROVE,
                            "id": self.client_id,
                            "rq": message["rq"],
                        }
                    )

    @staticmethod
    async def handle_new_connection(ws: websockets.server.WebSocketServer) -> None:
        """Start server communications with ws and add ws to CLIENTS."""
        global CLIENTS

        async with asyncio.TaskGroup() as tg:
            # add ws to the CLIENTS set and remove it upon disconnect
            client = Client(ws, tg)
            CLIENTS.add(client)
            logger.log(logging.DEBUG, f"added player with id {client.client_id}")
            try:
                await client.ws.wait_closed()
            finally:
                CLIENTS.remove(client)
                logger.log(logging.DEBUG, f"removed player with id {client.client_id}")


async def main() -> None:
    async with websockets.serve(
        Client.handle_new_connection,
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
